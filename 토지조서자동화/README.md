# 토지조서 자동화 (Phase 1 MVP)

`prd.md` 기반 개발 착수 결과물. 지번을 넣으면 브이월드 API로 조회해 토지조서 엑셀을 자동 생성한다.

## 실행 준비

```bash
pip install -r requirements.txt
cp .env.example .env   # VWORLD_API_KEY=... 입력 (또는 상위 나만의 AI Agent/.env 자동 인식)
```

## 실행

```bash
# 필지 1개
python src/main.py --input data/sample_1parcel.xlsx --output data/result.xlsx --site-name 신안군마명리

# 여러 필지 (배치)
python src/main.py --input data/sample_manyparcel.xlsx --output data/result.xlsx --site-name 신안군마명리_전체

# 브이월드 운영키 미승인 상태에서 면적을 채우고 싶으면 등기부등본 CSV(지번,면적_m2)를 함께 지정
python src/main.py --input data/sample_manyparcel.xlsx --output data/result.xlsx --registry-csv data/registry_마명리.csv
```

입력 엑셀은 `소재지`, `지번` 헤더 컬럼이 필수다 (`data/sample_*.xlsx` 참고).

## 현재 상태 (2026.09.09)

- ✅ FR-1 입력, FR-2 PNU 변환: 정상 동작 (브이월드 주소검색 API, 캐시 포함)
- ⚠️ FR-3 지목/면적/용도지역/공시지가: **브이월드 운영키 미승인**으로 `ned` 계열 API가 전부 막혀있음 (`API_KEY_UNAUTHORIZED`). 운영키 승인 전까지는 `--registry-csv`로 등기부등본 기반 면적만 채워짐
- ✅ FR-3-Fallback ②(등기부등본 CSV): 검증 완료 — 실제 신안군 마명리 12필지로 100% 일치 확인
- ⏳ FR-3-Fallback ③(연속지적도 shp): `fallback_cadastral.py`에 인터페이스만 구현, fiona/shapely 미설치 상태(선택 설치 필요)
- ⏳ FR-4 규제사항 AI 정리, FR-6 이상 Phase 2/3 항목: 착수 전

## 브이월드 운영키 승인되면

`main.py`, `vworld_client.py` 코드 변경 없이 **키만 교체**하면 FR-3가 정상 동작한다 (`_apply_land_characteristics`가 실제 데이터를 채우면 자동으로 `add_source("VWorld API")` 처리됨). 승인 여부는 다음으로 재확인:

```bash
curl "https://api.vworld.kr/ned/data/getLandUseAttr?pnu=1287040037101520000&format=json&key={키}"
```
`INCORRECT_KEY`가 사라지면 승인된 것.

## 알려진 이슈 / 인수인계 메모

- `getLandCharacteristics`는 `getLandUseAttr`/`getIndvdLandPriceAttr`와 실패 응답 형식이 다르다 (`INCORRECT_KEY` 대신 `resultCode:"" , totalCount:"0"`). `main.py`의 `_apply_land_characteristics`가 이를 감지해 `API_KEY_UNAUTHORIZED`로 처리하도록 이미 반영해뒀다 — 이 부분을 건드릴 때 이 차이를 잊지 말 것.
- 토지이음(eum.go.kr)의 공식 Open API 보유 여부는 아직 조사 전 (`prd.md` 리스크 섹션 참고). 규제사항 데이터 소스 확정 전 최우선 조사 필요.
- 캐시(`cache/`)는 PNU/주소별로 남기 때문에, 브이월드 키를 새로 발급받아 재테스트할 때는 `--no-cache`를 쓰거나 `cache/` 폴더를 비울 것.

## 테스트

```bash
python -m pytest tests/ -v
```
