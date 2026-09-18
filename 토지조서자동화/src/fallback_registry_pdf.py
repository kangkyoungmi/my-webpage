# -*- coding: utf-8 -*-
"""PRD FR-3-Fallback ②: 등기부등본 기반 면적 오버라이드.

등기부등본 PDF 자체를 이 스크립트가 직접 읽지는 않는다 (표 순서가 뒤섞여
Word/일반 PDF 파서로는 신뢰도가 낮다는 것이 이번 세션에서 확인된 사실).
대신 Claude(비전 기반 PDF 읽기)나 사람이 미리 추출해 둔
`지번, 면적_m2` 2컬럼 CSV/TSV를 읽어 지번 기준으로 값을 덮어쓴다.
"""
from __future__ import annotations

import csv
from pathlib import Path


def normalize_jibun(jibun: str) -> str:
    return jibun.strip().replace(" ", "")


def load_registry_areas(csv_path: str | Path) -> dict[str, float]:
    """지번 -> 면적(㎡) 매핑을 반환한다. 파일이 없으면 빈 dict."""
    path = Path(csv_path)
    if not path.exists():
        return {}

    delimiter = "\t" if path.suffix.lower() == ".tsv" else ","
    result: dict[str, float] = {}
    with path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter=delimiter)
        for row in reader:
            if len(row) < 2:
                continue
            jibun, area = row[0], row[1]
            if jibun.strip().lower() in ("지번", "jibun"):
                continue  # 헤더 행 skip
            try:
                area_val = float(area)
            except ValueError:
                continue
            result[normalize_jibun(jibun)] = area_val
    return result
