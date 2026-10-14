"""두 키프레임이 '같은 장소를 카메라만 옮겨 찍은' 관계인지 측정.

- 배경(가운데 타워 띠 제외)에서 SIFT 대응점을 찾고, 기본 행렬(F) RANSAC으로
  하나의 강체 카메라 이동으로 설명되는 대응점(=같은 3D 장면에서 나온 점)만 센다.
  카메라가 움직여 생기는 시차는 허용하고, 세부를 새로 그린 곳은 대응점이 사라진다.
- 타워 띠 안 대응점으로 타워 크기 변화(배율)도 추정한다.

사용: python3 work/scripts/keyframe_consistency.py <기준.png> <대상.png> [<대상2.png> ...]
"""
import sys

import cv2
import numpy as np

SIZE = (1672, 941)


def load(p):
    return cv2.resize(cv2.imread(p), SIZE, interpolation=cv2.INTER_AREA)


def feats(img, mask):
    g = cv2.createCLAHE(3.0, (8, 8)).apply(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
    return cv2.SIFT_create(6000).detectAndCompute(g, mask)


def band_masks(h, w):
    bg = np.full((h, w), 255, np.uint8)
    bg[:, int(w * 0.38):int(w * 0.62)] = 0
    bg[:int(h * 0.25)] = 0  # 하늘·구름 제외
    tw = np.zeros((h, w), np.uint8)
    tw[:, int(w * 0.40):int(w * 0.60)] = 255
    return bg, tw


def measure(a, b):
    h, w = a.shape[:2]
    bg, tw = band_masks(h, w)
    ka, da = feats(a, bg)
    kb, db = feats(b, bg)
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
    res = {'matches': len(good), 'F_inliers': 0, 'inlier_ratio': 0.0}
    if len(good) >= 12:
        pa = np.float32([ka[m.queryIdx].pt for m in good])
        pb = np.float32([kb[m.trainIdx].pt for m in good])
        F, inl = cv2.findFundamentalMat(pa, pb, cv2.FM_RANSAC, 1.5, 0.999)
        if inl is not None:
            res['F_inliers'] = int(inl.sum())
            res['inlier_ratio'] = res['F_inliers'] / max(1, min(len(ka), len(kb)))
    # 타워 배율
    ka, da = feats(a, tw)
    kb, db = feats(b, tw)
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance] if da is not None and db is not None else []
    res['tower_scale'] = None
    if len(good) >= 8:
        pa = np.float32([ka[m.queryIdx].pt for m in good])
        pb = np.float32([kb[m.trainIdx].pt for m in good])
        M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=4)
        if M is not None and inl.sum() >= 6:
            res['tower_scale'] = round(float(np.hypot(M[0, 0], M[1, 0])), 3)
    return res


def main():
    base = load(sys.argv[1])
    for p in sys.argv[2:]:
        r = measure(base, load(p))
        print(f"{p.split('/')[-1]:44s} 배경 대응 {r['matches']:5d}  같은장면 일치 {r['F_inliers']:5d}  "
              f"비율 {r['inlier_ratio']:.3f}  타워 배율 {r['tower_scale']}")


if __name__ == '__main__':
    main()
