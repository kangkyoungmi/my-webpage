# -*- coding: utf-8 -*-
"""ParcelRecord -> JSON 배열 변환.

사업부지_통합에이전트(KCH_9Team) 저장소의 scripts/load_parcels_to_supabase.py가
이 출력을 입력으로 받아 Supabase parcels 테이블에 적재한다. 그 스크립트는
record.get("lon")/record.get("lat")를 직접 읽으므로, 이 파일이 키 이름을
lon/lat으로 맞춰준다(ParcelRecord 자체의 필드명은 경도/위도).
"""
from __future__ import annotations

import json
from pathlib import Path

from models import ParcelRecord


def parcel_record_to_dict(record: ParcelRecord) -> dict:
    return {
        "pnu": record.pnu,
        "소재지": record.소재지,
        "지번": record.지번,
        "지목": record.지목,
        "면적_m2": record.면적_m2,
        "용도지역": record.용도지역,
        "용도지구": record.용도지구,
        "규제사항_원문": record.규제사항_원문,
        "개별공시지가": record.개별공시지가,
        "조회상태": record.조회상태.value,
        "실패사유": list(record.실패사유),
        "데이터출처": list(record.데이터출처),
        "조회시각": record.조회시각.isoformat(),
        "lon": record.경도,
        "lat": record.위도,
    }


def export_records_json(records: list[ParcelRecord], output_path: str | Path) -> Path:
    """PNU가 없는 레코드는 클라우드 스키마(parcels.pnu가 기본키)에 애초에
    적재할 수 없으므로, 조용히 빼지 않고 몇 건을 뺐는지 알려준다."""
    skipped = sum(1 for r in records if not r.pnu)
    if skipped:
        print(f"경고: PNU가 없는 {skipped}건은 클라우드 적재용 JSON에서 제외합니다 (기본키 없음)")

    rows = [parcel_record_to_dict(r) for r in records if r.pnu]

    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
    return out_path
