#!/usr/bin/env bash
# 시험 2 재현 절차 (저장소 루트에서 실행). 유료 호출 포함: 클립 하나당 Veo 3.1 Fast 4K 8초 약 $2.40.
# 필요: GEMINI_API_KEY, pip install google-genai opencv-contrib-python pillow, ffmpeg
# 주의: Gemini API의 Veo는 seed를 지원하지 않아 결과가 매번 다르다.
set -euo pipefail
D=work/test2
CAP=30.44   # 누적 예상 비용 상한(달러)

# C2: 원본 032 → 040 (같은 장면 묶음, 시작·끝 지정)
python3 -B work/scripts/chain_step.py --dir $D --name C2 --first 032_83Tower.png --last 040_83Tower.png --cap $CAP
# C3f: C2의 실제 마지막 프레임에서 끝 지정 없이 이어 그리기(전망대 주위 왼쪽 선회)
python3 -B work/scripts/chain_step.py --dir $D --name C3f --first $D/keyframes/C2_last.png --cap $CAP
# C4f: C3f의 실제 마지막 프레임에서 이어 그리기(선회하며 상승, 내려다보기)
python3 -B work/scripts/chain_step.py --dir $D --name C4f --first $D/keyframes/C3f_last.png --cap $CAP

# 연결부 속도 맞춤: C3f 앞 1.5초는 0.07배→1배, 마지막 1초는 1배→0.48배
python3 -B work/scripts/retime.py $D/raw/C3f_1080p.mp4 $D/raw/C3f_1080p_seamramp.mp4 --head 0.07 36 --tail 0.48 24
# 크로스페이드 없이 이어 붙이기(경계 중복 프레임 1장 제거, 오디오 제거, 24fps)
python3 -B work/scripts/stitch.py $D/edit/test2_032-057_1080p.mp4 \
  $D/raw/C2_1080p.mp4 $D/raw/C3f_1080p_seamramp.mp4 $D/raw/C4f_1080p.mp4 --seam-slow $D/edit
python3 -B work/scripts/clip_check.py $D/edit/test2_032-057_1080p.mp4 --out $D/check
# 한 파일 다운로드용(2패스 28Mbps)과 100MB 넘는 파일 분할
ffmpeg -y -i $D/edit/test2_032-057_1080p.mp4 -c:v libx264 -preset slow -b:v 28000k -pass 1 -an -f mp4 /dev/null
ffmpeg -y -i $D/edit/test2_032-057_1080p.mp4 -c:v libx264 -preset slow -b:v 28000k -pass 2 -an \
  -movflags +faststart $D/edit/test2_032-057_1080p_download.mp4
python3 -B work/scripts/split_large.py $D/raw $D/edit

# 참고(불합격): C1 030→032(배경이 다른 장면이라 디졸브), C3 C2끝→043(약 29° 기울며 급회전 후 정지)
