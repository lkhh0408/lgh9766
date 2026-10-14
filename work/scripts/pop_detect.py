"""생성 영상의 '팝'(한 프레임 만에 화면 세부가 다시 그려지는 순간) 찾기.

연속 프레임 t, t+1 사이를 광류로 맞춘 뒤 남는 차이(움직임으로 설명되지 않는 변화)를 프레임마다 재고,
앞뒤 25프레임 중앙값보다 크게 튀는 프레임을 보고한다.

사용: python3 work/scripts/pop_detect.py <영상.mp4> [<영상2.mp4> ...] [--ratio 2.0]
"""
import argparse

import cv2
import numpy as np


def residuals(path, size=(640, 360)):
    cap = cv2.VideoCapture(path)
    fr = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        fr.append(cv2.cvtColor(cv2.resize(f, size, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    h, w = fr[0].shape
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    out = []
    for i in range(len(fr) - 1):
        fl = dis.calc(fr[i], fr[i + 1], None)
        wb = cv2.remap(fr[i + 1], gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR)
        d = np.abs(fr[i].astype(np.float32) - wb.astype(np.float32))[8:-8, 8:-8]
        out.append(float(d.mean()))
    return np.array(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('videos', nargs='+')
    ap.add_argument('--ratio', type=float, default=2.0)
    a = ap.parse_args()
    for v in a.videos:
        r = residuals(v)
        pops = []
        for i in range(len(r)):
            lo, hi = max(0, i - 25), min(len(r), i + 26)
            med = np.median(np.r_[r[lo:i], r[i + 1:hi]])
            if r[i] > a.ratio * med and r[i] - med > 0.8:
                pops.append((i + 1, r[i] / med))
        desc = ', '.join(f'f{f}({f / 24:.2f}s, x{q:.1f})' for f, q in pops) or '없음'
        print(f'{v.split("/")[-1]}: 프레임 {len(r) + 1}, 잔차 중앙값 {np.median(r):.2f}, 팝: {desc}')


if __name__ == '__main__':
    main()
