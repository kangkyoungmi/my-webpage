# -*- coding: utf-8 -*-
"""PRD FR-3-Fallback ③: 연속지적도 Shapefile 기반 면적 매칭.

이번 세션에서는 PyQGIS(QGIS 번들 파이썬)로 검증했지만, 이 모듈은
일반 GDAL/Fiona 환경에서도 동작하도록 fiona/shapely 기반으로 작성한다.
fiona가 설치되어 있지 않으면 명확한 사유와 함께 매칭 실패로 처리한다
(전체 파이프라인이 죽지 않도록 main.py에서 except로 감싼다).
"""
from __future__ import annotations

import re
from pathlib import Path


class CadastralNotAvailable(Exception):
    """fiona 미설치 또는 shp 파일 경로 미설정."""


def normalize_num(jibun: str) -> str | None:
    m = re.match(r"^(산)?\s*([0-9]+(-[0-9]+)?)", jibun.strip())
    if not m:
        return None
    prefix = m.group(1) or ""
    return prefix + m.group(2)


def find_area_by_jibun(shp_path: str | Path, bjd_code_prefix: str, jibun: str) -> float | None:
    """법정동코드 10자리 prefix + 지번으로 폴리곤을 찾아 면적(㎡)을 반환한다.

    Args:
        shp_path: 연속지적도(LSMD_CONT_LDREG_*.shp) 경로
        bjd_code_prefix: PNU 앞 10자리 법정동코드
        jibun: 원본 지번 문자열 (예: "152", "산6")
    """
    try:
        import fiona  # type: ignore
        from shapely.geometry import shape  # type: ignore
    except ImportError as exc:
        raise CadastralNotAvailable(
            "fiona/shapely 미설치 - 'pip install fiona shapely' 필요 "
            "(또는 QGIS 번들 파이썬으로 render_map* 스크립트 방식 사용)"
        ) from exc

    target = normalize_num(jibun)
    if target is None:
        return None

    with fiona.open(str(shp_path), encoding="cp949") as src:
        for feature in src:
            props = feature["properties"]
            pnu = str(props.get("PNU", ""))
            if not pnu.startswith(bjd_code_prefix):
                continue
            feat_jibun = str(props.get("JIBUN", ""))
            if normalize_num(feat_jibun) == target:
                geom = shape(feature["geometry"])
                return geom.area
    return None
