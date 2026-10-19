"""같은 순간을 두 번 그린 영상 사이를 천천히 넘어가기: 첫 조각(A)과, 그 조각을 연장하며 앞부분을 다시 그린 영상(B)은
같은 프레임 번호에서 카메라 위치가 거의 같다. A의 마지막 L프레임 동안 B의 같은 순간 프레임을 광류로 A 위치에 맞춰
섞는 비중을 0에서 1로 부드럽게 올린다. 그 뒤 B(연장으로 새로 만든 부분)로 이어 가면 그림체(선명도·윤곽)가
이음새에서 한 번에 바뀌지 않고 L프레임에 걸쳐 바뀐다. 무료(로컬 계산만 함).

장면이 다른 두 영상을 섞는 크로스페이드가 아니라, 같은 장면·같은 순간의 두 그림 사이 질감 전환이다(보고서에 밝힘).
모양이 크게 다른 곳(옮긴 뒤에도 차이가 큰 곳)은 섞지 않아 이중 윤곽을 막는다(seam_polish.py와 같은 방식).

사용: python3 work/scripts/render_blend.py --a A.mp4 --a-end 216 --b B.mp4 --b-end 191 --frames 48 --b-blur 0.94 --out 출력.mp4
  --a-end, --b-end: 같은 순간인 마지막 프레임 번호(포함). 출력은 A의 (a_end-L+1 .. a_end)를 대신한다.
  --b-blur: B 쪽에 줄 흐림 σ(뒤에 이어 붙일 B 조각을 soften.py로 흐리게 했다면 그 시작 값과 같게)
"""
import argparse

import cv2
import numpy as np

from seam_polish import smooth, warp_to
from vio import read_frames, writer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--a-end', type=int, required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--b-end', type=int, required=True)
    ap.add_argument('--frames', type=int, default=48)
    ap.add_argument('--b-blur', type=float, default=0.0)
    ap.add_argument('--out', required=True)
    x = ap.parse_args()
    n = x.frames
    fa = read_frames(x.a, x.a_end - n + 1, n)
    fb = read_frames(x.b, x.b_end - n + 1, n)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    h, w = fa[0].shape[:2]
    enc = writer(x.out, w, h, crf=12)
    for k in range(n):
        b = cv2.GaussianBlur(fb[k], (0, 0), x.b_blur) if x.b_blur > 0.05 else fb[k]
        wgt = smooth((k + 1) / n)
        warped, mismatch = warp_to(b, fa[k], dis)
        m = (wgt * (1 - mismatch))[..., None]
        out = (fa[k].astype(np.float32) * (1 - m) + warped.astype(np.float32) * m).astype(np.uint8)
        enc.stdin.write(out.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f'{x.out}: {n}프레임, A {x.a_end - n + 1}~{x.a_end} ← B {x.b_end - n + 1}~{x.b_end} 비중 0→1')


if __name__ == '__main__':
    main()
