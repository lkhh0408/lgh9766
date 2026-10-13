#!/usr/bin/env python3
"""1단계 이미지 연속성 분석 — 수치 측정.

원본(NNN_83Tower.png)은 읽기만 하고 수정하지 않는다. 결과는 work/analysis/ 에 쓴다.

프레임별: 평균 밝기, 하늘(상단 20%) 밝기, 색온도 지표(R/B), 채도, 어두운 장면의 점광원 비율(야간 조명).
인접 쌍별: SIFT 매칭으로 구한 카메라 이동(유사변환: 확대율·회전·평행이동), 대응점 수,
          조밀 광류 중앙값(화면 전체 움직임 크기), 전역 정렬 후 남는 움직임(시차·구조 차이),
          정렬 후 픽셀 차이(구조·조명 차이), 밝기·색 변화량.

실행: python3 work/scripts/analyze_frames.py   (저장소 루트에서)
"""
import csv, glob, json, math, os, re, sys
import cv2
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, "work", "analysis")
AW, AH = 832, 468  # 분석 해상도 (원본 1664 폭의 절반)


def frames():
    fs = []
    for p in glob.glob(os.path.join(ROOT, "*_83Tower.png")):
        m = re.match(r"(\d{3})_83Tower\.png$", os.path.basename(p))
        if m:
            fs.append((int(m.group(1)), p))
    return sorted(fs)


def load(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR)
    h, w = im.shape[:2]
    cw, ch = 1664, 936
    im = im[(h - ch) // 2:(h - ch) // 2 + ch, (w - cw) // 2:(w - cw) // 2 + cw]
    return cv2.resize(im, (AW, AH), interpolation=cv2.INTER_AREA)


def photometry(im):
    f = im.astype(np.float32)
    b, g, r = f[..., 0], f[..., 1], f[..., 2]
    Y = 0.299 * r + 0.587 * g + 0.114 * b
    hsv = cv2.cvtColor(im, cv2.COLOR_BGR2HSV)
    sky = Y[: AH // 5]
    mid = (Y > 40) & (Y < 220)
    rb = float((r[mid].mean() + 1) / (b[mid].mean() + 1)) if mid.any() else float("nan")
    # 점광원: 어두운 주변 속의 작은 밝은 점 (top-hat)
    th = cv2.morphologyEx(Y.astype(np.uint8), cv2.MORPH_TOPHAT, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7)))
    lights = float(((th > 60) & (Y > 150)).mean() * 100) if np.median(Y) < 90 else 0.0
    return dict(luma=float(Y.mean()), luma_p10=float(np.percentile(Y, 10)), luma_p90=float(np.percentile(Y, 90)),
                sky_luma=float(sky.mean()), rb_ratio=rb, saturation=float(hsv[..., 1].mean()), point_lights_pct=lights)


def main():
    fs = frames()
    print(len(fs), "frames", flush=True)
    sift = cv2.SIFT_create(5000)
    bf = cv2.BFMatcher()
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    rows_f, rows_p, prev = [], [], None
    for n, p in fs:
        im = load(p)
        g = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        k, d = sift.detectAndCompute(g, None)
        ph = photometry(im)
        rows_f.append(dict(frame=n, **{a: round(v, 3) for a, v in ph.items()}))
        if prev is not None:
            pn, pim, pg, pk, pd, pph = prev
            rec = dict(pair=f"{pn:03d}-{n:03d}")
            m = [a for a, b in bf.knnMatch(pd, d, k=2) if a.distance < 0.75 * b.distance] if pd is not None and d is not None else []
            rec["matches"] = len(m)
            M, inl = None, 0
            if len(m) >= 12:
                p0 = np.float32([pk[a.queryIdx].pt for a in m]); p1 = np.float32([k[a.trainIdx].pt for a in m])
                M, mask = cv2.estimateAffinePartial2D(p0, p1, method=cv2.RANSAC, ransacReprojThreshold=3.0)
                inl = int(mask.sum()) if M is not None else 0
            rec["inliers"] = inl
            rel = M is not None and inl >= 40
            if rel:
                s = math.hypot(M[0, 0], M[1, 0])
                c = np.array([AW / 2, AH / 2])
                d_c = M[:, :2] @ c + M[:, 2] - c
                rec.update(scale=round(s, 4), rot_deg=round(math.degrees(math.atan2(M[1, 0], M[0, 0])), 3),
                           shift_x_pct=round(d_c[0] / AW * 100, 2), shift_y_pct=round(d_c[1] / AH * 100, 2))
            fl = dis.calc(pg, g, None)
            rec["flow_med_pct"] = round(float(np.median(np.hypot(fl[..., 0], fl[..., 1]))) / AW * 100, 3)
            if rel:
                Minv = cv2.invertAffineTransform(M)
                al = cv2.warpAffine(im, Minv, (AW, AH), borderMode=cv2.BORDER_REFLECT)
                valid = cv2.warpAffine(np.ones((AH, AW), np.uint8), Minv, (AW, AH)) > 0
                r = dis.calc(pg, cv2.cvtColor(al, cv2.COLOR_BGR2GRAY), None)
                rec["residual_med_pct"] = round(float(np.median(np.hypot(r[..., 0], r[..., 1])[valid])) / AW * 100, 3)
                rec["aligned_mad"] = round(float(np.abs(pim.astype(np.float32) - al.astype(np.float32))[valid].mean()), 2)
            rec["d_luma"] = round(ph["luma"] - pph["luma"], 2)
            rec["d_rb"] = round(ph["rb_ratio"] - pph["rb_ratio"], 3)
            rec["d_sky"] = round(ph["sky_luma"] - pph["sky_luma"], 2)
            rows_p.append(rec)
            print(rec, flush=True)
        prev = (n, im, g, k, d, ph)
    for name, rows in (("metrics_frames.csv", rows_f), ("metrics_pairs.csv", rows_p)):
        keys = sorted({k for r in rows for k in r}, key=lambda x: list(rows[0].keys()).index(x) if x in rows[0] else 99)
        with open(os.path.join(OUT, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(rows)
    print("written", OUT)


if __name__ == "__main__":
    main()
