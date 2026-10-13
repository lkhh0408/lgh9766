"""두 클립 비교(같은 구간을 다른 방식으로 만든 A/B).

측정
- 배경 변형: 오른쪽 배경 영역에서, 3프레임 뒤 화면을 광류로 되돌려 겹친 뒤에도 남는 차이(카메라 움직임으로 설명되지 않는 변화).
  창문처럼 반복되는 무늬에서는 값이 과하게 나올 수 있어 절대값보다 A/B 상대 비교로 쓴다.
- 전망대 출렁임: 화면 가운데(전망대·기둥) 영역에서 1프레임 간격으로 같은 방식의 차이.
- 접근 속도: 초마다 화면 전체 배율 변화(1프레임당)와 전망대 영역의 배율 변화.
- 1/3초 주기 출렁임: 프레임별 이동량이 9프레임 평균에서 벗어나는 비율(중앙값)과 8프레임 간격 자기상관.

사용: python3 work/scripts/ab_compare.py A.mp4 B.mp4 [--labels A B] [--out 폴더]
"""
import argparse
import os

import cv2
import numpy as np


def read(path, size=(960, 540)):
    cap = cv2.VideoCapture(path)
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(cv2.resize(f, size, interpolation=cv2.INTER_AREA))
    return out


def residual(frames, region, gap, dis):
    h, w = frames[0].shape[:2]
    x0, y0, x1, y1 = [int(v) for v in (region[0] * w, region[1] * h, region[2] * w, region[3] * h)]
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    vals = []
    for t in range(0, len(frames) - gap, 2):
        a = cv2.cvtColor(frames[t], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[t + gap], cv2.COLOR_BGR2GRAY)
        fl = dis.calc(a, b, None)
        wb = cv2.remap(b, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR)
        d = np.abs(a.astype(np.float32) - wb.astype(np.float32))[y0:y1, x0:x1]
        vals.append(float(d.mean()))
    return np.array(vals)


def scale_series(frames, region, dis, step=6):
    h, w = frames[0].shape[:2]
    x0, y0, x1, y1 = [int(v) for v in (region[0] * w, region[1] * h, region[2] * w, region[3] * h)]
    ys, xs = np.mgrid[y0:y1:8, x0:x1:8]
    p0 = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
    out = []
    for t in range(0, len(frames) - step, step):
        a = cv2.cvtColor(frames[t], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[t + step], cv2.COLOR_BGR2GRAY)
        fl = dis.calc(a, b, None)
        d = fl[ys.ravel(), xs.ravel()]
        M, _ = cv2.estimateAffinePartial2D(p0, p0 + d, ransacReprojThreshold=1.0)
        s = float(np.hypot(M[0, 0], M[1, 0])) if M is not None else 1.0
        out.append((t / 24, s ** (1 / step)))
    return np.array(out)


def pulsing(frames, dis):
    sp = []
    for t in range(len(frames) - 1):
        a = cv2.cvtColor(frames[t], cv2.COLOR_BGR2GRAY)
        b = cv2.cvtColor(frames[t + 1], cv2.COLOR_BGR2GRAY)
        fl = dis.calc(a, b, None)
        sp.append(float(np.median(np.hypot(fl[..., 0], fl[..., 1]))))
    sp = np.array(sp)
    sm = np.convolve(sp, np.ones(9) / 9, mode='same')
    dt = sp - sm
    ac8 = float(np.corrcoef(dt[8:-16], dt[16:-8])[0, 1])
    return float(np.median(np.abs(dt[8:-8]) / sm[8:-8]) * 100), ac8


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('a')
    ap.add_argument('b')
    ap.add_argument('--labels', nargs=2, default=['A', 'B'])
    a = ap.parse_args()
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    right_bg = (0.64, 0.30, 1.0, 0.85)
    left_bg = (0.0, 0.30, 0.34, 0.85)
    deck = (0.40, 0.15, 0.60, 0.80)
    for path, lab in ((a.a, a.labels[0]), (a.b, a.labels[1])):
        fr = read(path)
        rr = residual(fr, right_bg, 3, dis)
        rl = residual(fr, left_bg, 3, dis)
        rd = residual(fr, deck, 1, dis)
        sg = scale_series(fr, (0.05, 0.3, 0.95, 0.95), dis)
        sd = scale_series(fr, deck, dis)
        pf, ac8 = pulsing(fr, dis)
        print(f'[{lab}] {os.path.basename(path)}')
        print(f'  오른쪽 배경 변형(평균) {rr.mean():.2f}  /  왼쪽 배경 {rl.mean():.2f}  /  전망대 출렁임 {rd.mean():.2f}')
        print('  초별 화면 배율(×1e-4/프레임):', ' '.join(f'{(sg[(sg[:, 0] >= s) & (sg[:, 0] < s + 1), 1].mean() - 1) * 1e4:5.1f}' for s in range(8)))
        print('  초별 전망대 배율(×1e-4/프레임):', ' '.join(f'{(sd[(sd[:, 0] >= s) & (sd[:, 0] < s + 1), 1].mean() - 1) * 1e4:5.1f}' for s in range(8)))
        print(f'  프레임별 출렁임 {pf:.0f}%, 8프레임 주기 상관 {ac8:+.2f}')


if __name__ == '__main__':
    main()
