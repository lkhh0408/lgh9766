#!/usr/bin/env python3
"""색 보정(리터칭 가능 범위 확인용): 대상 이미지의 색 분포를 기준 이미지에 맞춘다 (Lab 공간 평균·표준편차 맞춤).
원본은 수정하지 않고 결과를 새 파일로 저장한다.
사용: python3 work/scripts/color_match.py <대상.png> <기준.png> <출력.png> [강도 0~1]
"""
import sys
import cv2
import numpy as np

def color_match(src, ref, strength=1.0):
    s = cv2.cvtColor(src, cv2.COLOR_BGR2LAB).astype(np.float32)
    r = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.float32)
    out = s.copy()
    for c in range(3):
        sm, ss = s[..., c].mean(), s[..., c].std() + 1e-6
        rm, rs = r[..., c].mean(), r[..., c].std()
        out[..., c] = (s[..., c] - sm) * (rs / ss) + rm
    out = s + (out - s) * strength
    return cv2.cvtColor(np.clip(out, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)

if __name__ == "__main__":
    src, ref, dst = sys.argv[1:4]
    k = float(sys.argv[4]) if len(sys.argv) > 4 else 1.0
    cv2.imwrite(dst, color_match(cv2.imread(src), cv2.imread(ref), k))
