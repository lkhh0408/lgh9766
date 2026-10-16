"""완성 영상의 이음새 검사: 속도·방향이 그대로 이어지는지, 멈칫·튐·팝·장면 끊김이 없는지. 무료(로컬 계산만 함).

이음새 시각 = 새 조각의 첫 프레임(그 앞 프레임과의 사이가 이음새). finish.py가 만든 <영상>.edit.json이
영상 옆에 있으면 이음새를 거기서 읽는다. 원본 4K나 묶음 안 연장 이음새(8초 등)에도 그대로 쓸 수 있다.

재는 것(앞뒤 각 1초, 640×360 회색조, clip_check.py와 같은 DIS 광류)
- 속도: 프레임 간 이동량 중앙값(화면 폭 %/프레임). 이음새 앞 1초 평균 대비 뒤 1초 평균의 비율.
- 방향: clip_check.global_motion의 화면 이동(x, y)과 확대율(가장자리 기준 %)을 묶은 벡터의 앞뒤 각도 차.
- 이음새 한 쌍: 바로 그 두 프레임 사이 이동량이 주변(앞뒤 0.25초)보다 확 작으면 '멈칫'(같은 그림 반복),
  확 크면 '튐'(프레임 건너뜀·되돌아감).
- 멈췄다 가기: 앞뒤 2초 안에서 0.5초 평균 속도가 전체 중앙값의 50% 아래로 떨어지는 곳.
- 팝: 광류로 움직임을 맞춘 뒤 남는 차이(pop_detect.py와 같은 계산)가 주변 중앙값의 2배 이상이고 0.8 넘게 큼.
- 장면 끊김: clip_check.continuity(ORB 호모그래피 정합 비율)가 이음새 쌍에서 주변의 50% 아래.
- 밝기: 이음새 앞뒤 프레임 평균 밝기 차(0~255, 계획 기준 2 이하).

판정(장면계획.md 12장 기준, 문턱값은 옵션으로 바꿀 수 있음)
- 불합격: 장면 끊김, 속도 비율 0.7~1.4 밖, 방향 차 45° 초과, 이음새 멈칫·튐, 멈췄다 가기
- 확인 필요: 팝 비율 2.0 이상, 밝기 차 2 초과 (4배 느린 영상과 시트를 눈으로 본다)
- 합격: 그 밖

사용(저장소 루트)
  python3 work/scripts/seam_check.py 영상.mp4                       # 옆의 영상.edit.json에서 이음새를 읽음
  python3 work/scripts/seam_check.py 영상.mp4 --seams 16 f767 31.5  # 초 또는 프레임 번호(f767 = 767번째, 0부터)
  선택: --edit 다른.edit.json --out 결과폴더 --window 1.0 --ratio-lo 0.7 --ratio-hi 1.4 --angle 45 --pop 2.0
결과(--out, 기본은 영상 옆 <이름>_seamcheck/)
  <이름>_seams.csv(이음새별 요약), <이름>_seam_pairs.csv(프레임 쌍별 수치), <이름>_seams.jpg(이음새 주변 프레임 시트)
종료 코드: 불합격 이음새가 없으면 0, 있으면 1.
"""
import argparse
import csv
import json
import os
import re
import sys

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clip_check import H, W, continuity, global_motion  # noqa: E402

OFFSETS = [-24, -12, -4, -2, -1, 0, 1, 2, 4, 12, 24]  # 시트에 넣을 프레임(이음새 첫 프레임 기준)
TW, TH = 256, 144


def font(size):
    for p in ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',):
        if os.path.exists(p):
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def parse_seam(spec, fps):
    s = spec.strip()
    m = re.fullmatch(r'[fF](\d+)|(\d+)[fF]', s)
    return int(m.group(1) or m.group(2)) if m else int(round(float(s) * fps))


def read_window_frames(path, need, full_need):
    """필요한 프레임만 남기며 처음부터 차례로 디코드(정확한 프레임 번호). 작은 회색조·썸네일·원본 크기."""
    cap = cv2.VideoCapture(path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    small, thumb, full = {}, {}, {}
    i, last = 0, max(need)
    while i <= last:
        ok, f = cap.read()
        if not ok:
            break
        if i in need:
            small[i] = cv2.cvtColor(cv2.resize(f, (W, H), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
            thumb[i] = cv2.resize(f, (TW, TH), interpolation=cv2.INTER_AREA)
        if i in full_need:
            full[i] = f
        i += 1
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    return small, thumb, full, fps, total


def pair_metrics(a, b, dis, gx, gy):
    """한 프레임 쌍: 속도(clip_check와 같음), 전역 이동, 움직임 보정 잔차(pop_detect와 같음)와 잔차 지도."""
    fl = dis.calc(a, b, None)
    mag = np.hypot(fl[..., 0], fl[..., 1]) / W * 100
    tx, ty, s, r = global_motion(fl)
    wb = cv2.remap(b, gx + fl[..., 0], gy + fl[..., 1], cv2.INTER_LINEAR)
    d = np.abs(a.astype(np.float32) - wb.astype(np.float32))[8:-8, 8:-8]
    return dict(speed=float(np.median(mag)), tx=tx, ty=ty, zoom=(s - 1) * 50, rot=r,
                resid=float(d.mean()), luma_a=float(a.mean()), luma_b=float(b.mean())), d


def angle(u, v):
    nu, nv = np.linalg.norm(u), np.linalg.norm(v)
    if nu < 1e-9 or nv < 1e-9:
        return None
    return float(np.degrees(np.arccos(np.clip(np.dot(u, v) / (nu * nv), -1, 1))))


def check_seam(s, small, n, a, dis, gx, gy):
    """이음새 s(새 조각 첫 프레임) 하나를 잰다."""
    rows, rmaps = {}, {}
    for i in range(s - n - 1, s + n):
        if i in small and i + 1 in small:
            rows[i], rmaps[i] = pair_metrics(small[i], small[i + 1], dis, gx, gy)
    seam_i = s - 1
    if seam_i not in rows:
        return None, rows
    before = [rows[i] for i in range(s - 1 - n, s - 1) if i in rows]
    after = [rows[i] for i in range(s, s + n) if i in rows]
    near = [rows[i] for i in list(range(s - 7, s - 1)) + list(range(s, s + 6)) if i in rows]
    seam = rows[seam_i]
    v_b = float(np.mean([r['speed'] for r in before])) if before else float('nan')
    v_a = float(np.mean([r['speed'] for r in after])) if after else float('nan')
    ratio = v_a / v_b if v_b > 1e-6 else float('inf')
    near_b = [rows[i]['speed'] for i in range(s - 7, s - 1) if i in rows]
    near_a = [rows[i]['speed'] for i in range(s, s + 6) if i in rows]
    ratio_near = (np.mean(near_a) / np.mean(near_b)) if near_b and near_a and np.mean(near_b) > 1e-6 else float('nan')
    med_near = float(np.median([r['speed'] for r in near])) if near else float('nan')
    q_seam = seam['speed'] / med_near if med_near > 1e-6 else float('nan')

    vec = lambda rs: np.array([np.mean([r['tx'] for r in rs]), np.mean([r['ty'] for r in rs]),
                               np.mean([r['zoom'] for r in rs])])  # noqa: E731
    vb, va = vec(before), vec(after)
    ang = angle(vb, va) if min(np.linalg.norm(vb), np.linalg.norm(va)) > 0.01 else None
    ang_seam = angle(np.array([seam['tx'], seam['ty'], seam['zoom']]), (vb + va) / 2) \
        if np.linalg.norm([seam['tx'], seam['ty'], seam['zoom']]) > 0.01 else None

    # 멈췄다 가기: 0.5초(12쌍) 이동 평균의 최솟값 / 창 전체 중앙값
    seq = [rows[i]['speed'] for i in sorted(rows)]
    win = min(12, len(seq))
    roll = np.convolve(seq, np.ones(win) / win, mode='valid')
    med_all = float(np.median(seq))
    stop_go = float(roll.min() / med_all) if med_all > 1e-6 else float('nan')
    stop_at = sorted(rows)[int(roll.argmin())] + win / 2 if len(roll) else None

    # 팝: 잔차 비율(이음새 쌍 / 주변 중앙값, pop_detect와 같은 기준)
    res_others = [rows[i]['resid'] for i in rows if i != seam_i]
    res_med = float(np.median(res_others))
    pop_ratio = seam['resid'] / res_med if res_med > 1e-6 else float('nan')
    pop = pop_ratio >= a.pop and seam['resid'] - res_med > 0.8
    other_pops = [i + 1 for i in rows if i != seam_i and rows[i]['resid'] >= a.pop * res_med and rows[i]['resid'] - res_med > 0.8]

    # 장면 끊김: 이음새 앞뒤 6프레임의 연속 쌍 ORB 정합 비율
    ids = [i for i in range(s - 6, s + 6) if i in small]
    cont = continuity([small[i] for i in ids], step=1, gap=1)
    cmap = {ids[k]: r for k, r in cont}
    c_seam = cmap.get(seam_i, float('nan'))
    c_med = float(np.median([r for i, r in cmap.items() if i != seam_i])) if len(cmap) > 1 else float('nan')
    cut = bool(c_med > 0 and c_seam < 0.5 * c_med)

    luma_step = abs(seam['luma_b'] - seam['luma_a'])

    fails, warns = [], []
    if cut:
        fails.append(f'장면 끊김 의심(정합 {c_seam:.3f} / 주변 {c_med:.3f})')
    if v_b < 0.01 and v_a < 0.01:
        fails.append('앞뒤 모두 거의 정지')
    elif not (a.ratio_lo <= ratio <= a.ratio_hi):
        fails.append(f'속도 비율 {ratio:.2f} ({a.ratio_lo}~{a.ratio_hi} 밖)')
    if ang is not None and ang > a.angle:
        fails.append(f'방향 차 {ang:.0f}°')
    if q_seam < 0.5:
        fails.append(f'이음새 멈칫(이음새 쌍 속도가 주변의 {q_seam:.2f}배)')
    elif q_seam > 2.0:
        fails.append(f'이음새 튐(이음새 쌍 속도가 주변의 {q_seam:.2f}배)')
    if ang_seam is not None and ang_seam > 90:
        fails.append(f'이음새 쌍 움직임이 반대 방향({ang_seam:.0f}°)')
    if stop_go < 0.5:
        fails.append(f'멈췄다 가기(0.5초 평균이 중앙값의 {stop_go:.2f}배, 약 {stop_at / 24:.2f}초)')
    if pop:
        warns.append(f'팝 비율 {pop_ratio:.2f}')
    if luma_step > 2:
        warns.append(f'밝기 차 {luma_step:.1f}')
    verdict = '불합격' if fails else ('확인 필요' if warns else '합격')

    # 시트용: 잔차가 가장 큰 영역(이음새 쌍) 찾기
    rm = rmaps[seam_i]
    nx, ny = 8, 8  # 잔차 지도를 8×8 칸으로 나눠 평균이 가장 큰 칸
    blocks = cv2.resize(rm, (nx, ny), interpolation=cv2.INTER_AREA)
    by, bx = np.unravel_index(int(blocks.argmax()), blocks.shape)
    hot = (((bx + 0.5) * rm.shape[1] / nx + 8) / W, ((by + 0.5) * rm.shape[0] / ny + 8) / H)  # 화면 비율 좌표(중심)

    res = dict(frame=s, v_before=v_b, v_after=v_a, ratio=ratio, ratio_near=float(ratio_near),
               seam_speed=seam['speed'], q_seam=q_seam, angle=ang, angle_seam=ang_seam, stop_go=stop_go,
               pop_ratio=pop_ratio, resid_seam=seam['resid'], resid_med=res_med, other_pops=other_pops,
               cont_seam=c_seam, cont_med=c_med, luma_step=luma_step, verdict=verdict,
               fails=fails, warns=warns, hot=hot)
    return res, rows


def plot_panel(rows, s, w, h, res):
    img = Image.new('RGB', (w, h), 'white')
    d = ImageDraw.Draw(img)
    f = font(14)
    ks = sorted(rows)
    sp = np.array([rows[i]['speed'] for i in ks])
    rs = np.array([rows[i]['resid'] for i in ks])
    m, top = 36, 20
    x = lambda i: m + (i - ks[0]) * (w - m - 10) / max(len(ks) - 1, 1)  # noqa: E731
    smax = max(sp.max() * 1.15, 0.05)
    rmax = max(rs.max() * 1.15, 1e-3)
    d.line([(m, h - 22), (w - 10, h - 22)], fill='gray')
    d.line([(m, top), (m, h - 22)], fill='gray')
    xs = x(s - 1) + (x(s) - x(s - 1)) / 2 if s in rows else x(s - 1)
    d.line([(xs, top), (xs, h - 22)], fill='red', width=2)
    d.line([(x(i), h - 22 - v / smax * (h - 22 - top)) for i, v in zip(ks, sp)], fill='blue', width=2)
    d.line([(x(i), h - 22 - v / rmax * (h - 22 - top)) for i, v in zip(ks, rs)], fill=(220, 120, 0), width=1)
    d.text((m + 4, 2), f'blue=speed %W/f (max {smax:.3f})  orange=residual  red=seam', fill='black', font=f)
    d.text((m + 4, h - 20), f'{(ks[0] + 1 - s) / 24:+.1f}s', fill='black', font=f)
    d.text((w - 60, h - 20), f'{(ks[-1] + 1 - s) / 24:+.1f}s', fill='black', font=f)
    d.text((m + 4, 20), f'before {res["v_before"]:.3f}  after {res["v_after"]:.3f}  ratio {res["ratio"]:.2f}',
           fill='black', font=f)
    return img


def sheet(path, seams, thumbs, fulls, rows_by_seam, labels):
    f, fb = font(15), font(20)
    width = TW * len(OFFSETS)
    crop_w, crop_h = 480, 270
    blocks = []
    for (s, res), lab in zip(seams, labels):
        head = Image.new('RGB', (width, 34), (30, 30, 30))
        d = ImageDraw.Draw(head)
        col = {'합격': (120, 220, 120), '확인 필요': (240, 200, 80), '불합격': (240, 90, 90)}[res['verdict']]
        tag = {'합격': 'PASS', '확인 필요': 'CHECK', '불합격': 'FAIL'}[res['verdict']]
        ang = f'{res["angle"]:.0f}' if res['angle'] is not None else '-'
        d.text((8, 6), f'{lab}  f{s} ({s / 24:.3f}s)  [{tag}]  speed ratio {res["ratio"]:.2f}  dir {ang}deg  '
                       f'seam pair x{res["q_seam"]:.2f}  pop x{res["pop_ratio"]:.2f}  cont {res["cont_seam"]:.2f}/'
                       f'{res["cont_med"]:.2f}  luma {res["luma_step"]:.1f}', fill=col, font=fb)
        row = Image.new('RGB', (width, TH + 20), 'black')
        for k, o in enumerate(OFFSETS):
            i = s + o
            if i not in thumbs:
                continue
            im = Image.fromarray(cv2.cvtColor(thumbs[i], cv2.COLOR_BGR2RGB))
            d = ImageDraw.Draw(im)
            d.rectangle([0, 0, TW - 1, TH - 1], outline=(255, 60, 60) if o >= 0 else (255, 220, 0), width=3)
            row.paste(im, (k * TW, 0))
            ImageDraw.Draw(row).text((k * TW + 6, TH + 2), f'{o:+d} (f{i})', fill='white', font=f)
        # 잔차가 가장 큰 영역 2배 확대: s-2, s-1, s, s+1
        crops = Image.new('RGB', (width, crop_h + 20), 'black')
        hx, hy = res['hot']
        for k, i in enumerate((s - 2, s - 1, s, s + 1)):
            if i not in fulls:
                continue
            fr = fulls[i]
            fh, fw = fr.shape[:2]
            cw, ch = fw // 8, fh // 8
            x0 = int(np.clip(hx * fw - cw / 2, 0, fw - cw))
            y0 = int(np.clip(hy * fh - ch / 2, 0, fh - ch))
            c = cv2.resize(fr[y0:y0 + ch, x0:x0 + cw], (crop_w, crop_h), interpolation=cv2.INTER_LANCZOS4)
            im = Image.fromarray(cv2.cvtColor(c, cv2.COLOR_BGR2RGB))
            ImageDraw.Draw(im).rectangle([0, 0, crop_w - 1, crop_h - 1],
                                         outline=(255, 60, 60) if i >= s else (255, 220, 0), width=3)
            crops.paste(im, (k * crop_w, 0))
            ImageDraw.Draw(crops).text((k * crop_w + 6, crop_h + 2),
                                       f'zoom {i - s:+d} (f{i}) max-residual area', fill='white', font=f)
        crops.paste(plot_panel(rows_by_seam[s], s, width - 4 * crop_w, crop_h + 20, res), (4 * crop_w, 0))
        blocks += [head, row, crops]
    out = Image.new('RGB', (width, sum(b.height for b in blocks)), 'black')
    y = 0
    for b in blocks:
        out.paste(b, (0, y))
        y += b.height
    out.save(path, quality=88)


def main():
    ap = argparse.ArgumentParser(description='이음새 속도·방향·팝·끊김 검사')
    ap.add_argument('film')
    ap.add_argument('--seams', nargs='*', help='새 조각 첫 프레임의 시각(초) 또는 f번호')
    ap.add_argument('--edit', help='finish.py의 .edit.json (기본: 영상 옆에 있으면 사용)')
    ap.add_argument('--out')
    ap.add_argument('--window', type=float, default=1.0, help='앞뒤 비교 길이(초)')
    ap.add_argument('--ratio-lo', type=float, default=0.7)
    ap.add_argument('--ratio-hi', type=float, default=1.4)
    ap.add_argument('--angle', type=float, default=45.0, help='방향 차 한도(도)')
    ap.add_argument('--pop', type=float, default=2.0, help='팝 비율 한도')
    a = ap.parse_args()

    name = os.path.splitext(os.path.basename(a.film))[0]
    out = a.out or os.path.join(os.path.dirname(os.path.abspath(a.film)), f'{name}_seamcheck')
    os.makedirs(out, exist_ok=True)
    fps = cv2.VideoCapture(a.film).get(cv2.CAP_PROP_FPS)
    labels = {}
    if a.seams:
        seam_frames = [parse_seam(x, fps) for x in a.seams]
    else:
        ej = a.edit or os.path.splitext(a.film)[0] + '.edit.json'
        if not os.path.exists(ej):
            raise SystemExit('--seams 를 주거나 finish.py의 .edit.json 이 필요함')
        doc = json.load(open(ej, encoding='utf-8'))
        seam_frames = [x['frame'] for x in doc['seams']]
        labels = {x['frame']: f'seam{x["index"]} {x["before"]}>{x["after"]}' for x in doc['seams']}
        print(f'이음새 {len(seam_frames)}개를 {ej}에서 읽음')
    if not seam_frames:
        raise SystemExit('이음새가 없음')
    n = int(round(a.window * fps))
    margin = max(n + 2, max(abs(o) for o in OFFSETS) + 1)
    need = {i for s in seam_frames for i in range(s - margin, s + margin + 1) if i >= 0}
    full_need = {i for s in seam_frames for i in range(s - 2, s + 2) if i >= 0}
    small, thumbs, fulls, fps, total = read_window_frames(a.film, need, full_need)

    dis = cv2.DISOpticalFlow_create(cv2.DISOPTICAL_FLOW_PRESET_MEDIUM)
    gy, gx = np.mgrid[0:H, 0:W].astype(np.float32)
    results, rows_by_seam, pair_rows = [], {}, []
    for k, s in enumerate(seam_frames, 1):
        if not (1 <= s < total):
            print(f'이음새 f{s}: 영상 범위(1~{total - 1}) 밖이라 건너뜀')
            continue
        res, rows = check_seam(s, small, n, a, dis, gx, gy)
        if res is None:
            continue
        res['label'] = labels.get(s, f'seam{k}')
        results.append((s, res))
        rows_by_seam[s] = rows
        for i, r in sorted(rows.items()):
            pair_rows.append(dict(seam=res['label'], seam_frame=s, pair=f'{i}-{i + 1}', offset=i + 1 - s,
                                  t=round((i + 1) / fps, 4), speed_pct=round(r['speed'], 4), tx_pct=round(r['tx'], 4),
                                  ty_pct=round(r['ty'], 4), zoom_pct=round(r['zoom'], 4), rot_deg=round(r['rot'], 4),
                                  resid=round(r['resid'], 3), luma=round(r['luma_b'], 2),
                                  is_seam=int(i == s - 1)))

    print(f'{name}: {total}프레임 @ {fps:.2f}fps, 이음새 {len(results)}개 (앞뒤 {a.window}초 비교)')
    summ = []
    for s, r in results:
        ang = f'{r["angle"]:.0f}°' if r['angle'] is not None else '-'
        print(f'- {r["label"]} f{s} ({s / fps:.3f}초): {r["verdict"]}')
        print(f'    속도 앞 {r["v_before"]:.3f} → 뒤 {r["v_after"]:.3f} %/f, 비율 {r["ratio"]:.2f} '
              f'(0.25초 기준 {r["ratio_near"]:.2f}), 방향 차 {ang}, 이음새 쌍 {r["seam_speed"]:.3f} (주변의 {r["q_seam"]:.2f}배)')
        print(f'    팝 비율 {r["pop_ratio"]:.2f} (잔차 {r["resid_seam"]:.2f} / 주변 {r["resid_med"]:.2f}), '
              f'장면 정합 {r["cont_seam"]:.3f} / 주변 {r["cont_med"]:.3f}, 밝기 차 {r["luma_step"]:.2f}, '
              f'0.5초 최저 속도 {r["stop_go"]:.2f}배')
        if r['other_pops']:
            print(f'    (이음새 밖 창 안의 팝 의심 프레임: {r["other_pops"]})')
        for x in r['fails']:
            print(f'    불합격 사유: {x}')
        for x in r['warns']:
            print(f'    확인할 것: {x}')
        summ.append(dict(seam=r['label'], frame=s, time_s=round(s / fps, 4), verdict=r['verdict'],
                         speed_before=round(r['v_before'], 4), speed_after=round(r['v_after'], 4),
                         speed_ratio=round(r['ratio'], 3), speed_ratio_025s=round(r['ratio_near'], 3),
                         direction_deg=round(r['angle'], 1) if r['angle'] is not None else '',
                         seam_pair_speed=round(r['seam_speed'], 4), seam_pair_vs_near=round(r['q_seam'], 3),
                         stop_go_min=round(r['stop_go'], 3), pop_ratio=round(r['pop_ratio'], 3),
                         continuity_seam=round(r['cont_seam'], 4), continuity_near=round(r['cont_med'], 4),
                         luma_step=round(r['luma_step'], 2), fails=' / '.join(r['fails']), warns=' / '.join(r['warns'])))
    if not summ:
        raise SystemExit('검사한 이음새가 없음')
    p_sum = os.path.join(out, f'{name}_seams.csv')
    with open(p_sum, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(summ[0]))
        w.writeheader()
        w.writerows(summ)
    p_pair = os.path.join(out, f'{name}_seam_pairs.csv')
    with open(p_pair, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=list(pair_rows[0]))
        w.writeheader()
        w.writerows(pair_rows)
    p_jpg = os.path.join(out, f'{name}_seams.jpg')
    sheet(p_jpg, results, thumbs, fulls, rows_by_seam, [r['label'] for _, r in results])
    print(f'저장: {p_sum}\n      {p_pair}\n      {p_jpg}')
    bad = [r for _, r in results if r['verdict'] == '불합격']
    print(f'결과: 합격 {sum(r["verdict"] == "합격" for _, r in results)}, '
          f'확인 필요 {sum(r["verdict"] == "확인 필요" for _, r in results)}, 불합격 {len(bad)}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
