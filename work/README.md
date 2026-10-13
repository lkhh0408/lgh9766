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
- `scripts/color_match.py` — 색 보정(기준 이미지 색 분포에 맞춤). 리터칭 가능 범위 확인용
- `retouch_test/` — 로컬 리터칭 시험 결과(008을 002 새벽 색으로 맞춤)
- `analysis/시험1_계획.md` — 시험 1(001~028) 클립 구성·프롬프트 초안·비용
- `cost_ledger.csv` — 모든 유료 호출의 예상 비용 장부(가격표 기준, 실패·거절 호출은 0원으로 기록)
- `scripts/gen_api.py` — Gemini 이미지 편집·Veo 영상 생성(시작·끝 프레임, 연장) 호출. 누적 예상액이 상한(`--cap`, 기본 30달러)을 넘으면 실행하지 않음
- `scripts/clip_check.py` — 클립 측정(프레임 간 이동량·방향, 밝기, 0.5초 간격 장면 연속성으로 디졸브 탐지, 시작·끝 프레임 일치도)
- `scripts/last_frame.py`, `scripts/align_to.py`, `scripts/stitch.py` — 마지막 프레임 추출, 생성 이미지 기하 정렬, 크로스페이드 없는 이어 붙이기
- `test1/` — 시험 1 결과(보고서 `test1/시험1_결과보고서.md`, 재현 절차 `test1/run_test1.sh`)
