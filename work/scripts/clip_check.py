"""생성 클립 측정: 프레임 간 이동량(정지·멈칫·급변 확인), 밝기 변화, 시작·끝 프레임과 키프레임의 일치도.

사용: python3 work/scripts/clip_check.py <클립.mp4> [--first 시작이미지] [--last 끝이미지] [--out 폴더]
출력: <out>/<이름>_motion.csv, <이름>_motion.png(이동량 그래프), <이름>_sheet.jpg(1초 간격 프레임)
이동량은 640x360 축소 영상의 DIS 광류로 계산하며 화면 폭 대비 %/프레임으로 적는다.
"""
import argparse
import csv
import os

import cv2
import numpy as np
from PIL import Image, ImageDraw

W, H = 640, 360


def read_frames(path):
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    return frames, fps


def global_motion(flow):
    """광류에서 닮음변환(이동·배율·회전)을 추정."""
    ys, xs = np.mgrid[8:H:16, 8:W:16]
    p0 = np.stack([xs.ravel(), ys.ravel()], 1).astype(np.float32)
    d = flow[ys.ravel(), xs.ravel()]
    M, _ = cv2.estimateAffinePartial2D(p0, p0 + d, ransacReprojThreshold=1.5)
    if M is None:
        return 0, 0, 1, 0
    s = float(np.hypot(M[0, 0], M[1, 0]))
    r = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    # 화면 중심 기준 이동량
    c = np.array([W / 2, H / 2])
    t = M[:, :2] @ c + M[:, 2] - c
    return float(t[0]) / W * 100, float(t[1]) / W * 100, s, r


def match(img_a, img_b, sky_frac=0.3):
    """두 이미지의 지상부 SIFT 정렬: (대응점 수, 배율, 이동 %, 정렬 후 평균 밝기차)."""
    a = cv2.resize(img_a, (960, 540), interpolation=cv2.INTER_AREA)
    b = cv2.resize(img_b, (960, 540), interpolation=cv2.INTER_AREA)
    clahe = cv2.createCLAHE(3.0, (8, 8))
    ga = clahe.apply(cv2.cvtColor(a, cv2.COLOR_BGR2GRAY))
    gb = clahe.apply(cv2.cvtColor(b, cv2.COLOR_BGR2GRAY))
    mask = np.zeros_like(ga)
    mask[int(540 * sky_frac):] = 255
    sift = cv2.SIFT_create(3000)
    ka, da = sift.detectAndCompute(ga, mask)
    kb, db = sift.detectAndCompute(gb, mask)
    if da is None or db is None:
        return 0, None, None, None
    good = [m for m, n in cv2.BFMatcher().knnMatch(da, db, k=2) if m.distance < 0.75 * n.distance]
    if len(good) < 8:
        return len(good), None, None, None
    pa = np.float32([ka[m.queryIdx].pt for m in good])
    pb = np.float32([kb[m.trainIdx].pt for m in good])
    M, inl = cv2.estimateAffinePartial2D(pb, pa, ransacReprojThreshold=3)
    if M is None:
        return 0, None, None, None
    s = float(np.hypot(M[0, 0], M[1, 0]))
    warped = cv2.warpAffine(b, M, (960, 540))
    valid = cv2.warpAffine(np.ones_like(gb), M, (960, 540)) > 0
    lo = slice(int(540 * sky_frac), 540)
    mad = float(np.abs(a.astype(int) - warped.astype(int)).mean(2)[lo][valid[lo]].mean())
    return int(inl.sum()), s, (M[:, 2] / 960 * 100).round(2).tolist(), mad


def continuity(small, step=6, gap=12):
    """0.5초(12프레임) 떨어진 프레임 사이의 ORB 대응점 중 호모그래피 정합 비율.
    같은 장면을 카메라가 움직이며 찍으면 높게 유지되고, 장면 전환·디졸브 구간에서는 급락한다."""
    orb = cv2.ORB_create(1500)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
    out = []
    for i in range(0, len(small) - gap, step):
        ka, da = orb.detectAndCompute(small[i], None)
        kb, db = orb.detectAndCompute(small[i + gap], None)
        ratio = 0.0
        if da is not None and db is not None and len(ka) > 20 and len(kb) > 20:
            m = bf.match(da, db)
            if len(m) >= 12:
                pa = np.float32([ka[x.queryIdx].pt for x in m])
                pb = np.float32([kb[x.trainIdx].pt for x in m])
                _, inl = cv2.findHomography(pa, pb, cv2.RANSAC, 4.0)
                ratio = float(inl.sum()) / min(len(ka), len(kb)) if inl is not None else 0.0
        out.append((i, ratio))
    return out


def plot(rows, path, title):
    pw, ph, m = 900, 300, 40
    img = Image.new('RGB', (pw, ph), 'white')
    d = ImageDraw.Draw(img)
    vals = [r['speed_pct'] for r in rows]
    top = max(max(vals) * 1.1, 0.3)
    d.text((m, 5), f'{title}  frame-to-frame motion (% width), max axis {top:.2f}', fill='black')
    d.line([(m, ph - m), (pw - 10, ph - m)], fill='gray')
    d.line([(m, 20), (m, ph - m)], fill='gray')
    n = len(vals)
    for key, col in (('speed_pct', 'blue'), ('tx_abs', 'green'), ('ty_abs', 'orange')):
        pts = []
        for i, r in enumerate(rows):
            v = abs(r[key.replace('_abs', '_pct')]) if key.endswith('_abs') else r[key]
            pts.append((m + i * (pw - m - 10) / max(n - 1, 1), ph - m - v / top * (ph - m - 20)))
        d.line(pts, fill=col, width=2)
    d.text((pw - 250, 22), 'blue=median flow  green=|pan x|  orange=|pan y|', fill='black')
    for s in range(0, n // 24 + 1):
        x = m + s * 24 * (pw - m - 10) / max(n - 1, 1)
        d.text((x - 3, ph - m + 5), f'{s}s', fill='black')
    img.save(path)


def sheet(frames, fps, path, every=1.0):
    idx = [min(int(round(t * fps)), len(frames) - 1) for t in np.arange(0, len(frames) / fps + 1e-6, every)]
    idx[-1] = len(frames) - 1
    tw, th = 480, 270
    cols = 3
    rows = (len(idx) + cols - 1) // cols
    out = Image.new('RGB', (tw * cols, th * rows), 'black')
    for k, i in enumerate(idx):
        im = Image.fromarray(cv2.cvtColor(frames[i], cv2.COLOR_BGR2RGB)).resize((tw, th))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 90, 18], fill='black')
        d.text((4, 3), f'{i / fps:.2f}s #{i}', fill='yellow')
        out.paste(im, ((k % cols) * tw, (k // cols) * th))
    out.save(path, quality=88)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('clip')
    ap.add_argument('--first')
    ap.add_argument('--last')
    ap.add_argument('--out', default=None)
    a = ap.parse_args()
    out = a.out or os.path.join(os.path.dirname(a.clip), '..', 'check')
    os.makedirs(out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.clip))[0]
    frames, fps = read_frames(a.clip)
    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    small = [cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY) for f in frames]
    rows = []
    for i in range(len(frames) - 1):
        fl = dis.calc(small[i], small[i + 1], None)
        mag = np.hypot(fl[..., 0], fl[..., 1]) / W * 100
        tx, ty, s, r = global_motion(fl)
        band = {k: float(np.median(mag[int(H * y0):int(H * y1)])) for k, (y0, y1) in
                {'top': (0, .4), 'mid': (.4, .65), 'bot': (.65, 1)}.items()}
        diff = float(np.abs(small[i].astype(int) - small[i + 1].astype(int)).mean())
        rows.append(dict(frame=i + 1, t=round((i + 1) / fps, 3), speed_pct=round(float(np.median(mag)), 4),
                         top_pct=round(band['top'], 4), mid_pct=round(band['mid'], 4), bot_pct=round(band['bot'], 4),
                         tx_pct=round(tx, 4), ty_pct=round(ty, 4), scale=round(s, 5), rot_deg=round(r, 4),
                         luma=round(float(small[i + 1].mean()), 2), absdiff=round(diff, 2)))
    with open(os.path.join(out, f'{name}_motion.csv'), 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    plot(rows, os.path.join(out, f'{name}_motion.png'), name)
    sheet(frames, fps, os.path.join(out, f'{name}_sheet.jpg'))

    sp = np.array([r['speed_pct'] for r in rows])
    n = len(sp)
    q = max(n // 8, 1)
    print(f'{name}: {len(frames)} frames @ {fps:.2f} fps')
    print(f'  이동량 중앙값 {np.median(sp):.3f}%/f, 최소 {sp.min():.3f} (t={rows[int(sp.argmin())]["t"]}s), 최대 {sp.max():.3f}')
    print(f'  첫 1/8 평균 {sp[:q].mean():.3f}, 중간 평균 {sp[q:-q].mean():.3f}, 끝 1/8 평균 {sp[-q:].mean():.3f}')
    jumps = [r for r in rows if r['absdiff'] > 4 * np.median([x['absdiff'] for x in rows]) + 3]
    print(f'  급변(컷 의심) 프레임: {[r["t"] for r in jumps] or "없음"}')
    print(f'  밝기 {rows[0]["luma"]} → {rows[-1]["luma"]}')
    cont = continuity(small)
    cv = np.array([r for _, r in cont])
    base = np.median(cv)
    low = [round(i / fps, 2) for (i, r) in cont if r < 0.5 * base]
    print(f'  장면 연속성(0.5초 간격 정합 비율) 중앙값 {base:.3f}, 최소 {cv.min():.3f} '
          f'(t={cont[int(cv.argmin())][0] / fps:.2f}~{(cont[int(cv.argmin())][0] + 12) / fps:.2f}s)')
    print(f'  장면 전환·디졸브 의심 구간 시작(중앙값의 50% 미만): {low or "없음"}')
    with open(os.path.join(out, f'{name}_continuity.csv'), 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['t_start', 't_end', 'inlier_ratio'])
        for i, r in cont:
            w.writerow([round(i / fps, 3), round((i + 12) / fps, 3), round(r, 4)])
    if a.first:
        print('  시작 프레임 vs 시작 이미지:', match(cv2.imread(a.first), frames[0]))
    if a.last:
        print('  끝 프레임 vs 끝 이미지:', match(cv2.imread(a.last), frames[-1]))


if __name__ == '__main__':
    main()
