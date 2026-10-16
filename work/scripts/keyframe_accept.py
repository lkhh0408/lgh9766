"""다시 그린(사실화) 키프레임 합격 검사. 무료(로컬 계산만 함).

기준 키프레임(예: 008c_clean.png)과 후보(예: Gemini 3 Pro Image 4K 재생성본)를 비교해
'타워·구도·빛은 그대로이고, 주변 질감만 더 사진 같아졌는지'를 숫자로 판정한다.

검사 항목 (모든 계산은 기준 해상도에서 함. 후보는 INTER_AREA로 줄여서 비교하고 키우지 않음)
1. 구도(기하): align_to.align으로 지상부 SIFT 닮음변환을 구한다.
   배율·회전·타워 중심 이동·가장자리 채움 폭(정렬 때 화면 밖이 드러나는 폭)을 본다.
2. 배치(놀이기구·건물 위치): 정렬 후 지상 구조물(나무 제외) 윤곽의 광류 이동량 95백분위.
   keyframe_consistency.measure의 '같은 장면' 대응점 비율은 참고만 한다(나무 결을 다시 그리면 크게 낮아짐).
3. 타워 보존: 타워 상자마다(전망대 좌우에 정비용 팔이 생기는지 보려고 약 40px 여유를 둠)
   (a) 바뀐 덩어리: 밝기 평균·대비를 맞춘 뒤 흐린 차이가 30단계를 넘는 화소가 이어진 가장 큰 덩어리 넓이,
   (b) 타워 윤곽 위 광류 이동량 95백분위(전망대 크기·모양이 바뀌면 커짐),
   (c) 저주파 SSIM, (d) 상자 안 SIFT로 구한 국소 배율·이동(대응점이 충분할 때만),
   (e) 윤곽선 평균 거리(챔퍼, 참고용).
   상자 안 나무 색 화소는 빼고 잰다(나무는 바뀌어야 하므로).
4. 빛·시간대: 하늘·타워·지상의 평균 색 차이(Lab ΔE, 밝기 ΔL).
5. 질감(그림 같은 느낌 대용 지표)
   - 테두리 지수: 강한 계단 경계를 법선 방향으로 잘라, 양쪽 평평한 부분보다 더 밝거나 어두운
     넘침(흰 테두리·검은 테두리)의 크기를 경계 대비로 나눈 값의 평균. 낮을수록 좋다.
   - 나무 잔결: 나무 색 화소(강한 윤곽 근처 제외)의 대역통과(DoG 0.7~2.0) 크기 / 주변 밝기. 높을수록 잎 단위 결이 많다.
   - 평평한 칠 비율: 5×5 국소 표준편차/밝기가 8% 미만인 나무 화소 비율. 낮을수록 '붓칠 덩어리'가 적다.
   - 하늘 잡음: 하늘의 대역통과 크기 중앙값. 가짜 입자·압축 잡음을 막는다.
6. 비교 이미지(jpg): 전체, 타워 확대·차이, 숲·놀이기구·도시 확대.

판정
- 보존 항목(1~4, 테두리, 하늘 잡음) 중 하나라도 넘으면 불합격.
- 개선 항목(나무 잔결 1.10배 이상, 평평한 칠 비율이 기준 이하)을 못 채우면 '개선 없음'으로 불합격.
  --no-gain-ok를 주면 개선 항목은 참고만 한다(정비 장비 지우기 같은 보존용 편집 검사).

사용(저장소 루트)
  python3 work/scripts/keyframe_accept.py --candidate 후보.png \
      --reference work/final/s1/keyframes/008c_clean.png --out 비교.jpg \
      [--tower-box x,y,w,h ...] [--write-aligned 정렬본.png --aligned-size 3840x2160] [--json 결과.json]
  타워 상자를 주지 않고 기준이 1672×941이면 008c_clean용 기본 상자(타워 위쪽·타워 아래 건물·오른쪽 가는 탑)를 쓴다.
  문턱값은 1672×941 기준에서 맞췄다. 기준은 008c_clean.png 그대로 쓰는 것을 권한다(4K 기준을 쓰면 테두리 지수의 단면 길이가 맞지 않음).
  영상 첫 프레임 검사(보존·테두리만): --no-gain-ok 를 붙이고 후보에 프레임 png를 준다.
  구도가 다른 프레임의 테두리만 재기: --halo-only (기준 없이 1672×941로 줄여 아래 45%의 테두리 지수를 출력)
    예) python3 work/scripts/keyframe_accept.py --halo-only --candidate 프레임1.png 프레임2.png
종료 코드: 합격 0, 불합격 1.
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from align_to import align  # noqa: E402
from keyframe_consistency import measure as scene_measure  # noqa: E402
from quality_check import hf_ratio, lap_var  # noqa: E402

# 008c_clean.png(1672×941) 기준 타워 상자: 안테나·위 전망대·주 전망대·기둥(좌우 여유 포함) / 타워 아래 건물 / 오른쪽 가는 탑
DEFAULT_BOXES_008C = [(700, 128, 166, 402), (700, 518, 198, 80), (945, 322, 52, 243)]
BOX_NAMES = ['tower', 'base', 'mast']

# 확대 비교 영역(기준 크기에 대한 비율 x, y, w, h). 008c에서 숲·롤러코스터·빨간 놀이기구·도시
ZOOMS = {'forest_L': (0.0, 0.68, 0.251, 0.319), 'coaster': (0.24, 0.68, 0.24, 0.32),
         'ride_hill': (0.53, 0.68, 0.17, 0.212), 'city_R': (0.75, 0.553, 0.25, 0.191)}

# 판정 기준(기준 해상도 화소). 근거는 work/final/plan/환경개선_방법.md 참고
LIM = {
    'align_inliers_min': 60,       # 지상 대응점이 이보다 적으면 다른 장면으로 봄(영상 첫 프레임처럼 다시 그린 경우 160 안팎)
    'scale_dev_max': 0.02,         # 전체 배율 차이
    'rot_deg_max': 0.5,            # 회전
    'center_shift_max': 20.0,      # 타워 중심 이동(px)
    'border_fill_max': 6.0,        # 정렬 때 화면 밖이 드러나는 폭(px). 넘으면 가장자리에 반사 띠가 보임
    'layout_flow_p95_max': 4.0,    # 정렬 후 지상 구조물 이동 95백분위(px)
    'tower_scale_dev_max': 0.015,  # 타워 상자 국소 배율
    'tower_shift_max': 2.0,        # 타워 상자 국소 이동(px)
    'blob_max': 100,               # 타워 상자 안 바뀐 덩어리 최대 넓이(px², 1672 폭 기준. 다른 크기면 넓이 비례)
    'tower_flow_p95_max': 2.0,     # 타워 윤곽 광류 95백분위(px)
    'tower_ssim_min': 0.85,        # 저주파 SSIM(형태)
    'dE_sky_max': 6.0, 'dE_tower_max': 8.0, 'dL_ground_max': 8.0,
    'halo_ratio_max': 1.30,        # 테두리 지수: 기준의 1.3배 또는 기준+0.03 중 큰 값까지 허용
    'halo_abs_slack': 0.03,
    'sky_noise_ratio': 1.8,        # 하늘 잡음: 기준의 1.8배 또는 기준+0.15 단계 중 큰 값까지 허용
    'sky_noise_slack': 0.15,
    'texture_gain_min': 1.10,      # 개선: 나무 잔결 비율
}


def parse_box(s):
    v = [int(round(float(t))) for t in s.split(',')]
    if len(v) != 4:
        raise argparse.ArgumentTypeError('x,y,w,h 형식이어야 함')
    return tuple(v)


def gray_f(img):
    return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)


def box_mask(shape, boxes, pad=0):
    m = np.zeros(shape[:2], np.uint8)
    for x, y, w, h in boxes:
        m[max(0, y - pad):y + h + pad, max(0, x - pad):x + w + pad] = 255
    return m


def foliage_mask(ref, ground_top):
    """기준 이미지에서 나무 색 화소(녹색 쪽 a*, 너무 밝지 않음)를 찾는다. 두 이미지에 같은 마스크를 쓴다."""
    lab = cv2.cvtColor(ref, cv2.COLOR_BGR2LAB).astype(np.int16)
    a = lab[..., 1] - 128
    m = ((a <= -2) & (lab[..., 0] < 170)).astype(np.uint8) * 255
    m[:ground_top] = 0
    m = cv2.morphologyEx(m, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    m = cv2.morphologyEx(m, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return m


def strong_edges(g, lo=80, hi=160):
    gb = cv2.GaussianBlur(g, (0, 0), 1.2)
    return cv2.Canny(np.clip(gb, 0, 255).astype(np.uint8), lo, hi, L2gradient=True)


def halo_index(g, mask, R=5.0, min_c=25.0, max_pts=40000, seed=0):
    """강한 계단 경계에서 넘침(흰·검은 테두리) 크기 / 경계 대비. 경계 법선 방향 단면으로 잰다."""
    gb = cv2.GaussianBlur(g, (0, 0), 1.2)
    e = cv2.Canny(np.clip(gb, 0, 255).astype(np.uint8), 40, 100, L2gradient=True)
    e[mask == 0] = 0
    ys, xs = np.nonzero(e)
    if len(xs) == 0:
        return {'n': 0, 'mean': None, 'p75': None, 'strong_pct': None}
    rng = np.random.default_rng(seed)
    if len(xs) > max_pts:
        sel = rng.choice(len(xs), max_pts, replace=False)
        ys, xs = ys[sel], xs[sel]
    gx = cv2.Sobel(gb, cv2.CV_32F, 1, 0, ksize=3)[ys, xs]
    gy = cv2.Sobel(gb, cv2.CV_32F, 0, 1, ksize=3)[ys, xs]
    nrm = np.hypot(gx, gy) + 1e-6
    nx, ny = gx / nrm, gy / nrm  # 어두운 쪽 → 밝은 쪽
    d = np.arange(-R, R + 1e-3, 0.5, dtype=np.float32)
    mx = (xs[:, None] + d[None, :] * nx[:, None]).astype(np.float32)
    my = (ys[:, None] + d[None, :] * ny[:, None]).astype(np.float32)
    # cv2.remap은 출력 행 수가 32767 미만이어야 하므로 나눠서 표본을 뽑는다
    prof = np.vstack([cv2.remap(g, mx[i:i + 20000], my[i:i + 20000], cv2.INTER_LINEAR,
                                borderMode=cv2.BORDER_REFLECT) for i in range(0, len(mx), 20000)])
    far_lo, far_hi = prof[:, d <= -R + 1.5], prof[:, d >= R - 1.5]
    lo, hi = far_lo.mean(1), far_hi.mean(1)
    c = hi - lo
    ok = (c >= min_c) & (far_lo.std(1) < 0.15 * c) & (far_hi.std(1) < 0.15 * c)
    if ok.sum() < 30:
        return {'n': int(ok.sum()), 'mean': None, 'p75': None, 'strong_pct': None}
    inner_hi = prof[:, (d > 0) & (d < R - 1.5)].max(1)
    inner_lo = prof[:, (d < 0) & (d > -R + 1.5)].min(1)
    h = (np.clip(inner_hi - hi, 0, None) + np.clip(lo - inner_lo, 0, None)) / np.maximum(c, 1e-3)
    h = h[ok]
    return {'n': int(ok.sum()), 'mean': round(float(h.mean()), 4), 'p75': round(float(np.percentile(h, 75)), 4),
            'strong_pct': round(float((h > 0.2).mean() * 100), 2)}


def dog(g, s1=0.7, s2=2.0):
    return np.abs(cv2.GaussianBlur(g, (0, 0), s1) - cv2.GaussianBlur(g, (0, 0), s2))


def texture_stats(g, fol):
    """나무 잔결(%), 평평한 칠 비율(%)."""
    excl = cv2.dilate(strong_edges(g), np.ones((5, 5), np.uint8))
    interior = (cv2.erode(fol, np.ones((3, 3), np.uint8)) > 0) & (excl == 0)
    if interior.sum() < 500:
        return None, None
    loc = cv2.GaussianBlur(g, (0, 0), 6) + 10
    fine = float((dog(g) / loc)[interior].mean() * 100)
    mu = cv2.blur(g, (5, 5))
    sd = np.sqrt(np.maximum(cv2.blur(g * g, (5, 5)) - mu * mu, 0))
    flat = float(((sd / (mu + 10)) < 0.08)[interior].mean() * 100)
    return round(fine, 3), round(flat, 2)


def sky_noise(g, sky):
    v = dog(g)[sky > 0]
    return round(float(np.median(v)), 3) if v.size else None


def lab_mean(img, m):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB).astype(np.float32)
    lab[..., 0] *= 100 / 255
    lab[..., 1:] -= 128
    return lab[m > 0].mean(0)


def ssim_lowpass(a, b, m):
    a = cv2.GaussianBlur(a, (0, 0), 2.0)
    b = cv2.GaussianBlur(b, (0, 0), 2.0)
    C1, C2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_a, mu_b = cv2.GaussianBlur(a, (0, 0), 3), cv2.GaussianBlur(b, (0, 0), 3)
    va = cv2.GaussianBlur(a * a, (0, 0), 3) - mu_a ** 2
    vb = cv2.GaussianBlur(b * b, (0, 0), 3) - mu_b ** 2
    cab = cv2.GaussianBlur(a * b, (0, 0), 3) - mu_a * mu_b
    s = ((2 * mu_a * mu_b + C1) * (2 * cab + C2)) / ((mu_a ** 2 + mu_b ** 2 + C1) * (va + vb + C2))
    return float(s[m > 0].mean())


def chamfer(a, b, m):
    """흐리게 한 두 이미지의 윤곽선 사이 평균 거리. a→b: 기준 윤곽이 후보에서 사라짐, b→a: 후보에 새 윤곽이 생김."""
    def ed(g):
        gb = np.clip(cv2.GaussianBlur(g, (0, 0), 1.5), 0, 255).astype(np.uint8)
        return cv2.Canny(gb, 20, 50, L2gradient=True)
    ea, eb = ed(a), ed(b)
    ea[m == 0] = 0
    eb[m == 0] = 0
    if ea.sum() == 0 or eb.sum() == 0:
        return None
    da = cv2.distanceTransform(255 - ea, cv2.DIST_L2, 3)
    db = cv2.distanceTransform(255 - eb, cv2.DIST_L2, 3)
    ab, ba = db[ea > 0], da[eb > 0]
    return {'ref_to_cand': round(float(ab.mean()), 3), 'cand_to_ref': round(float(ba.mean()), 3),
            'p90': round(float(max(np.percentile(ab, 90), np.percentile(ba, 90))), 3)}


def changed_blob(a, b, m, thr=30.0):
    """상자 안 밝기 평균·대비를 기준에 맞춘 뒤, 흐린 차이가 thr를 넘는 화소의 가장 큰 연결 덩어리 넓이(px²)와 비율(%)."""
    sel = m > 0
    if sel.sum() < 50:
        return None
    b2 = (b - b[sel].mean()) / (b[sel].std() + 1e-6) * a[sel].std() + a[sel].mean()
    d = np.abs(cv2.GaussianBlur(a, (0, 0), 1.5) - cv2.GaussianBlur(b2, (0, 0), 1.5))
    bw = ((d > thr) & sel).astype(np.uint8)
    n, _, st, _ = cv2.connectedComponentsWithStats(bw, connectivity=8)
    big = int(st[1:, cv2.CC_STAT_AREA].max()) if n > 1 else 0
    return {'max_blob': big, 'changed_pct': round(float(bw[sel].mean() * 100), 2)}


def edge_flow_p95(a, b, m):
    """흐린 기준 윤곽 화소에서 기준→후보 광류 크기 95백분위(px). 모양·크기가 바뀐 곳에서 커진다."""
    A = np.clip(cv2.GaussianBlur(a, (0, 0), 1.5), 0, 255).astype(np.uint8)
    B = np.clip(cv2.GaussianBlur(b, (0, 0), 1.5), 0, 255).astype(np.uint8)
    fl = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(A, B, None)
    sel = (m > 0) & (cv2.Canny(A, 20, 50) > 0)
    if sel.sum() < 20:
        return None
    return round(float(np.percentile(np.hypot(fl[..., 0], fl[..., 1])[sel], 95)), 2)


def local_transform(ref, cand, box, pad=12):
    x, y, w, h = box
    m = box_mask(ref.shape, [box], pad)
    clahe = cv2.createCLAHE(3.0, (8, 8))
    sift = cv2.SIFT_create(3000)
    ka, da = sift.detectAndCompute(clahe.apply(cv2.cvtColor(ref, cv2.COLOR_BGR2GRAY)), m)
    kb, db = sift.detectAndCompute(clahe.apply(cv2.cvtColor(cand, cv2.COLOR_BGR2GRAY)), m)
    if da is None or db is None or len(ka) < 8 or len(kb) < 8:
        return None
    good = [p[0] for p in cv2.BFMatcher().knnMatch(da, db, k=2) if len(p) == 2 and p[0].distance < 0.75 * p[1].distance]
    if len(good) < 8:
        return None
    pa = np.float32([ka[g.queryIdx].pt for g in good])
    pb = np.float32([kb[g.trainIdx].pt for g in good])
    M, inl = cv2.estimateAffinePartial2D(pa, pb, ransacReprojThreshold=2.0)
    if M is None or inl.sum() < 6:
        return None
    c = np.array([x + w / 2, y + h / 2, 1.0])
    shift = M @ c - c[:2]
    return {'n': int(inl.sum()), 'scale': round(float(np.hypot(M[0, 0], M[1, 0])), 4),
            'shift': round(float(np.hypot(*shift)), 2)}


def layout_flow(ref, cand_al, m):
    a = np.clip(cv2.GaussianBlur(gray_f(ref), (0, 0), 2.0), 0, 255).astype(np.uint8)
    b = np.clip(cv2.GaussianBlur(gray_f(cand_al), (0, 0), 2.0), 0, 255).astype(np.uint8)
    fl = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM).calc(a, b, None)
    mag = np.hypot(fl[..., 0], fl[..., 1])[m > 0]
    return round(float(np.median(mag)), 2), round(float(np.percentile(mag, 95)), 2)


def border_fill(M, w, h):
    """출력 화면 네 모서리를 후보 좌표로 되돌렸을 때 후보 화면 밖으로 나가는 최대 폭(px)."""
    Mi = cv2.invertAffineTransform(M)
    worst = 0.0
    for x, y in [(0, 0), (w, 0), (0, h), (w, h)]:
        sx, sy = Mi @ np.array([x, y, 1.0])
        worst = max(worst, -sx, sx - w, -sy, sy - h)
    return round(float(max(worst, 0.0)), 2)


def aligned_highres(cand, M, ref_size, out_size):
    """후보 원본 해상도의 결을 살려 out_size로 정렬한다(M은 기준 크기에서 구한 닮음변환)."""
    wr, hr = ref_size
    wo, ho = out_size
    interp = cv2.INTER_AREA if cand.shape[1] >= wo else cv2.INTER_LANCZOS4
    mid = cv2.resize(cand, (wo, ho), interpolation=interp)
    S = np.diag([wo / wr, ho / hr, 1.0])
    M3 = np.vstack([M, [0, 0, 1]])
    A = (S @ M3 @ np.linalg.inv(S))[:2]
    return cv2.warpAffine(mid, A, (wo, ho), flags=cv2.INTER_LANCZOS4, borderMode=cv2.BORDER_REFLECT)


def label(img, text, scale=0.7):
    cv2.rectangle(img, (0, 0), (int(len(text) * 13 * scale / 0.7) + 12, int(30 * scale / 0.7)), (0, 0, 0), -1)
    cv2.putText(img, text, (6, int(22 * scale / 0.7)), cv2.FONT_HERSHEY_SIMPLEX, scale, (0, 255, 255), 2)
    return img


def make_sheet(ref, cand_hr, cand_al, boxes, verdict_lines, path):
    H, W = ref.shape[:2]
    hr_s = cand_hr.shape[1] / W
    top = np.hstack([label(cv2.resize(ref, (960, 540), interpolation=cv2.INTER_AREA), 'reference'),
                     label(cv2.resize(cand_al, (960, 540), interpolation=cv2.INTER_AREA), 'candidate (aligned)')])
    # 타워 확대(모든 상자를 감싸는 영역) + 저주파 차이
    xs = [b[0] for b in boxes] + [b[0] + b[2] for b in boxes]
    ys = [b[1] for b in boxes] + [b[1] + b[3] for b in boxes]
    x0, x1, y0, y1 = max(0, min(xs) - 10), min(W, max(xs) + 10), max(0, min(ys) - 10), min(H, max(ys) + 10)
    th = 640
    tw = int(round((x1 - x0) * th / (y1 - y0)))
    rt = cv2.resize(ref[y0:y1, x0:x1], (tw, th), interpolation=cv2.INTER_CUBIC)
    ct = cv2.resize(cand_hr[int(y0 * hr_s):int(y1 * hr_s), int(x0 * hr_s):int(x1 * hr_s)], (tw, th),
                    interpolation=cv2.INTER_AREA)
    d = np.abs(cv2.GaussianBlur(gray_f(ref), (0, 0), 1.5) - cv2.GaussianBlur(gray_f(cand_al), (0, 0), 1.5))
    dm = cv2.applyColorMap(np.clip(d[y0:y1, x0:x1] * 4, 0, 255).astype(np.uint8), cv2.COLORMAP_INFERNO)
    dm = cv2.resize(dm, (tw, th), interpolation=cv2.INTER_NEAREST)
    for (bx, by, bw, bh) in boxes:
        p0 = (int((bx - x0) * tw / (x1 - x0)), int((by - y0) * th / (y1 - y0)))
        p1 = (int((bx + bw - x0) * tw / (x1 - x0)), int((by + bh - y0) * th / (y1 - y0)))
        cv2.rectangle(dm, p0, p1, (0, 255, 0), 1)
    mid = np.hstack([label(rt, 'ref tower'), label(ct, 'cand tower'), label(dm, 'diff x4')])
    free = 1920 - mid.shape[1]
    if free >= 400:
        # 남는 칸에 판정과 주요 숫자를 쓴다(줄이 길면 접음)
        panel = np.full((th, free, 3), 20, np.uint8)
        wrapped = []
        n = max(20, int(free / 9.5))
        for line in verdict_lines:
            # ' | ' 단위로 먼저 나누고, 그래도 길면 글자 수로 자른다
            for k, piece in enumerate(line.split(' | ')):
                piece = piece if k == 0 else '  ' + piece
                wrapped += [piece[i:i + n] for i in range(0, len(piece), n)] or ['']
        for i, line in enumerate(wrapped[:th // 24]):
            col = (80, 80, 255) if 'FAIL' in line else (120, 230, 120) if 'PASS' in line else (230, 230, 230)
            cv2.putText(panel, line, (10, 26 + 24 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.52, col, 1, cv2.LINE_AA)
        mid = np.hstack([mid, panel])
        verdict_lines = []
    else:
        mid = cv2.copyMakeBorder(mid, 0, 0, 0, max(0, free), cv2.BORDER_CONSTANT, value=(30, 30, 30))[:, :1920]
    # 숲·놀이기구·도시 확대: 영역마다 기준|후보, 한 줄에 두 영역
    tiles = []
    for name, (fx, fy, fw, fh) in ZOOMS.items():
        x, y, w, h = int(fx * W), int(fy * H), int(fw * W), int(fh * H)
        tw2, th2 = 480, int(round(480 * h / w))
        a = cv2.resize(ref[y:y + h, x:x + w], (tw2, th2), interpolation=cv2.INTER_CUBIC)
        b = cv2.resize(cand_hr[int(y * hr_s):int((y + h) * hr_s), int(x * hr_s):int((x + w) * hr_s)], (tw2, th2),
                       interpolation=cv2.INTER_AREA)
        tiles.append(np.hstack([label(a, f'ref {name}', 0.6), label(b, f'cand {name}', 0.6)]))
    rows = []
    for i in range(0, len(tiles), 2):
        pair = tiles[i:i + 2]
        hh = max(t.shape[0] for t in pair)
        pair = [cv2.copyMakeBorder(t, 0, hh - t.shape[0], 0, 0, cv2.BORDER_CONSTANT, value=(30, 30, 30)) for t in pair]
        row = np.hstack(pair)
        rows.append(cv2.copyMakeBorder(row, 0, 0, 0, 1920 - row.shape[1], cv2.BORDER_CONSTANT, value=(30, 30, 30)))
    parts = [top, mid] + rows
    if verdict_lines:
        txt = np.full((26 * len(verdict_lines) + 16, 1920, 3), 20, np.uint8)
        for i, line in enumerate(verdict_lines):
            col = (80, 80, 255) if 'FAIL' in line else (120, 230, 120) if 'PASS' in line else (230, 230, 230)
            cv2.putText(txt, line, (10, 28 + 26 * i), cv2.FONT_HERSHEY_SIMPLEX, 0.62, col, 1, cv2.LINE_AA)
        parts.append(txt)
    sheet = np.vstack(parts)
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    cv2.imwrite(path, sheet, [cv2.IMWRITE_JPEG_QUALITY, 88])


def evaluate(ref, cand, boxes, need_gain=True):
    H, W = ref.shape[:2]
    cand_r = cv2.resize(cand, (W, H), interpolation=cv2.INTER_AREA if cand.shape[1] >= W else cv2.INTER_CUBIC)
    cand_al, M, inl = align(cand, ref)  # align_to와 같은 방식(지상 SIFT 닮음변환)
    s = float(np.hypot(M[0, 0], M[1, 0]))
    rot = float(np.degrees(np.arctan2(M[1, 0], M[0, 0])))
    tb = boxes[0]
    c = np.array([tb[0] + tb[2] / 2, tb[1] + tb[3] / 2, 1.0])
    center_shift = float(np.hypot(*(cv2.invertAffineTransform(M) @ c - c[:2])))
    r = {'geometry': {'inliers': inl, 'scale': round(s, 4), 'rot_deg': round(rot, 3),
                      'tower_center_shift_px': round(center_shift, 2), 'border_fill_px': border_fill(M, W, H)}}

    ground_top = int(H * 0.55)
    fol = foliage_mask(ref, ground_top)
    tower_m = box_mask(ref.shape, boxes)
    fol_d = cv2.dilate(fol, np.ones((7, 7), np.uint8))

    sc = scene_measure(ref, cand_r)
    g_ref, g_al = gray_f(ref), gray_f(cand_al)
    struct = np.zeros((H, W), np.uint8)
    struct[ground_top:] = 255
    struct[(fol_d > 0) | (tower_m > 0)] = 0
    struct = cv2.bitwise_and(struct, cv2.dilate(strong_edges(g_ref, 30, 80), np.ones((5, 5), np.uint8)))
    fmed, fp95 = layout_flow(ref, cand_al, struct) if struct.sum() else (None, None)
    r['layout'] = {'scene_matches': sc['matches'], 'scene_inliers': sc['F_inliers'],
                   'scene_ratio': round(sc['inlier_ratio'], 3), 'tower_scale_kc': sc['tower_scale'],
                   'struct_flow_median': fmed, 'struct_flow_p95': fp95}

    tw = []
    for i, b in enumerate(boxes):
        m = box_mask(ref.shape, [b])
        m[fol_d > 0] = 0
        tw.append({'box': list(b), 'name': BOX_NAMES[i] if i < len(BOX_NAMES) and len(boxes) == 3 else f'box{i}',
                   'blob': changed_blob(g_ref, g_al, m), 'edge_flow_p95': edge_flow_p95(g_ref, g_al, m),
                   'ssim_lowpass': round(ssim_lowpass(g_ref, g_al, m), 4),
                   'local': local_transform(ref, cand_al, b), 'chamfer': chamfer(g_ref, g_al, m)})
    r['tower'] = tw

    sky = np.zeros((H, W), np.uint8)
    sky[:int(H * 0.40)] = 255
    sky[box_mask(ref.shape, boxes, pad=15) > 0] = 0
    ground = np.zeros((H, W), np.uint8)
    ground[ground_top:] = 255
    ground[tower_m > 0] = 0
    tower_nf = tower_m.copy()
    tower_nf[fol_d > 0] = 0
    lr, lc = lab_mean(ref, sky), lab_mean(cand_r, sky)
    tr, tc = lab_mean(ref, tower_nf), lab_mean(cand_r, tower_nf)
    gr, gc = lab_mean(ref, ground), lab_mean(cand_r, ground)
    r['color'] = {'dE_sky': round(float(np.linalg.norm(lr - lc)), 2), 'dE_tower': round(float(np.linalg.norm(tr - tc)), 2),
                  'dL_ground': round(float(abs(gr[0] - gc[0])), 2)}

    # 질감: 후보는 정렬하지 않은 축소본으로 잰다(보간이 결을 지우거나 테두리를 만들지 않게). 마스크만 옮긴다.
    Mi = cv2.invertAffineTransform(M)

    def to_cand(m):
        return cv2.warpAffine(m, Mi, (W, H), flags=cv2.INTER_NEAREST)
    g_c = gray_f(cand_r)
    tex = {}
    for nm, img, gm, fm, sm, tm in [('ref', ref, g_ref, fol, sky, tower_m),
                                    ('cand', cand_r, g_c, to_cand(fol), to_cand(sky), to_cand(tower_m))]:
        gmask = to_cand(ground) if nm == 'cand' else ground
        fine, flat = texture_stats(gm, fm)
        tex[nm] = {'halo_ground': halo_index(gm, gmask), 'halo_tower': halo_index(gm, tm),
                   'foliage_fine': fine, 'foliage_flat_pct': flat, 'sky_noise': sky_noise(gm, sm),
                   'lap_var': round(lap_var(img), 1), 'hf_pct': round(hf_ratio(img), 2)}
    r['texture'] = tex
    fr, fc = tex['ref']['foliage_fine'], tex['cand']['foliage_fine']
    r['texture']['foliage_gain'] = round(fc / fr, 3) if fr and fc else None

    # 판정
    L = LIM
    checks = []

    def chk(name, ok, val, lim, kind='keep'):
        checks.append({'name': name, 'ok': bool(ok), 'value': val, 'limit': lim, 'kind': kind})
    gmt = r['geometry']
    chk('align_inliers', gmt['inliers'] >= L['align_inliers_min'], gmt['inliers'], f">={L['align_inliers_min']}")
    chk('scale', abs(gmt['scale'] - 1) <= L['scale_dev_max'], gmt['scale'], f"1±{L['scale_dev_max']}")
    chk('rotation_deg', abs(gmt['rot_deg']) <= L['rot_deg_max'], gmt['rot_deg'], f"<={L['rot_deg_max']}")
    chk('tower_center_shift', gmt['tower_center_shift_px'] <= L['center_shift_max'], gmt['tower_center_shift_px'],
        f"<={L['center_shift_max']}")
    chk('border_fill', gmt['border_fill_px'] <= L['border_fill_max'], gmt['border_fill_px'], f"<={L['border_fill_max']}")
    lay = r['layout']
    # 같은 장면 대응점 비율은 나무 결을 다시 그리면 크게 낮아지므로(영상 첫 프레임 0.05) 참고만 한다
    chk('scene_ratio', True, lay['scene_ratio'], 'info', 'info')
    chk('layout_flow_p95', fp95 is not None and fp95 <= L['layout_flow_p95_max'], fp95, f"<={L['layout_flow_p95_max']}")
    blob_lim = int(round(L['blob_max'] * (W / 1672) ** 2))
    flow_lim = round(L['tower_flow_p95_max'] * W / 1672, 2)
    for t in tw:
        lt, bl, ef = t['local'], t['blob'], t['edge_flow_p95']
        chk(f"{t['name']}_changed_blob", bl is not None and bl['max_blob'] <= blob_lim,
            bl['max_blob'] if bl else None, f'<={blob_lim}')
        chk(f"{t['name']}_edge_flow_p95", ef is not None and ef <= flow_lim, ef, f'<={flow_lim}')
        chk(f"{t['name']}_ssim_lowpass", t['ssim_lowpass'] >= L['tower_ssim_min'], t['ssim_lowpass'],
            f">={L['tower_ssim_min']}")
        if lt is not None:
            chk(f"{t['name']}_local_scale", abs(lt['scale'] - 1) <= L['tower_scale_dev_max'], lt['scale'],
                f"1±{L['tower_scale_dev_max']}")
            chk(f"{t['name']}_local_shift", lt['shift'] <= L['tower_shift_max'], lt['shift'], f"<={L['tower_shift_max']}")
        if t['chamfer'] is not None:
            chk(f"{t['name']}_chamfer", True, max(t['chamfer']['ref_to_cand'], t['chamfer']['cand_to_ref']),
                'info', 'info')
    col = r['color']
    chk('dE_sky', col['dE_sky'] <= L['dE_sky_max'], col['dE_sky'], f"<={L['dE_sky_max']}")
    chk('dE_tower', col['dE_tower'] <= L['dE_tower_max'], col['dE_tower'], f"<={L['dE_tower_max']}")
    chk('dL_ground', col['dL_ground'] <= L['dL_ground_max'], col['dL_ground'], f"<={L['dL_ground_max']}")
    for key in ['halo_ground', 'halo_tower']:
        hr_, hc_ = tex['ref'][key]['mean'], tex['cand'][key]['mean']
        if hr_ is None or hc_ is None:
            chk(key, True, hc_, 'not measurable', 'info')
            continue
        lim = max(hr_ * L['halo_ratio_max'], hr_ + L['halo_abs_slack'])
        chk(key, hc_ <= lim, hc_, f'<={lim:.3f} (ref {hr_})')
    sr, sc_ = tex['ref']['sky_noise'], tex['cand']['sky_noise']
    sky_lim = max(sr * L['sky_noise_ratio'], sr + L['sky_noise_slack'])
    chk('sky_noise', sc_ is not None and sc_ <= sky_lim, sc_, f'<={sky_lim:.3f}')
    gain = r['texture']['foliage_gain']
    chk('foliage_gain', gain is not None and gain >= L['texture_gain_min'], gain, f">={L['texture_gain_min']}", 'gain')
    flr, flc = tex['ref']['foliage_flat_pct'], tex['cand']['foliage_flat_pct']
    chk('foliage_flat_pct', flc is not None and flr is not None and flc <= flr, flc, f'<={flr}', 'gain')

    keep_ok = all(c['ok'] for c in checks if c['kind'] == 'keep')
    gain_ok = all(c['ok'] for c in checks if c['kind'] == 'gain')
    r['checks'] = checks
    r['keep_ok'], r['gain_ok'] = keep_ok, gain_ok
    r['pass'] = keep_ok and (gain_ok or not need_gain)
    return r, cand_al, M


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--candidate', required=True, nargs='+', help='후보 이미지(--halo-only일 때는 여러 장 가능)')
    ap.add_argument('--reference')
    ap.add_argument('--halo-only', action='store_true', help='기준 없이 테두리 지수만 출력')
    ap.add_argument('--tower-box', type=parse_box, action='append',
                    help='x,y,w,h (기준 이미지 화소). 여러 번 줄 수 있음. 첫 상자를 타워 중심 기준으로 씀')
    ap.add_argument('--out', help='비교 이미지(jpg). 기본: 후보 이름_accept.jpg')
    ap.add_argument('--json', help='측정값 저장(json)')
    ap.add_argument('--write-aligned', help='기준 구도에 맞춘 고해상도 정렬본 저장 경로(png)')
    ap.add_argument('--aligned-size', default='3840x2160')
    ap.add_argument('--no-gain-ok', action='store_true', help='개선 항목을 참고만 함(보존 검사만)')
    a = ap.parse_args()

    if a.halo_only:
        # 1672×941로 줄여(키프레임 검사와 같은 크기) 아래 45%(지상)의 테두리 지수
        for p in a.candidate:
            im = cv2.imread(p)
            if im is None:
                sys.exit(f'이미지를 읽지 못함: {p}')
            g = gray_f(cv2.resize(im, (1672, 941), interpolation=cv2.INTER_AREA))
            m = np.zeros(g.shape, np.uint8)
            m[int(941 * 0.55):] = 255
            h = halo_index(g, m)
            print(f"{p}: 테두리 지수(지상) {h['mean']} (강한 테두리 {h['strong_pct']}%, 경계 {h['n']}개)")
        return
    if not a.reference or len(a.candidate) != 1:
        sys.exit('--reference 하나와 --candidate 하나가 필요함')
    a.candidate = a.candidate[0]
    ref = cv2.imread(a.reference)
    cand = cv2.imread(a.candidate)
    if ref is None or cand is None:
        sys.exit('이미지를 읽지 못함')
    boxes = a.tower_box
    if not boxes:
        if (ref.shape[1], ref.shape[0]) != (1672, 941):
            sys.exit('기준이 1672×941이 아니면 --tower-box를 지정해야 함')
        boxes = DEFAULT_BOXES_008C
    r, cand_al, M = evaluate(ref, cand, boxes, need_gain=not a.no_gain_ok)
    wo, ho = [int(v) for v in a.aligned_size.lower().split('x')]
    cand_hr = aligned_highres(cand, M, (ref.shape[1], ref.shape[0]), (wo, ho))
    if a.write_aligned:
        os.makedirs(os.path.dirname(os.path.abspath(a.write_aligned)), exist_ok=True)
        cv2.imwrite(a.write_aligned, cand_hr)

    # 출력
    print(f'후보 {a.candidate} ({cand.shape[1]}x{cand.shape[0]})  기준 {a.reference} ({ref.shape[1]}x{ref.shape[0]})')
    g = r['geometry']
    print(f"구도: 대응점 {g['inliers']}, 배율 {g['scale']}, 회전 {g['rot_deg']}°, 타워 중심 이동 {g['tower_center_shift_px']}px, "
          f"가장자리 채움 {g['border_fill_px']}px")
    lay = r['layout']
    print(f"배치: 같은 장면 비율 {lay['scene_ratio']} (대응 {lay['scene_matches']}, 일치 {lay['scene_inliers']}), "
          f"지상 구조물 이동 중앙 {lay['struct_flow_median']} / 95% {lay['struct_flow_p95']}px")
    for t in r['tower']:
        print(f"타워[{t['name']}]: 바뀐 덩어리 {t['blob']}, 윤곽 광류 95% {t['edge_flow_p95']}px, 저주파 SSIM {t['ssim_lowpass']}, "
              f"국소변환 {t['local']}, 윤곽거리 {t['chamfer']}")
    print(f"빛: 하늘 ΔE {r['color']['dE_sky']}, 타워 ΔE {r['color']['dE_tower']}, 지상 ΔL {r['color']['dL_ground']}")
    for k in ['ref', 'cand']:
        t = r['texture'][k]
        print(f"질감[{k}]: 테두리(지상) {t['halo_ground']['mean']} (강한 테두리 {t['halo_ground']['strong_pct']}%, n={t['halo_ground']['n']}), "
              f"테두리(타워) {t['halo_tower']['mean']}, 나무 잔결 {t['foliage_fine']}, 평평한 칠 {t['foliage_flat_pct']}%, "
              f"하늘 잡음 {t['sky_noise']}, 선명도 {t['lap_var']}, 고주파 {t['hf_pct']}%")
    print(f"나무 잔결 비율(후보/기준): {r['texture']['foliage_gain']}")
    lines = []
    for c in r['checks']:
        if c['kind'] == 'info':
            tag = 'INFO'
        elif c['ok']:
            tag = 'PASS'
        else:
            tag = 'NOTE' if (c['kind'] == 'gain' and a.no_gain_ok) else 'FAIL'
        lines.append(f"[{tag}] {c['kind']:4s} {c['name']}: {c['value']} (limit {c['limit']})")
    fails = [c['name'] for c in r['checks'] if not c['ok'] and c['kind'] == 'keep']
    gfails = [c['name'] for c in r['checks'] if not c['ok'] and c['kind'] == 'gain']
    if r['pass']:
        verdict = 'PASS'
        ko = '합격'
    elif not r['keep_ok']:
        verdict = 'FAIL (preservation): ' + ', '.join(fails)
        ko = '불합격(보존 위반): ' + ', '.join(fails)
    else:
        verdict = 'FAIL (no texture gain): ' + ', '.join(gfails)
        ko = '불합격(질감 개선 없음): ' + ', '.join(gfails)
    for ln in lines:
        print('  ' + ln)
    print('판정:', ko)
    out = a.out or os.path.splitext(a.candidate)[0] + '_accept.jpg'
    tx = r['texture']
    sheet_lines = [f'VERDICT: {verdict}'] + [ln for ln in lines if ln.startswith(('[FAIL]', '[NOTE]'))][:8] + [
        f"geometry: inliers {g['inliers']} scale {g['scale']} rot {g['rot_deg']} deg border {g['border_fill_px']}px | "
        f"layout flow p95 {lay['struct_flow_p95']}px | color dE sky {r['color']['dE_sky']} tower {r['color']['dE_tower']}",
        'tower: ' + ' | '.join(f"{t['name']} blob {t['blob']['max_blob'] if t['blob'] else None} "
                               f"flow95 {t['edge_flow_p95']} ssim {t['ssim_lowpass']}" for t in r['tower']),
        f"halo(ground) ref {tx['ref']['halo_ground']['mean']} cand {tx['cand']['halo_ground']['mean']} | "
        f"foliage fine ref {tx['ref']['foliage_fine']} cand {tx['cand']['foliage_fine']} (gain {tx['foliage_gain']}) | "
        f"flat% ref {tx['ref']['foliage_flat_pct']} cand {tx['cand']['foliage_flat_pct']} | "
        f"sky noise ref {tx['ref']['sky_noise']} cand {tx['cand']['sky_noise']}"]
    make_sheet(ref, cand_hr, cand_al, boxes, sheet_lines, out)
    print('비교 이미지:', out)
    if a.json:
        with open(a.json, 'w', encoding='utf-8') as f:
            json.dump({'candidate': a.candidate, 'reference': a.reference, 'verdict': verdict, **r}, f,
                      ensure_ascii=False, indent=1, default=float)
    sys.exit(0 if r['pass'] else 1)


if __name__ == '__main__':
    main()
