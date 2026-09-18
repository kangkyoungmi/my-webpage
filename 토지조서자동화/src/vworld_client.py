# -*- coding: utf-8 -*-
"""브이월드 API 래퍼. PRD 6절 FR-2/FR-3, 캐시 포함(NFR-로깅)."""
from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

import requests

from models import FailureCode

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.vworld.kr/req/search"
NED_BASE_URL = "https://api.vworld.kr/ned/data"

CACHE_DIR = Path(__file__).resolve().parent.parent / "cache"


class VWorldError(Exception):
    def __init__(self, code: FailureCode, message: str = ""):
        super().__init__(message or code.value)
        self.code = code


class VWorldClient:
    """PNU 조회는 실제로 동작 확인됨. ned 계열은 운영키 승인 전까지
    API_KEY_UNAUTHORIZED로 실패 처리된다 (PRD 6절 FR-3 알려진 제약)."""

    def __init__(self, api_key: str, use_cache: bool = True, timeout: int = 10):
        self.api_key = api_key
        self.use_cache = use_cache
        self.timeout = timeout
        CACHE_DIR.mkdir(exist_ok=True)

    def _cache_path(self, kind: str, key: str) -> Path:
        safe_key = key.replace("/", "_").replace(" ", "_")
        return CACHE_DIR / f"{kind}__{safe_key}.json"

    def _cached_get(self, kind: str, cache_key: str, url: str, params: dict) -> dict:
        path = self._cache_path(kind, cache_key)
        if self.use_cache and path.exists():
            logger.info("캐시 사용: %s", path.name)
            return json.loads(path.read_text(encoding="utf-8"))

        try:
            resp = requests.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.warning("API 요청 실패: %s", exc)
            raise VWorldError(FailureCode.API_TIMEOUT, str(exc)) from exc

        time.sleep(0.2)  # PRD FR-9: 요청 간 최소 딜레이

        try:
            data = resp.json()
        except ValueError as exc:
            raise VWorldError(FailureCode.API_TIMEOUT, "JSON 파싱 실패") from exc

        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return data

    def search_pnu(self, address: str) -> dict[str, Any] | None:
        """주소/지번 문자열로 PNU와 좌표를 조회한다. 검증된 엔드포인트 (PRD FR-2)."""
        params = {
            "service": "search",
            "request": "search",
            "version": "2.0",
            "crs": "epsg:4326",
            "type": "address",
            "category": "parcel",
            "format": "json",
            "key": self.api_key,
            "query": address,
        }
        data = self._cached_get("search", address, SEARCH_URL, params)

        response = data.get("response", {})
        if response.get("status") != "OK":
            return None

        items = response.get("result", {}).get("items", [])
        if not items:
            return None

        item = items[0]
        return {
            "pnu": item.get("id"),
            "matched_address": item.get("address", {}).get("parcel"),
            "x": item.get("point", {}).get("x"),
            "y": item.get("point", {}).get("y"),
        }

    def _call_ned(self, operation: str, pnu: str) -> dict[str, Any]:
        params = {
            "pnu": pnu,
            "format": "json",
            "numOfRows": 10,
            "pageNo": 1,
            "key": self.api_key,
        }
        url = f"{NED_BASE_URL}/{operation}"
        data = self._cached_get(f"ned_{operation}", pnu, url, params)

        # ned 응답은 {"<root>": {"resultCode": "...", ...}} 형태
        root = next(iter(data.values()), {}) if isinstance(data, dict) else {}
        result_code = root.get("resultCode")
        if result_code == "INCORRECT_KEY":
            raise VWorldError(FailureCode.API_KEY_UNAUTHORIZED)
        return data

    def get_land_characteristics(self, pnu: str) -> dict[str, Any]:
        """지목·면적 (PRD FR-3). 운영키 미승인 시 VWorldError 발생."""
        return self._call_ned("getLandCharacteristics", pnu)

    def get_land_use(self, pnu: str) -> dict[str, Any]:
        """용도지역·용도지구 (PRD FR-3/FR-4)."""
        return self._call_ned("getLandUseAttr", pnu)

    def get_individual_land_price(self, pnu: str) -> dict[str, Any]:
        """개별공시지가 (PRD FR-3)."""
        return self._call_ned("getIndvdLandPriceAttr", pnu)
