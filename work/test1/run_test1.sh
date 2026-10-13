#!/usr/bin/env bash
# 시험 1 재현 절차 (저장소 루트에서 실행). 유료 호출이 들어 있으므로 필요한 단계만 골라 실행할 것.
# 필요: GEMINI_API_KEY 환경변수, pip install google-genai opencv-contrib-python pillow, ffmpeg
# 주의: Gemini API의 Veo는 seed를 지원하지 않아 같은 명령이라도 매번 다른 영상이 나온다.
set -euo pipefail
P=work/test1/prompts

# 1) 008을 새벽 조명으로 재조명(참조 이미지 없이 텍스트로만 색 지정) 후 008 기하에 정렬  [약 $0.10]
python3 work/scripts/gen_api.py image --out work/test1/keyframes/008c_v2.png \
  --prompt-file $P/008c.txt 008_83Tower.png
python3 work/scripts/align_to.py work/test1/keyframes/008c_v2.png 008_83Tower.png work/test1/keyframes/008c.png

# 2) T1: 008ᶜ → 011, Veo 3.1 Fast 1080p 8초  [약 $0.96]
python3 work/scripts/gen_api.py video --out work/test1/raw/T1_v1.mp4 \
  --first work/test1/keyframes/008c.png --last 011_83Tower.png --prompt-file $P/T1.txt
python3 work/scripts/last_frame.py work/test1/raw/T1_v1.mp4 work/test1/keyframes/T1_v1_last.png

# 3) T2 1차: 끝 프레임 없이 T1의 실제 마지막 프레임에서 자유 이어가기(같은 세계 유지)  [약 $0.96]
python3 work/scripts/gen_api.py video --out work/test1/raw/T2c_v2.mp4 \
  --first work/test1/keyframes/T1_v1_last.png --prompt-file $P/T2c.txt --negative "$(cat $P/negative_v3.txt)"
python3 work/scripts/last_frame.py work/test1/raw/T2c_v2.mp4 work/test1/keyframes/T2c_v2_last.png

# 4) 그 마지막 프레임을 낮 조명으로 재조명 후 정렬  [약 $0.10]
python3 work/scripts/gen_api.py image --out work/test1/keyframes/T2c_v2_last_day_raw.png \
  --prompt-file $P/T2c_last_day.txt work/test1/keyframes/T2c_v2_last.png
python3 work/scripts/align_to.py work/test1/keyframes/T2c_v2_last_day_raw.png \
  work/test1/keyframes/T2c_v2_last.png work/test1/keyframes/T2c_v2_last_day.png

# 5) T2 최종: T1 마지막 프레임 → 재조명한 같은 세계 끝 프레임(일출빛 → 낮)  [약 $0.96]
python3 work/scripts/gen_api.py video --out work/test1/raw/T2d_v2.mp4 \
  --first work/test1/keyframes/T1_v1_last.png --last work/test1/keyframes/T2c_v2_last_day.png \
  --prompt-file $P/T2d.txt --negative "$(cat $P/negative_v4.txt)"

# 6) 측정과 편집(크로스페이드 없음, 경계 중복 프레임 1장 제거, 오디오 제거, 24fps 1080p)
for c in T1_v1 T2d_v2; do python3 work/scripts/clip_check.py work/test1/raw/$c.mp4; done
python3 work/scripts/stitch.py work/test1/edit/test1_T1_T2d_1080p.mp4 \
  work/test1/raw/T1_v1.mp4 work/test1/raw/T2d_v2.mp4 --seam-slow work/test1/edit
python3 work/scripts/clip_check.py work/test1/edit/test1_T1_T2d_1080p.mp4 --out work/test1/check

# 참고(불합격 시도, 결과는 work/test1/rejected/ 와 보고서 참고)
#  T2_v1, T2_v2: T1 끝 → 013 (Fast)              → 4초 부근 디졸브(타워 이중상)
#  T2_v3std:     T1 끝 → 013 (Standard)          → 5초 부근 디졸브 후 거의 정지
#  T2b_v1:       T1 끝 → 018 (Fast)              → 3~4초 방사형 블러 전환
#  T2c_v1:       자유 이어가기, 'drone' 표현       → 화면 안에 다른 드론 등장
#  T2d_v1:       T2d와 같은 구성                   → 1.8~2.5초 가장자리 줄무늬
#  E2_v1:        720p T1 + 연장 7초               → 9.7초 부근 다른 장면으로 디졸브
