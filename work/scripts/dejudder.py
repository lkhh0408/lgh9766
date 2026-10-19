"""프레임 간격 고르기(떨림 줄이기): 생성 영상의 프레임 사이 움직임이 들쭉날쭉할 때, 움직임 양에 맞춰 시각을 다시 잡는다.

방법
1. 프레임 쌍마다 움직임 크기(밝기 정규화 회색조 960폭, DIS 광류 크기의 중앙값)를 잰다.
2. 누적 움직임 D를 만든다. 목표는 같은 프레임 수로, 움직임이 이웃 평균(--window 프레임)대로 고르게 늘어나는 것.
3. 출력 프레임마다 목표 누적값에 해당하는 원본 시각(소수)을 찾아, 두 원본 프레임 사이를 광류로 보간한다(retime.interp와 같음).
   첫 프레임과 끝 프레임은 원본 그대로 둔다(이음새가 바뀌지 않게).

작은 움직임(프레임당 수 화소)에서만 쓴다. 크로스페이드가 아니라 움직임 보간이다. 무료(로컬 계산만 함).

시작 속도 맞추기(--start-speed S --ramp N): 재시작 조각이 앞 조각보다 느리게 출발할 때, 처음 N 출력 프레임 동안
목표 속도를 S(앞 조각 끝의 같은 방식 움직임 값)에서 원래 속도로 고르게 옮긴다. 그만큼 앞부분이 빨라져 출력 프레임 수가 줄어든다.

--head-only: 램프 구간만 보간하고 그 뒤는 원본 프레임을 그대로 쓴다(도시처럼 세밀한 장면의 선명도 보존).

사용: python3 work/scripts/dejudder.py <입력.mp4> <출력.mp4> [--window 9] [--start-speed 0.24 --ramp 36 [--head-only]]
      python3 work/scripts/dejudder.py --measure <영상.mp4> [--last 24]   # 끝 N프레임의 같은 방식 움직임 평균
"""
import argparse

import cv2
import numpy as np

from retime import interp, read
from vio import writer


def norm_gray(f):
    x = cv2.cvtColor(cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
    x = (x - x.mean()) / (x.std() + 1e-6) * 40 + 128
    return np.clip(x, 0, 255).astype(np.uint8)


def motions(frames):
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    gs = [norm_gray(f) for f in frames]
    return np.array([np.median(np.sqrt((dis.calc(a, b, None) ** 2).sum(-1))) for a, b in zip(gs, gs[1:])])


def head_only_times(d, start_speed, ramp):
    """앞부분만 속도 맞추기: ramp 동안 목표 속도를 S에서 원래 속도로 옮기고, 그 뒤는 원본 프레임(정수 시각) 그대로."""
    n = len(d) + 1
    cum = np.concatenate([[0.0], np.cumsum(d)])
    idx = np.arange(n, dtype=float)
    pos, ts = 0.0, [0.0]
    for k in range(ramp):
        s = np.interp(pos, cum, idx)
        natural = np.interp(s, idx[:-1] + 0.5, d)
        u = (k + 1) / ramp
        w = u * u * (3 - 2 * u)
        pos += (1 - w) * start_speed + w * natural
        ts.append(float(np.interp(pos, cum, idx)))
    end = int(np.ceil(ts[-1]))
    ts = [t * end / ts[-1] for t in ts]  # 램프 끝이 정수 프레임에 닿도록 고르게 늘림
    return np.array(ts + [float(i) for i in range(end + 1, n)])


def source_times(d, window, start_speed=None, ramp=0):
    """출력 프레임 k마다 읽을 원본 시각. d: 프레임 쌍 움직임(n-1개)."""
    n = len(d) + 1
    cum = np.concatenate([[0.0], np.cumsum(d)])
    pad = window // 2
    sm = np.convolve(np.pad(d, pad, mode='edge'), np.ones(window) / window, mode='valid')
    if not start_speed:
        target = np.concatenate([[0.0], np.cumsum(sm)])
        target *= cum[-1] / target[-1]
        return np.interp(target, cum, np.arange(n, dtype=float))
    # 시작 속도 맞추기: 출력 k번째 쌍의 목표 속도 = (1-w)·S + w·(그 지점 원래 속도), w는 ramp 동안 0→1(부드럽게)
    pos, out = 0.0, [0.0]
    k = 0
    while pos < cum[-1]:
        s = np.interp(pos, cum, np.arange(n, dtype=float))
        natural = np.interp(s, np.arange(len(sm)) + 0.5, sm)
        u = min(k / ramp, 1.0) if ramp else 1.0
        w = u * u * (3 - 2 * u)
        pos = min(pos + (1 - w) * start_speed + w * natural, cum[-1])
        out.append(pos)
        k += 1
    return np.interp(np.array(out), cum, np.arange(n, dtype=float))


def measure_tail(path, last):
    frames = read(path)[-(last + 1):]
    return float(motions(frames).mean())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst', nargs='?')
    ap.add_argument('--window', type=int, default=9)
    ap.add_argument('--start-speed', type=float)
    ap.add_argument('--ramp', type=int, default=36)
    ap.add_argument('--measure', action='store_true')
    ap.add_argument('--last', type=int, default=24)
    ap.add_argument('--head-only', action='store_true', help='--start-speed 램프 뒤는 원본 프레임 그대로(보간 없음)')
    a = ap.parse_args()
    if a.measure:
        print(f'{a.src}: 끝 {a.last}프레임 움직임 평균 {measure_tail(a.src, a.last):.3f}')
        return
    frames = read(a.src)
    d = motions(frames)
    if a.head_only:
        times = head_only_times(d, a.start_speed, a.ramp)
    else:
        times = source_times(d, a.window, a.start_speed, a.ramp)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    h, w = frames[0].shape[:2]
    enc = writer(a.dst, w, h)
    made = 0
    for t in times:
        i = int(np.floor(t + 1e-9))
        alpha = t - i
        if alpha < 1e-3 or i >= len(frames) - 1:
            f = frames[min(i, len(frames) - 1)]
        else:
            f = interp(frames[i], frames[i + 1], alpha, dis)
            made += 1
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f'{a.dst}: {len(frames)}프레임 → {len(times)}프레임(보간 {made}), 움직임 들쭉날쭉 {np.std(d / np.convolve(d, np.ones(5) / 5, mode="same")):.2f}')


if __name__ == '__main__':
    main()
