# -*- coding: utf-8 -*-
"""PRD 11절 완료기준: Mock 응답 기반 단위테스트."""
import json

import pytest

from models import FailureCode
from vworld_client import VWorldClient, VWorldError


class FakeResponse:
    def __init__(self, payload: dict):
        self._payload = payload

    def json(self):
        return self._payload


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr("vworld_client.CACHE_DIR", tmp_path)
    return VWorldClient(api_key="TEST-KEY", use_cache=False)


def test_search_pnu_success(client, monkeypatch):
    payload = {
        "response": {
            "status": "OK",
            "result": {
                "items": [
                    {
                        "id": "1283036023110980011",
                        "address": {"parcel": "전남 영광군 염산면 봉남리 1098-11"},
                        "point": {"x": "126.34", "y": "35.20"},
                    }
                ]
            },
        }
    }
    monkeypatch.setattr("vworld_client.requests.get", lambda *a, **k: FakeResponse(payload))

    result = client.search_pnu("전남 영광군 염산면 봉남리 1098-11")
    assert result["pnu"] == "1283036023110980011"


def test_search_pnu_not_found(client, monkeypatch):
    payload = {"response": {"status": "NOT_FOUND"}}
    monkeypatch.setattr("vworld_client.requests.get", lambda *a, **k: FakeResponse(payload))

    result = client.search_pnu("존재하지 않는 주소 999")
    assert result is None


def test_ned_incorrect_key_raises_unauthorized(client, monkeypatch):
    payload = {"landUses": {"resultCode": "INCORRECT_KEY", "resultMsg": "인증키 정보가 올바르지 않습니다."}}
    monkeypatch.setattr("vworld_client.requests.get", lambda *a, **k: FakeResponse(payload))

    with pytest.raises(VWorldError) as exc_info:
        client.get_land_use("1283036023110980011")
    assert exc_info.value.code == FailureCode.API_KEY_UNAUTHORIZED
