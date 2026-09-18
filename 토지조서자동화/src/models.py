# -*- coding: utf-8 -*-
"""PRD 9절 데이터 모델: ParcelRecord."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class QueryStatus(str, Enum):
    SUCCESS = "성공"
    PARTIAL = "부분성공"
    FAILED = "실패"


class FailureCode(str, Enum):
    PNU_NOT_FOUND = "PNU_NOT_FOUND"
    API_KEY_UNAUTHORIZED = "API_KEY_UNAUTHORIZED"
    NO_MATCHING_PARCEL = "NO_MATCHING_PARCEL"
    API_TIMEOUT = "API_TIMEOUT"


FAILURE_MESSAGES = {
    FailureCode.PNU_NOT_FOUND: "PNU 조회 실패 - 주소/지번 확인 필요",
    FailureCode.API_KEY_UNAUTHORIZED: "브이월드 운영키 미승인 (ned API)",
    FailureCode.NO_MATCHING_PARCEL: "연속지적도/등기부에서도 매칭 실패",
    FailureCode.API_TIMEOUT: "외부 API 응답 지연/오류",
}


@dataclass
class ParcelRecord:
    소재지: str
    지번: str
    pnu: str | None = None
    # 브이월드 PNU 조회(search_pnu)가 함께 돌려주는 좌표(x=경도, y=위도, EPSG:4326).
    # 클라우드 적재(Supabase parcels.geom) 시에만 쓰이지만, 여기서 안 받아두면
    # 조서 자체는 정상 완성돼도 그 필지가 지도/판정 화면에 영원히 안 나타난다.
    경도: float | None = None
    위도: float | None = None
    지목: str | None = None
    면적_m2: float | None = None
    면적_평: float | None = None
    소유구분: str | None = None
    용도지역: str | None = None
    용도지구: str | None = None
    규제사항_원문: str | None = None
    규제사항_정리: str | None = None
    개별공시지가: int | None = None
    조회상태: QueryStatus = QueryStatus.FAILED
    실패사유: list[str] = field(default_factory=list)
    데이터출처: list[str] = field(default_factory=list)
    조회시각: datetime = field(default_factory=datetime.now)
    비고: str | None = None

    def mark_failure(self, code: FailureCode) -> None:
        msg = f"#조회실패: {FAILURE_MESSAGES[code]}"
        if msg not in self.실패사유:
            self.실패사유.append(msg)
        if self.조회상태 != QueryStatus.SUCCESS:
            self.조회상태 = QueryStatus.FAILED

    def add_source(self, source: str) -> None:
        if source not in self.데이터출처:
            self.데이터출처.append(source)

    def failure_text(self) -> str:
        return " / ".join(self.실패사유)

    def source_text(self) -> str:
        return ", ".join(self.데이터출처) if self.데이터출처 else ""
