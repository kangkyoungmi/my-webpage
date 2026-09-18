# -*- coding: utf-8 -*-
"""main.process_parcel이 PNU 조회 응답의 좌표(x=경도, y=위도)를
ParcelRecord에 실제로 붙이는지 검증한다.

배경: 이 좌표는 클라우드(Supabase parcels.geom)에 적재될 때만 쓰이는데,
좌표가 없으면 그 필지는 지도/판정 화면 어디에도 나타나지 않는다
(parcel_at RPC가 geom is not null로 걸러내기 때문). 그런데도 조회 자체는
성공으로 끝나 사람이 눈치채기 어려우므로, 여기서 값이 실제로 옮겨붙는지
회귀로 고정해 둔다.
"""
from main import process_parcel


class FakeClient:
    """VWorldClient를 대신하는 가짜 클라이언트. process_parcel의 좌표 처리
    로직만 격리해서 보기 위해 나머지 조회는 전부 빈 응답으로 둔다."""

    def __init__(self, search_result):
        self._search_result = search_result

    def search_pnu(self, address):
        return self._search_result

    def get_land_characteristics(self, pnu):
        return {}

    def get_land_use(self, pnu):
        return {}

    def get_individual_land_price(self, pnu):
        return {}


def test_pnu_조회_성공시_경도_위도가_레코드에_붙는다():
    fake = FakeClient({
        "pnu": "1283036023110980011",
        "matched_address": "전남 영광군 염산면 봉남리 1098-11",
        "x": "126.34",
        "y": "35.20",
    })
    record = process_parcel(fake, "전남 영광군 염산면 봉남리", "1098-11", {})
    assert record.경도 == 126.34
    assert record.위도 == 35.20


def test_좌표가_없으면_None으로_남고_예외가_안_난다():
    fake = FakeClient({
        "pnu": "1283036023110980011",
        "matched_address": "전남 영광군 염산면 봉남리 1098-11",
        "x": None,
        "y": None,
    })
    record = process_parcel(fake, "전남 영광군 염산면 봉남리", "1098-11", {})
    assert record.경도 is None
    assert record.위도 is None


def test_좌표_형식이_이상해도_예외_없이_None():
    fake = FakeClient({
        "pnu": "1283036023110980011",
        "matched_address": "전남 영광군 염산면 봉남리 1098-11",
        "x": "이상한값",
        "y": "35.20",
    })
    record = process_parcel(fake, "전남 영광군 염산면 봉남리", "1098-11", {})
    assert record.경도 is None
    assert record.위도 is None


def test_PNU_조회_실패시_좌표도_None():
    fake = FakeClient(None)
    record = process_parcel(fake, "존재하지 않는 주소", "1", {})
    assert record.pnu is None
    assert record.경도 is None
    assert record.위도 is None
