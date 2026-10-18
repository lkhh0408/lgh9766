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

## 최종 마감·이어 붙이기 도구 (무료, 로컬 계산만 함 · API 호출 없음)

자세한 사용법은 각 스크립트 맨 위 설명에 있다. 모두 저장소 루트에서 실행한다.

- `scripts/finish.py` — 4K 원본들을 자르기 목록 CSV(`raw,in_s,out_s,label`, 선택 열 `plan_t0,plan_segs,ff_s,ff_x`)대로
  프레임 단위로 잘라 1920×1080 lanczos, 24fps, x264 crf 16 preset slow, yuv420p, 소리 없음, faststart로 **한 번만** 인코딩해 잇는다.
  크로스페이드 없음. 선택: `--dehalo 0.2`(unsharp=5:5:-값:5:5:0), `--clamp 0.8`(윤곽 넘침 자르기, 권장 완화판).
  느린 출발 보정은 `ff_s, ff_x`로 정수 프레임만 건너뛴다(보간·잔상 없음). 단, 1배·2배 간격이 번갈아 떨림이 생기므로
  최후 수단이다(`seam_check.py` 프레임 간격 검사 통과 + 4배 느린 영상 눈 확인 뒤에만, `final/plan/장면계획.md` 5장).
  결과: 완성본, `<이름>.edit.json`(조각·이음새·검사 기록), 조각별 파일, 이음새 앞뒤 1초 4배 느린 확인 영상.
  검사: 해상도·fps·프레임 수 = 조각 합·오디오 없음·색 표시 정보, 조각 첫·끝 프레임이 원본의 그 프레임인지.
  `python3 work/scripts/finish.py --trims 자르기.csv --out work/final/edit/최종_1080p.mp4`
- `scripts/seam_check.py` — 완성본 이음새 검사. 앞뒤 1초 속도 비율(0.7~1.4), 방향 차(45° 이하),
  이음새 한 쌍의 멈칫·튐, 멈췄다 가기, 움직임 보정 잔차로 본 팝, 장면 끊김, 밝기 차를 재고, 이음새 주변 프레임 시트(jpg)를 만든다.
  프레임 간격 검사: 이음새 뒤 2초와 빨리 감기 구간의 프레임 쌍마다 이동량을 앞뒤 3쌍 중앙값과 비교해 1.6배 넘게 다르면 불합격.
  `python3 work/scripts/seam_check.py work/final/edit/최종_1080p.mp4` (옆의 .edit.json에서 이음새를 읽음, `--seams 16 f767`도 가능)
- `scripts/next_chain_frame.py` — 다음 묶음의 첫 장면용 프레임을 4K 원본에서 원본 크기(3840×2160) 무손실 PNG로 꺼낸다.
  진짜 프레임 수는 전체 디코드로 세고, 같은 폴더에 더 긴 연장 결과(묶음 전체)가 있으면 알려 주고 멈춘다.
  저장한 PNG가 디코드한 그 프레임과 화소까지 같은지 확인하고 md5·프레임 번호·시각을 출력·기록한다.
  `python3 work/scripts/next_chain_frame.py work/final/A/raw/A12_4k.mp4 --at -1.0 --out work/final/B/keyframes/A_overlap.png`
- `scripts/mapping_table.py` — 계획표(`final/plan/plan.csv`, `final/plan/이미지_시간_대응표.csv`)와 최종 편집 기록으로
  이미지 번호 ↔ 최종 영상 시간 대응표(한국어 CSV + Markdown)를 만든다. 자르기·겹침 재시작·빨리 감기로 바뀐 시간을 반영한다.
  `python3 work/scripts/mapping_table.py --edit work/final/edit/최종_1080p.edit.json`
