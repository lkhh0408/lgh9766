"""끝 키프레임의 배경을 시작 키프레임 배경으로 맞춘다(타워는 끝 키프레임 그대로).

시작·끝 원본 이미지가 같은 장소를 세부가 다르게 그린 경우, 영상 모델이 비행 중에 세부를 바꿔 그려
"건물이 생겨나는" 느낌이 생긴다. 먼 배경은 카메라가 다가가도 거의 평면처럼 움직이므로,
시작 이미지를 호모그래피로 끝 시점에 맞춰 변형해 배경으로 쓰고 그 위에 끝 이미지의 타워만 얹는다.

사용: python3 work/scripts/harmonize_bg.py <시작.png> <끝.png> <출력.png> [--debug 폴더]
"""
import argparse
import os

import cv2
import numpy as np


def tower_mask(img, x0=0.30, x1=0.70):
    """GrabCut으로 화면 가운데 타워를 분리(1=타워)."""
    h, w = img.shape[:2]
    mask = np.full((h, w), cv2.GC_BGD, np.uint8)
    mask[:, int(w * x0):int(w * x1)] = cv2.GC_PR_BGD
    # 타워 축 근처는 '아마 타워'로 시작
    b, g, r = [img[..., i].astype(int) for i in range(3)]
    sky = (b > r + 25) & (b > 110)
    cx = w // 2
    cols = img[:, int(w * 0.40):int(w * 0.60)]
    mask[:, int(w * 0.44):int(w * 0.56)] = cv2.GC_PR_FGD
    mask[sky] = cv2.GC_BGD
    bgd, fgd = np.zeros((1, 65), np.float64), np.zeros((1, 65), np.float64)
    cv2.grabCut(img, mask, None, bgd, fgd, 6, cv2.GC_INIT_WITH_MASK)
    m = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 1, 0).astype(np.uint8)
    # 가장 큰 연결 성분(타워)만 남김
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    if n > 1:
        k = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        m = (lab == k).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return m


def bg_homography(src, dst, dst_tower):
    """타워를 뺀 영역의 SIFT 대응점으로 src→dst 호모그래피."""
    clahe = cv2.createCLAHE(3.0, (8, 8))
    gs = clahe.apply(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY))
    gd = clahe.apply(cv2.cvtColor(dst, cv2.COLOR_BGR2GRAY))
    ms = np.full(gs.shape, 255, np.uint8)
    ms[:, int(src.shape[1] * 0.38):int(src.shape[1] * 0.62)] = 0
    md = np.where(cv2.dilate(dst_tower, np.ones((41, 41), np.uint8)) > 0, 0, 255).astype(np.uint8)
    sift = cv2.SIFT_create(6000)
    ks, ds = sift.detectAndCompute(gs, ms)
    kd, dd = sift.detectAndCompute(gd, md)
    good = [m for m, n in cv2.BFMatcher().knnMatch(ds, dd, k=2) if m.distance < 0.75 * n.distance]
    ps = np.float32([ks[m.queryIdx].pt for m in good])
    pd = np.float32([kd[m.trainIdx].pt for m in good])
    H, inl = cv2.findHomography(ps, pd, cv2.RANSAC, 4.0)
    return H, int(inl.sum()), len(good)


def tower_union(dst, warped, band=(0.28, 0.72)):
    """두 이미지가 크게 다른 가운데 영역(끝 타워 + 변형된 시작 타워) 마스크."""
    h, w = dst.shape[:2]
    a = cv2.GaussianBlur(dst, (0, 0), 4).astype(np.float32)
    b = cv2.GaussianBlur(warped, (0, 0), 4).astype(np.float32)
    r = np.abs(a - b).mean(2)
    r8 = np.clip(r * 3, 0, 255).astype(np.uint8)
    x0, x1 = int(w * band[0]), int(w * band[1])
    thr, _ = cv2.threshold(r8[:, x0:x1], 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    m = np.zeros((h, w), np.uint8)
    m[:, x0:x1] = (r8[:, x0:x1] > thr).astype(np.uint8)
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((15, 15), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((7, 7), np.uint8))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(m, 8)
    keep = np.zeros_like(m)
    cx = w // 2
    for k in range(1, n):
        x, y, ww, hh, area = stats[k]
        if area > 0.002 * h * w and x <= cx + w * 0.1 and x + ww >= cx - w * 0.1:
            keep[lab == k] = 1
    # 구멍 메우기(지지대 사이 등)
    filled = keep.copy()
    cnts, _ = cv2.findContours(keep, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    cv2.drawContours(filled, cnts, -1, 1, thickness=cv2.FILLED)
    return cv2.dilate(filled, np.ones((21, 21), np.uint8)), thr


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('start')
    ap.add_argument('end')
    ap.add_argument('out')
    ap.add_argument('--debug')
    a = ap.parse_args()
    src, dst = cv2.imread(a.start), cv2.imread(a.end)
    h, w = dst.shape[:2]
    band = np.zeros((h, w), np.uint8)
    band[:, int(w * 0.38):int(w * 0.62)] = 1
    H, ninl, nm = bg_homography(src, dst, band)
    warped = cv2.warpPerspective(src, H, (w, h), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)
    valid = cv2.warpPerspective(np.ones(src.shape[:2], np.uint8), H, (w, h), flags=cv2.INTER_NEAREST)
    union, thr = tower_union(dst, warped)
    keep_end = np.maximum(union, 1 - valid)  # 변형 후 비는 가장자리도 끝 이미지 사용
    alpha = cv2.GaussianBlur(keep_end.astype(np.float32), (0, 0), 8)[..., None]
    out = (dst.astype(np.float32) * alpha + warped.astype(np.float32) * (1 - alpha)).clip(0, 255).astype(np.uint8)
    cv2.imwrite(a.out, out)
    print(f'배경 대응점 {nm}, 정합 {ninl}, 끝 이미지 유지 영역 {keep_end.mean() * 100:.1f}% (임계 {thr:.0f})')
    if a.debug:
        os.makedirs(a.debug, exist_ok=True)
        vis = dst.copy()
        vis[keep_end > 0] = (vis[keep_end > 0] * 0.5 + np.array([0, 0, 255]) * 0.5).astype(np.uint8)
        cv2.imwrite(os.path.join(a.debug, 'keep_end_mask.jpg'), vis)
        cv2.imwrite(os.path.join(a.debug, 'warped_start.jpg'), warped)


if __name__ == '__main__':
    main()
