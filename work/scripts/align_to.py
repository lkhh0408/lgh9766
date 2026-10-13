"""생성·편집된 이미지를 기준 이미지의 기하(위치·크기)에 맞춰 정렬한다.

하늘(위 30%)을 제외한 지상부 SIFT 대응점으로 닮음변환을 구해 대상 이미지를 기준 해상도로 워핑한다.
사용: python3 work/scripts/align_to.py <대상> <기준> <출력>
"""
import sys
import cv2
import numpy as np


def align(src, ref, sky_frac=0.3):
    src = cv2.resize(src, (ref.shape[1], ref.shape[0]), interpolation=cv2.INTER_AREA)
    clahe = cv2.createCLAHE(3.0, (8, 8))
    ga = clahe.apply(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY))
    gb = clahe.apply(cv2.cvtColor(src, cv2.COLOR_BGR2GRAY))
    mask = np.zeros_like(ga)
    mask[int(ref.shape[0] * sky_frac):] = 255
    sift = cv2.SIFT_create(4000)
    ka, da = sift.detectAndCompute(ga, mask)
    kb, db = sift.detectAndCompute(gb, mask)
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(pb, pa, ransacReprojThreshold=3)
    out = cv2.warpAffine(src, M, (ref.shape[1], ref.shape[0]), flags=cv2.INTER_LANCZOS4,
                         borderMode=cv2.BORDER_REFLECT)
    return out, M, int(inl.sum())


if __name__ == '__main__':
    src, ref, dst = sys.argv[1:4]
    out, M, n = align(cv2.imread(src), cv2.imread(ref))
    cv2.imwrite(dst, out)
    print(f'inliers {n}, scale {np.hypot(M[0, 0], M[1, 0]):.4f}, shift {M[:, 2].round(2)}')
