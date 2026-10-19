#!/usr/bin/env bash
# 승인본 기준 본편(R)의 이음새 다듬기 조각 만들기. 무료(로컬 계산만 함). 저장소 루트에서 실행.
#   1) 조각 자르기(4K, 쓰는 프레임 범위) → 2) 속도 맞춤(dejudder.py / retime.py) → 3) 색·질감 다듬기(seam_polish.py)
# 결과: work/final/R/polish/ 의 4K 조각들. 자르기 목록은 work/final/R/trims_final.csv.
# 속도 값(--start-speed)은 dejudder.py와 같은 방식(밝기 정규화 960폭 광류 중앙값)으로 앞 조각 끝 24프레임을 잰 값.
set -euo pipefail
cd "$(dirname "$0")/../../.."
R=work/final/R
P=$R/polish
S=work/scripts
mkdir -p "$P"

cut() {  # cut 원본 시작 끝(포함) 출력
  ffmpeg -y -v error -i "$1" -vf "select='between(n\,$2\,$3)'" -vsync 0 -c:v libx264 -preset fast -crf 12 \
    -pix_fmt yuv420p -color_primaries bt709 -color_trc iec61966-2-1 -colorspace smpte170m -color_range tv "$4"
}
polish() { python3 $S/seam_polish.py "$@"; }

S1=work/final/s1/raw/C1fE1_4k_v2.mp4
MID=work/final/mid/raw/E12_4k_b_recovered.mp4

# 중간 시험 끝 선회 감속: 324~383(60프레임) → 끝 4초(96프레임)에 걸쳐 0.08배까지 늦춤(105프레임, 383번에서 끝남)
[ -f $R/edit/mid_tail_ease_4k.mp4 ] || { cut $MID 324 383 $P/C_midtail.mp4
  python3 $S/retime.py $P/C_midtail.mp4 $R/edit/mid_tail_ease_4k.mp4 --tail 0.08 96; rm $P/C_midtail.mp4; }

# 오후 두 번째 조각 X2r: 출발 속도를 X1b 끝(0.165)에 맞추고 프레임 간격 고르기
[ -f $R/edit/X2r_match_4k.mp4 ] || (cd $S && python3 dejudder.py ../../$R/raw/X2r_4k.mp4 ../../$R/edit/X2r_match_4k.mp4 --start-speed 0.165 --ramp 48)

# BR_up: 0~138(0번은 1단계 끝을 다시 그린 프레임이라 안 씀). 출발 속도를 1단계 끝(0.49)에 맞춤
[ -f $P/D_BRup.mp4 ] || { cut $R/raw/BR_up_4k.mp4 0 138 $P/C_BRup.mp4
  (cd $S && python3 dejudder.py ../../$P/C_BRup.mp4 ../../$P/D_BRup.mp4 --start-speed 0.49 --ramp 36 --head-only); rm $P/C_BRup.mp4; }
polish --ref $S1 --ref-frame -1 --clip $P/D_BRup.mp4 --start 1 --out $P/H_BRup.mp4

# BR_sky: 0~142. 출발 속도를 BR_up 끝(1.47)에 맞춤
[ -f $P/D_BRsky.mp4 ] || { cut $R/raw/BR_sky_4k.mp4 0 142 $P/C_BRsky.mp4
  (cd $S && python3 dejudder.py ../../$P/C_BRsky.mp4 ../../$P/D_BRsky.mp4 --start-speed 1.47 --ramp 24 --head-only); rm $P/C_BRsky.mp4; }
polish --ref $P/D_BRup.mp4 --ref-frame -1 --clip $P/D_BRsky.mp4 --start 0 --out $P/H_BRsky.mp4

# BR_sky2: 0~59(속도는 이미 이어짐)
[ -f $P/C_BRsky2.mp4 ] || cut $R/raw/BR_sky2_4k.mp4 0 59 $P/C_BRsky2.mp4
polish --ref $P/D_BRsky.mp4 --ref-frame -1 --clip $P/C_BRsky2.mp4 --start 0 --out $P/H_BRsky2.mp4

# BR_sky3: 0~95. 0.83초의 한 프레임 멈칫을 고르게 하고, 끝 1초는 위로 드는 움직임을 거의 멈출 때까지 늦춤(꼭대기에서 방향 바꾸기)
[ -f $P/D_BRsky3.mp4 ] || { cut $R/raw/BR_sky3_4k.mp4 0 95 $P/C_BRsky3.mp4
  (cd $S && python3 dejudder.py ../../$P/C_BRsky3.mp4 ../../$P/J_BRsky3.mp4 --window 9)
  python3 $S/retime.py $P/J_BRsky3.mp4 $P/D_BRsky3.mp4 --tail 0.12 24; rm $P/C_BRsky3.mp4 $P/J_BRsky3.mp4; }
polish --ref $P/C_BRsky2.mp4 --ref-frame -1 --clip $P/D_BRsky3.mp4 --start 0 --out $P/H_BRsky3.mp4

# BR_down3: 0~190. 처음 1초는 아주 느리게 출발해 아래로 기울기 시작(꼭대기에서 방향 바꾸기), 끝은 중간 시험 첫 장면 쪽으로 맞춤
[ -f $P/D_BRdown.mp4 ] || { cut $R/raw/BR_down3_4k.mp4 0 190 $P/C_BRdown.mp4
  python3 $S/retime.py $P/C_BRdown.mp4 $P/D_BRdown.mp4 --head 0.25 24; rm $P/C_BRdown.mp4; }
polish --ref $P/D_BRsky3.mp4 --ref-frame -1 --clip $P/D_BRdown.mp4 --start 1 --out $P/H_BRdown.mp4
N=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $P/D_BRdown.mp4)
polish --tail --ref $MID --ref-frame 0 --clip $P/D_BRdown.mp4 --end $((N-1)) --blend 1.0 --texture-frames 12 --out $P/T_BRdown.mp4

# X1b: 0~191(0번은 중간 시험 끝을 다시 그린 프레임). 출발 속도를 감속 끝(0.15)에 맞춤
[ -f $P/D_X1.mp4 ] || { cut $R/raw/X1b_4k.mp4 0 191 $P/C_X1.mp4
  (cd $S && python3 dejudder.py ../../$P/C_X1.mp4 ../../$P/D_X1.mp4 --start-speed 0.15 --ramp 36 --head-only); rm $P/C_X1.mp4; }
polish --ref $R/edit/mid_tail_ease_4k.mp4 --ref-frame -1 --clip $P/D_X1.mp4 --start 1 --out $P/H_X1.mp4

# X2(출발 속도는 이미 맞춘 X2r_match)
polish --ref $P/D_X1.mp4 --ref-frame -1 --clip $R/edit/X2r_match_4k.mp4 --start 1 --out $P/H_X2.mp4

# Y1: 0~191. 노을 조각의 급한 출발(0.15→0.8)을 3초에 걸쳐 오후 끝 속도(0.105)에서 천천히 올림, 밝기 차가 커서 색 맞춤 2초
[ -f $P/D_Y1.mp4 ] || { cut $R/raw/Y1_4k.mp4 0 191 $P/C_Y1.mp4
  (cd $S && python3 dejudder.py ../../$P/C_Y1.mp4 ../../$P/D_Y1.mp4 --start-speed 0.105 --ramp 72 --head-only); rm $P/C_Y1.mp4; }
polish --ref $R/edit/X2r_match_4k.mp4 --ref-frame -1 --clip $P/D_Y1.mp4 --start 1 --color-frames 48 --out $P/H_Y1.mp4

# Y12 뒷부분: 192~383(연장으로 새로 만든 8초). 프레임 간격 고르기
[ -f $P/D_Y12b.mp4 ] || { cut $R/raw/Y12_4k.mp4 192 383 $P/C_Y12b.mp4
  (cd $S && python3 dejudder.py ../../$P/C_Y12b.mp4 ../../$P/D_Y12b.mp4 --window 9); rm $P/C_Y12b.mp4; }

# Z1: 0~119(0번은 Y12 끝을 다시 그린 프레임). 프레임 간격 고르기(15프레임) + 출발 속도를 Y12 마지막 0.5초(0.30)에 맞춰 2초에 걸쳐 올림
[ -f $P/D_Z.mp4 ] || (cd $S && python3 dejudder.py ../../$R/raw/Z1_4k.mp4 ../../$P/D_Z.mp4 --window 15 --start-speed 0.30 --ramp 48)
polish --ref $P/D_Y12b.mp4 --ref-frame -1 --clip $P/D_Z.mp4 --start 1 --out $P/H_Z.mp4
echo 끝
