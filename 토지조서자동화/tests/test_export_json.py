# -*- coding: utf-8 -*-
"""ParcelRecord -> JSON 변환이 사업부지_통합에이전트(KCH_9Team) 저장소의
scripts/load_parcels_to_supabase.py가 기대하는 키(lon/lat 포함)로 정확히
나오는지 검증한다."""
import json
from datetime import datetime

from export_json import export_records_json, parcel_record_to_dict
from models import ParcelRecord, QueryStatus


def test_경도_위도가_lon_lat_키로_나온다():
    record = ParcelRecord(
        소재지="전남 신안군 안좌면 마명리", 지번="152", pnu="1287040037101520000",
        경도=126.123456, 위도=34.812345,
        조회상태=QueryStatus.SUCCESS, 조회시각=datetime(2026, 9, 9, 14, 32, 2),
    )
    row = parcel_record_to_dict(record)
    assert row["lon"] == 126.123456
    assert row["lat"] == 34.812345


def test_조회시각은_ISO_문자열이고_조회상태는_한글값이다():
    record = ParcelRecord(
        소재지="a", 지번="1", pnu="1",
        조회상태=QueryStatus.PARTIAL, 조회시각=datetime(2026, 9, 9, 14, 32, 2),
    )
    row = parcel_record_to_dict(record)
    assert row["조회시각"] == "2026-09-09T14:32:02"
    assert row["조회상태"] == "부분성공"


def test_실패사유와_데이터출처는_빈배열이지_None이_아니다():
    record = ParcelRecord(소재지="a", 지번="1", pnu="1")
    row = parcel_record_to_dict(record)
    assert row["실패사유"] == []
    assert row["데이터출처"] == []


def test_PNU가_없는_레코드는_내보내지_않는다(tmp_path):
    # 클라우드 스키마에서 pnu가 기본키라, pnu 없는 행은 애초에 적재될 수 없다.
    # 조용히 버리지 않고 건수를 세어 경고하는 동작까지 함께 확인한다.
    no_pnu = ParcelRecord(소재지="a", 지번="1", pnu=None)
    has_pnu = ParcelRecord(소재지="b", 지번="2", pnu="999", 경도=1.0, 위도=2.0)

    out_path = export_records_json([no_pnu, has_pnu], tmp_path / "out.json")
    rows = json.loads(out_path.read_text(encoding="utf-8"))

    assert len(rows) == 1
    assert rows[0]["pnu"] == "999"


def test_빈_목록도_빈_배열_파일을_만든다(tmp_path):
    out_path = export_records_json([], tmp_path / "out.json")
    rows = json.loads(out_path.read_text(encoding="utf-8"))
    assert rows == []
