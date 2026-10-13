"""연결부 속도 맞춤: 클립 앞·뒤 일부의 재생 속도를 선형으로 바꾼다(그 밖은 원래 속도·원래 프레임).

속도가 1보다 작은 구간은 광류(DIS)로 두 프레임 사이 중간 프레임을 만들어 채운다.
프레임당 이동이 작고 구조가 일관된 구간에서만 쓴다(크로스페이드가 아니라 움직임 보간).

사용: python3 work/scripts/retime.py <입력.mp4> <출력.mp4> [--head 시작속도 출력프레임수] [--tail 끝속도 출력프레임수]
  예) --head 0.07 36 : 처음에는 원래 속도의 0.07배로 시작해 36프레임(1.5초) 동안 1배까지 올라감
      --tail 0.48 24 : 마지막 24프레임(1초) 동안 1배에서 0.48배로 내려가 원본 마지막 프레임에서 끝남
"""
import argparse
import subprocess

import cv2
import numpy as np


def read(path):
    cap = cv2.VideoCapture(path)
    out = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        out.append(f)
    return out


def source_times(n, head=None, tail=None):
    """출력 프레임마다 읽을 원본 시각(프레임 단위, 소수 가능)."""
    fwd = [0.0]
    if head:
        v0, r = head
        inc = np.array([v0 + (1 - v0) * k / r for k in range(1, r + 1)])
        inc *= round(inc.sum()) / inc.sum()  # 램프 끝이 정수 프레임에 닿도록 증분 전체를 조금씩 보정
        fwd += list(np.cumsum(inc))
        fwd[-1] = float(round(fwd[-1]))
    back = []
    if tail:
        v1, r = tail
        t = float(n - 1)
        for k in range(r):
            back.append(t)
            t -= v1 + (1 - v1) * k / r
        start_tail = float(round(t))
    else:
        start_tail = float(n - 1)
    mid_start = int(fwd[-1])
    times = fwd[:-1] + [float(i) for i in range(mid_start, int(start_tail) + 1)]
    if tail:
        # 정수 지점에서 램프로 넘어가며 생기는 반올림 차이를 램프 구간에 고르게 나눠 흡수
        ramp = list(reversed(back))
        shift = (ramp[0] - start_tail) - (ramp[1] - ramp[0]) if len(ramp) > 1 else 0
        ramp = [x - shift * (1 - i / (len(ramp) - 1)) for i, x in enumerate(ramp)] if len(ramp) > 1 else ramp
        times += [x for x in ramp if x > times[-1]]
    return times


def interp(a, b, alpha, dis):
    h, w = a.shape[:2]
    sa = cv2.cvtColor(cv2.resize(a, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    sb = cv2.cvtColor(cv2.resize(b, (w // 2, h // 2), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    f_ab = cv2.resize(dis.calc(sa, sb, None), (w, h)) * 2
    f_ba = cv2.resize(dis.calc(sb, sa, None), (w, h)) * 2
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    al = np.float32(alpha)
    wa = cv2.remap(a, gx - al * f_ab[..., 0], gy - al * f_ab[..., 1], cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REFLECT)
    wb = cv2.remap(b, gx - (1 - al) * f_ba[..., 0], gy - (1 - al) * f_ba[..., 1], cv2.INTER_LINEAR,
                   borderMode=cv2.BORDER_REFLECT)
    return cv2.addWeighted(wa, 1 - alpha, wb, alpha, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--head', nargs=2, type=float)
    ap.add_argument('--tail', nargs=2, type=float)
    a = ap.parse_args()
    frames = read(a.src)
    n = len(frames)
    head = (a.head[0], int(a.head[1])) if a.head else None
    tail = (a.tail[0], int(a.tail[1])) if a.tail else None
    times = source_times(n, head, tail)
    assert abs(times[-1] - (n - 1)) < 1e-6 and all(t2 > t1 for t1, t2 in zip(times, times[1:]))
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    h, w = frames[0].shape[:2]
    enc = subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24',
                            '-s', f'{w}x{h}', '-r', '24', '-i', '-', '-c:v', 'libx264', '-preset', 'slow',
                            '-crf', '16', '-pix_fmt', 'yuv420p', a.dst], stdin=subprocess.PIPE)
    made = 0
    for t in times:
        t = float(t)
        i = int(np.floor(t + 1e-9))
        alpha = t - i
        if alpha < 1e-3 or i >= n - 1:
            f = frames[min(i, n - 1)]
        else:
            f = interp(frames[i], frames[i + 1], alpha, dis)
            made += 1
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f'{a.dst}: 원본 {n}프레임 → 출력 {len(times)}프레임(보간 {made}프레임)')


if __name__ == '__main__':
    main()
