# 83타워 연속 비행 영상 작업 폴더

원본 이미지(저장소 루트의 `001_83Tower.png` ~ `137_83Tower.png`)는 읽기만 하며 수정·이동하지 않는다.
모든 작업 결과는 이 `work/` 폴더에 둔다.

- `scripts/analyze_frames.py` — 1단계 수치 분석(인접 쌍 카메라 이동·대응점·밝기·색온도). 저장소 루트에서 `python3 work/scripts/analyze_frames.py`
- `analysis/metrics_frames.csv`, `analysis/metrics_pairs.csv` — 위 스크립트 결과
- `analysis/sheets/contact_*.jpg` — 번호가 적힌 전체 썸네일
- `analysis/pair_review.json` — 인접 136쌍 시각 검토 결과(타워·카메라·수평선·랜드마크·조명·문제·처리 제안)
- `scripts/build_plan_tables.py` — 구간표·이미지 역할표 생성. `python3 work/scripts/build_plan_tables.py`
- `analysis/segments.csv` — 구간표(S1~S9)
- `analysis/image_roles.csv` — 137장 대응표(구간·시간대·역할·사유)
- `analysis/1단계_분석보고서.md` — 1단계 분석 보고서(이미지 연속성 + 제작 환경)
