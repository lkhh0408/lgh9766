"""이음새 다듬기: 새로 시작한 조각(첫 장면을 다시 그린 조각)이 앞 조각과 이어질 때 생기는 색·질감 튐을 줄인다. 무료(로컬 계산만 함).

하는 일(앞쪽 모드, 기본)
1. 색 맞춤: 조각 첫 프레임의 Lab 평균·표준편차를 앞 조각 마지막 프레임에 맞춘다. 보정 세기는 첫 프레임 1에서
   --color-frames 프레임 동안 부드럽게 0이 된다(원래 색으로 천천히 돌아감).
2. 질감 전환: 첫 --texture-frames 프레임 동안 앞 조각 마지막 프레임을 광류로 각 프레임의 위치에 맞게 옮겨(warp) 섞는다.
   섞는 비중은 0.9에서 0으로 줄어든다. 두 그림의 모양이 다른 곳(옮긴 뒤에도 차이가 큰 곳)은 섞지 않아 이중 윤곽을 막는다.
   장면 전체를 섞는 크로스페이드가 아니라, 같은 장면을 다르게 그린 두 그림 사이의 0.4초 질감 전환이다(보고서에 밝힘).

뒤쪽 모드(--tail): 조각의 마지막 프레임들을 다음 조각 첫 프레임 쪽으로 맞춘다(다음 조각을 건드리지 않을 때, 예: 승인본).

출력: 다듬은 앞(또는 뒤) N프레임만 담은 4K 파일. 자르기 목록에서 이 파일 + 원래 조각의 나머지를 이어 쓴다.

사용
  python3 work/scripts/seam_polish.py --ref 앞조각.mp4 --ref-frame -1 --clip 조각.mp4 --start 1 --out 머리.mp4
  python3 work/scripts/seam_polish.py --tail --ref 다음조각.mp4 --ref-frame 0 --clip 조각.mp4 --end 190 --out 꼬리.mp4
  선택: --color-frames 36 --texture-frames 10 --blend 0.9
"""
import argparse

import cv2
import numpy as np

from vio import read_frame, read_frames, writer


def read_range(path, a, b):
    return read_frames(path, a, b - a)  # ffmpeg로 정확한 색 변환(vio.py)


def frame_at(path, idx):
    return read_frame(path, idx)


def to_lab(f):
    return cv2.cvtColor(f.astype(np.float32) / 255, cv2.COLOR_BGR2LAB)  # 실수 Lab(정수 Lab 왕복의 반올림 오차 없음)


def lab_stats(f):
    lab = to_lab(cv2.resize(f, (960, 540), interpolation=cv2.INTER_AREA))
    return lab.reshape(-1, 3).mean(0), lab.reshape(-1, 3).std(0) + 1e-3


def color_correct(f, src, dst, strength):
    if strength < 0.01:
        return f
    lab = to_lab(f)
    m_s, s_s = src
    m_d, s_d = dst
    fixed = (lab - m_s) * (s_d / s_s) + m_d
    lab = lab + strength * (fixed - lab)
    return np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2BGR) * 255 + 0.5, 0, 255).astype(np.uint8)


def warp_to(ref, f, dis):
    """ref를 f의 위치에 맞게 옮긴 그림과, 옮긴 뒤에도 모양이 다른 곳(0~1)."""
    h, w = f.shape[:2]
    small = (960, 540)
    gf = cv2.cvtColor(cv2.resize(f, small, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    gr = cv2.cvtColor(cv2.resize(ref, small, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    fl = dis.calc(gf, gr, None)
    sx, sy = w / small[0], h / small[1]
    flow = cv2.resize(fl, (w, h))
    flow[..., 0] *= sx
    flow[..., 1] *= sy
    gx, gy = np.meshgrid(np.arange(w, dtype=np.float32), np.arange(h, dtype=np.float32))
    warped = cv2.remap(ref, gx + flow[..., 0], gy + flow[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    sgx, sgy = np.meshgrid(np.arange(small[0], dtype=np.float32), np.arange(small[1], dtype=np.float32))
    gw = cv2.remap(gr, sgx + fl[..., 0], sgy + fl[..., 1], cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)
    diff = cv2.GaussianBlur(np.abs(gw.astype(np.float32) - gf.astype(np.float32)), (0, 0), 3)
    mismatch = np.clip((diff - MISMATCH_LO) / MISMATCH_SPAN, 0, 1)
    return warped, cv2.resize(cv2.GaussianBlur(mismatch, (0, 0), 4), (w, h))


MISMATCH_LO, MISMATCH_SPAN = 30.0, 30.0  # 옮긴 뒤 회색조 차이(흐림 후)가 이 값을 넘는 곳만 섞지 않음(모양이 다른 곳)


def smooth(u):
    u = min(max(u, 0.0), 1.0)
    return u * u * (3 - 2 * u)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ref', required=True, help='맞출 기준 영상(앞쪽 모드: 앞 조각, 뒤쪽 모드: 다음 조각)')
    ap.add_argument('--ref-frame', type=int, required=True, help='기준 프레임 번호(-1 = 마지막)')
    ap.add_argument('--clip', required=True)
    ap.add_argument('--start', type=int, default=0, help='앞쪽 모드: 다듬기 시작 프레임(자르기 목록에서 쓰는 첫 프레임)')
    ap.add_argument('--end', type=int, help='뒤쪽 모드: 자르기 목록에서 쓰는 마지막 프레임(포함)')
    ap.add_argument('--tail', action='store_true')
    ap.add_argument('--color-frames', type=int, default=36)
    ap.add_argument('--texture-frames', type=int, default=10)
    ap.add_argument('--blend', type=float, default=0.9)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    ref = frame_at(a.ref, a.ref_frame)
    n = max(a.color_frames, a.texture_frames)
    if a.tail:
        frames = read_range(a.clip, a.end - n + 1, a.end + 1)
        order = list(range(len(frames) - 1, -1, -1))  # 끝 프레임부터 거꾸로 k = 0, 1, ...
        anchor = frames[-1]
    else:
        frames = read_range(a.clip, a.start, a.start + n)
        order = list(range(len(frames)))
        anchor = frames[0]
    dst = lab_stats(ref)
    src = lab_stats(anchor)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    out = [None] * len(frames)
    for k, i in enumerate(order):
        f = color_correct(frames[i], src, dst, smooth(1 - k / a.color_frames))
        if k < a.texture_frames:
            wgt = a.blend * smooth(1 - k / a.texture_frames)
            warped, mismatch = warp_to(ref, f, dis)
            m = (wgt * (1 - mismatch))[..., None]
            f = (f.astype(np.float32) * (1 - m) + warped.astype(np.float32) * m).astype(np.uint8)
        out[i] = f
    h, w = out[0].shape[:2]
    enc = writer(a.out, w, h, crf=12)
    for f in out:
        enc.stdin.write(f.tobytes())
    enc.stdin.close()
    enc.wait()
    print(f'{a.out}: {"뒤" if a.tail else "앞"} {len(out)}프레임 다듬음(색 {a.color_frames}, 질감 {a.texture_frames})')


if __name__ == '__main__':
    main()
