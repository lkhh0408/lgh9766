"""최종 영상의 '이미지 번호 ↔ 영상 시간' 대응표(한국어 CSV + Markdown)를 만든다. 무료(로컬 계산만 함).

계획표의 시간(생성 기준 0~96초)은 편집에서 앞뒤를 자르고, 겹침 재시작으로 겹친 부분을 잘라 내고,
느린 출발을 빨리 감으면 달라진다. 이 스크립트는 최종 자르기 목록을 따라 영상의 프레임 하나하나가
계획표의 몇 초에 해당하는지 계산한 뒤, 이미지마다 실제 영상에서 나오는 시각을 적는다.

입력
- 계획표: work/final/plan/plan.csv (구간 A1~F2의 계획 시간·원본 이미지 범위·움직임·시간대)
- 이미지별 계획 시간: work/final/plan/이미지_시간_대응표.csv (있으면 사용. 없으면 plan.csv의 이미지 범위를
  구간 시간에 고르게 나눔)
- 최종 편집: finish.py가 만든 <영상>.edit.json(--edit, 권장) 또는 자르기 목록 CSV(--trims, 원본 mp4가 있어야 함)

원본 시간 ↔ 계획 시간 정하는 법(자르기 목록의 조각마다, 위에서부터 먼저 맞는 것)
1. plan_segs 열: 예) F1:0-8;F2:8-18 → 원본 0~8초가 F1, 8~18초가 F2(F2를 10초로 만든 경우). 구간 안은 고르게 늘이거나 줄임.
2. plan_t0 열: 원본 t초 = 계획 (plan_t0 + t)초.
3. label: A, B(묶음 이름), A1, B2-C2(구간 이름·범위)를 찾아, 그 구간들이 원본 0초부터 plan.csv 길이(8초)대로
   차례로 들어 있다고 본다. 원본이 그 합보다 0.5초 넘게 길면 마지막 구간을 원본 끝까지 늘인다(주의로 알림).
   겹침 재시작 묶음도 이 방식이 맞다(프롬프트 내용은 그 원본 0초부터 계획대로 나오므로).
위 셋 다 없으면 그 조각은 대응에서 빠진다(주의로 알림).

상태
- 전부 나옴: 그 이미지의 계획 시간이 영상에 95% 이상 남음
- 일부 잘림: 일부만 남음(겹침·끝 자르기)
- 잘려서 없음: 만든 원본에는 있었지만 편집에서 모두 잘림(가장 가까운 영상 시각을 적음)
- 원본 없음: 아직 그 시간의 원본 영상이 없음(생성 전)

사용(저장소 루트)
  python3 work/scripts/mapping_table.py --edit work/final/edit/최종_1080p.edit.json
  python3 work/scripts/mapping_table.py --trims work/final/edit/자르기.csv --out work/final/edit/이미지_시간_대응표_최종
  선택: --plan 다른계획.csv --images 다른대응표.csv
결과: <출력>.csv (UTF-8 BOM, 엑셀에서 바로 열림), <출력>.md
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finish import FPS  # noqa: E402

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..'))
PLAN = os.path.join(ROOT, 'work', 'final', 'plan', 'plan.csv')
IMAGES = os.path.join(ROOT, 'work', 'final', 'plan', '이미지_시간_대응표.csv')
FULL = 0.95  # 이만큼 이상 남으면 '전부 나옴'


# ---------------------------------------------------------------- 읽기

def read_csv(path):
    with open(path, encoding='utf-8-sig', newline='') as f:
        return [r for r in csv.DictReader(ln for ln in f if ln.strip() and not ln.lstrip().startswith('#'))]


def load_plan(path):
    rows = read_csv(path)
    for r in rows:
        r['t_start'], r['t_end'] = float(r['t_start']), float(r['t_end'])
    return rows


def kind_of(use):
    head = (use or '').split(':')[0].strip()
    for k in ('시작 키프레임', '내용 참조', '색 참조', '제외'):
        if head.startswith(k):
            return k
    return head or '-'


def load_images(path, plan):
    """이미지별 계획 시간. 대응표 CSV가 있으면 그대로, 없으면 plan.csv 이미지 범위를 구간 시간에 고르게 나눔."""
    out = []
    if path and os.path.exists(path):
        for r in read_csv(path):
            out.append(dict(img=r['이미지'].strip().zfill(3), seg=r['구간'].strip(), a=float(r['영상시작초']),
                            b=float(r['영상끝초']), use=r.get('쓰임', '').strip()))
        src = path
    else:
        for p in plan:
            lo, hi = int(p['src_from']), int(p['src_to'])
            k = hi - lo + 1
            for j, n in enumerate(range(lo, hi + 1)):
                a = p['t_start'] + (p['t_end'] - p['t_start']) * j / k
                b = p['t_start'] + (p['t_end'] - p['t_start']) * (j + 1) / k
                out.append(dict(img=f'{n:03d}', seg=p['seg_id'], a=round(a, 3), b=round(b, 3), use=''))
        src = path + ' (없어서 plan.csv로 계산)' if path else 'plan.csv로 계산'
    for r in out:
        r['kind'] = kind_of(r['use'])
    return out, src


def load_segments(edit, trims):
    """편집 조각 목록(finish.py와 같은 계산). 각 조각: label, raw, raw_frames, kept, film_start_frame, plan_t0, extra."""
    if edit:
        doc = json.load(open(edit, encoding='utf-8'))
        segs = []
        for s in doc['segments']:
            kept = s.get('kept') or list(range(s['in_frame'], s['out_frame']))
            segs.append(dict(index=s['index'], label=s['label'], raw=s['raw'], raw_frames=s['raw_frames'], kept=kept,
                             in_frame=s['in_frame'], out_frame=s['out_frame'], ff_s=s.get('ff_s'), ff_x=s.get('ff_x'),
                             film_start_frame=s['film_start_frame'], film_end_frame=s['film_end_frame'],
                             plan_t0=s.get('plan_t0'), extra=s.get('extra') or {}))
        return segs, doc['frames'], dict(film=doc.get('film'), trims=doc.get('trims'), edit=edit)
    from finish import load_trims
    segs = load_trims(trims)
    return segs, segs[-1]['film_end_frame'], dict(film=None, trims=trims, edit=None)


# ---------------------------------------------------------------- 원본 시간 → 계획 시간

def ids_from_label(label, plan):
    order = [p['seg_id'] for p in plan]
    chains = {}
    for p in plan:
        chains.setdefault(p['chain'], []).append(p['seg_id'])
    got = []
    for x, y in re.findall(r'([A-Z]\d+)\s*[-~]\s*([A-Z]\d+)', label):
        if x in order and y in order and order.index(x) <= order.index(y):
            got += order[order.index(x):order.index(y) + 1]
    for tok in re.split(r'[^A-Za-z0-9]+', label):
        if tok in order:
            got.append(tok)
        elif tok in chains:
            got += chains[tok]
    seen = []
    for g in sorted(set(got), key=order.index):
        seen.append(g)
    return seen


def parse_plan_segs(spec, plan):
    """'F1:0-8;F2:8-18' → [(구간, 원본 시작초, 원본 끝초)]"""
    order = {p['seg_id'] for p in plan}
    out = []
    for part in re.split(r'[;,\s]+', spec.strip()):
        if not part:
            continue
        m = re.fullmatch(r'([A-Z]\d+):(-?[\d.]+)-([\d.]+)', part)
        if not m or m.group(1) not in order:
            raise SystemExit(f'plan_segs 형식 오류: {part!r} (예: F1:0-8;F2:8-18)')
        out.append((m.group(1), float(m.group(2)), float(m.group(3))))
    return out


def pieces_for(seg, plan):
    """조각의 원본 → 계획 대응: [(r0, r1, p0, p1, 구간)] (원본 초, 계획 초). 방식 설명, 주의도 돌려줌."""
    byid = {p['seg_id']: p for p in plan}
    raw_dur = seg['raw_frames'] / FPS if seg.get('raw_frames') else None
    notes = []
    spec = (seg.get('extra') or {}).get('plan_segs')
    if spec:
        ps = [(r0, r1, byid[i]['t_start'], byid[i]['t_end'], i) for i, r0, r1 in parse_plan_segs(spec, plan)]
        return ps, f'plan_segs {spec}', notes
    if seg.get('plan_t0') is not None:
        t0 = float(seg['plan_t0'])
        end = raw_dur if raw_dur else max(p['t_end'] for p in plan) - t0
        ps = []
        for p in plan:
            r0, r1 = max(0.0, p['t_start'] - t0), min(end, p['t_end'] - t0)
            if r1 > r0:
                ps.append((r0, r1, t0 + r0, t0 + r1, p['seg_id']))
        return ps, f'plan_t0 {t0:g}초(원본 t초 = 계획 {t0:g}+t초)', notes
    ids = ids_from_label(seg['label'], plan)
    if not ids:
        notes.append(f'조각 {seg["label"]}: label에서 계획 구간을 못 찾았고 plan_t0·plan_segs도 없어 대응에서 뺌')
        return [], '대응 없음', notes
    ps, r = [], 0.0
    for i in ids:
        d = byid[i]['t_end'] - byid[i]['t_start']
        ps.append([r, r + d, byid[i]['t_start'], byid[i]['t_end'], i])
        r += d
    if raw_dur is not None and raw_dur > r + 0.5:
        notes.append(f'조각 {seg["label"]}: 원본 {raw_dur:.2f}초 > 계획 {r:g}초 → 마지막 구간 {ids[-1]}를 원본 끝까지 늘임')
        ps[-1][1] = raw_dur
    elif raw_dur is not None and raw_dur < r - 0.5:
        notes.append(f'조각 {seg["label"]}: 원본 {raw_dur:.2f}초 < 계획 {r:g}초 → 뒷부분 계획 시간은 원본 없음')
    return [tuple(p) for p in ps], f'label {"+".join(ids)} (원본 0초부터 {r:g}초)', notes


def raw_to_plan(t, ps):
    for r0, r1, p0, p1, sid in ps:
        if r0 <= t < r1:
            return p0 + (t - r0) * (p1 - p0) / (r1 - r0), sid, (p1 - p0) / (r1 - r0) / FPS
    return None, None, None


# ---------------------------------------------------------------- 표 만들기

def tc(sec):
    """영상 시각 → 분:초+프레임 (예: 01:05+07f)"""
    if sec is None or (isinstance(sec, float) and math.isnan(sec)):
        return ''
    f = int(round(sec * FPS))
    m, s, fr = f // (60 * FPS), (f // FPS) % 60, f % FPS
    return f'{m:02d}:{s:02d}+{fr:02d}f'


def build(plan, images, segs, total):
    # 영상 프레임마다: 계획 시각, 구간, 계획 1프레임 길이, 조각 번호, 원본 시각
    fp = [None] * total
    covered = []  # 원본이 있는 계획 범위(편집에서 잘린 부분 포함)
    seg_info, notes = [], []
    for k, s in enumerate(segs):
        ps, how, nt = pieces_for(s, plan)
        notes += nt
        covered += [(p0, p1) for _, _, p0, p1, _ in ps]
        for j, r in enumerate(s['kept']):
            f = s['film_start_frame'] + j
            p, sid, step = raw_to_plan((r + 0.5) / FPS, ps)
            if p is not None and 0 <= f < total:
                fp[f] = (p, sid, step, k, r)
        mapped = [fp[f] for f in range(s['film_start_frame'], s['film_end_frame']) if fp[f]]
        seg_info.append(dict(seg=s, how=how, pieces=ps,
                             plan_lo=min(m[0] for m in mapped) if mapped else None,
                             plan_hi=max(m[0] + m[2] for m in mapped) if mapped else None))
    if any(x is None for x in fp):
        notes.append(f'계획 시간과 대응하지 않는 영상 프레임 {sum(x is None for x in fp)}장')

    rows = []
    for im in images:
        a, b = im['a'], im['b']
        F = [f for f in range(total) if fp[f] and a <= fp[f][0] < b]
        r = dict(im)
        if F:
            ps_ = [fp[f][0] for f in F]
            span = max(ps_) - min(ps_) + fp[F[0]][2]
            ratio = min(1.0, span / (b - a)) if b > a else 1.0
            r.update(f0=min(F), f1=max(F) + 1, n=len(F), ratio=ratio,
                     state='전부 나옴' if ratio >= FULL else '일부 잘림',
                     split=(max(F) - min(F) + 1) != len(F))
            ks = sorted({fp[f][3] for f in F})
            r['pieces'] = ks
            r['raw_t'] = (min(fp[f][4] for f in F if fp[f][3] == ks[0]) / FPS,
                          (max(fp[f][4] for f in F if fp[f][3] == ks[-1]) + 1) / FPS)
        else:
            gen = any(p0 < b and a < p1 for p0, p1 in covered)
            near = None
            cand = [(min(abs(fp[f][0] - a), abs(fp[f][0] - b)), f) for f in range(total) if fp[f]]
            if cand:
                near = min(cand)[1]
            r.update(f0=None, f1=None, n=0, ratio=0.0, state='잘려서 없음' if gen else '원본 없음',
                     split=False, pieces=[], raw_t=None, near=near)
        rows.append(r)

    seg_rows = []
    for p in plan:
        F = [f for f in range(total) if fp[f] and fp[f][1] == p['seg_id']]
        if F:
            ps_ = [fp[f][0] for f in F]
            span = max(ps_) - min(ps_) + fp[F[0]][2]
            ratio = min(1.0, span / (p['t_end'] - p['t_start']))
            seg_rows.append(dict(p=p, f0=min(F), f1=max(F) + 1, n=len(F), ratio=ratio,
                                 state='전부 나옴' if ratio >= FULL else '일부 잘림'))
        else:
            gen = any(p0 < p['t_end'] and p['t_start'] < p1 for p0, p1 in covered)
            seg_rows.append(dict(p=p, f0=None, f1=None, n=0, ratio=0.0, state='잘려서 없음' if gen else '원본 없음'))
    return rows, seg_rows, seg_info, notes


def write_csv(path, rows, segs):
    cols = ['이미지', '계획구간', '분류', '계획시작초', '계획끝초', '영상시작초', '영상끝초', '영상시작(분:초+프레임)',
            '영상에 나오는 길이(초)', '남은 비율', '상태', '편집조각', '원본파일', '원본시작초', '원본끝초', '쓰임']
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(cols)
        for r in rows:
            if r['n']:
                pcs = '+'.join(segs[k]['label'] for k in r['pieces'])
                raws = '+'.join(os.path.basename(segs[k]['raw']) for k in r['pieces'])
                state = r['state'] + (' (여러 곳에 나뉘어 나옴)' if r['split'] else '')
                w.writerow([r['img'], r['seg'], r['kind'], f'{r["a"]:.2f}', f'{r["b"]:.2f}',
                            f'{r["f0"] / FPS:.3f}', f'{r["f1"] / FPS:.3f}', tc(r['f0'] / FPS), f'{r["n"] / FPS:.3f}',
                            f'{r["ratio"]:.2f}', state, pcs, raws, f'{r["raw_t"][0]:.3f}', f'{r["raw_t"][1]:.3f}',
                            r['use']])
            else:
                near = f' (가장 가까운 영상 시각 {r["near"] / FPS:.3f}초)' if r.get('near') is not None else ''
                w.writerow([r['img'], r['seg'], r['kind'], f'{r["a"]:.2f}', f'{r["b"]:.2f}', '', '', '', '0',
                            '0.00', r['state'] + near, '', '', '', '', r['use']])


def md_escape(s):
    return (s or '').replace('|', '\\|').replace('\n', ' ')


def write_md(path, rows, seg_rows, seg_info, notes, total, src, img_src, plan_path):
    L = []
    L.append('# 이미지 번호 ↔ 최종 영상 시간 대응표')
    L.append('')
    L.append(f'- 만든 시각: {dt.datetime.now().strftime("%Y-%m-%d %H:%M")} (mapping_table.py, 자동 생성)')
    if src.get('film'):
        L.append(f'- 영상: `{src["film"]}`')
    L.append(f'- 편집 기록: `{src["edit"] or src["trims"]}`')
    L.append(f'- 계획표: `{os.path.relpath(plan_path, ROOT)}`, 이미지 계획 시간: `{img_src}`')
    L.append(f'- 영상 길이: {total}프레임 = {total / FPS:.3f}초 (24fps)')
    L.append('')
    L.append('## 읽는 법')
    L.append('')
    L.append('- **계획 시간**은 생성 기준(0~96초) 시간입니다. **영상 시간**은 편집을 마친 최종 영상에서의 시간입니다.')
    L.append('- 편집에서 앞뒤를 자르거나 겹친 부분을 잘라 내면, 그 뒤의 이미지는 영상 시간이 그만큼 앞당겨집니다.')
    L.append('- 원본 이미지는 모델에 직접 넣지 않고(008번만 시작 장면으로 씀), 장면 내용을 프롬프트로 옮기는 참조로 썼습니다.'
             ' 그래서 "그 이미지가 그 시각에 그대로 나온다"가 아니라 "그 이미지의 내용이 그 시각쯤에 나온다"는 뜻입니다.')
    L.append(f'- 상태: 전부 나옴(계획 시간의 {int(FULL * 100)}% 이상 남음) / 일부 잘림 / 잘려서 없음(만들었지만 편집에서 잘림) /'
             ' 원본 없음(아직 만들지 않음).')
    L.append('')
    L.append('## 편집 조각(자르기 목록)')
    L.append('')
    L.append('| 순서 | 이름 | 원본 파일 | 원본 구간(초) | 영상 구간(초) | 빨리 감기 | 계획 시간 대응 |')
    L.append('|---|---|---|---|---|---|---|')
    for si in seg_info:
        s = si['seg']
        ff = f'{s["ff_s"]:g}초 {s["ff_x"]:g}배→1배' if s.get('ff_s') and (s.get('ff_x') or 1) > 1 else '-'
        L.append(f'| {s["index"]} | {md_escape(s["label"])} | `{os.path.basename(s["raw"])}` | '
                 f'{s["in_frame"] / FPS:.3f}~{s["out_frame"] / FPS:.3f} | '
                 f'{s["film_start_frame"] / FPS:.3f}~{s["film_end_frame"] / FPS:.3f} | {ff} | {md_escape(si["how"])} |')
    L.append('')
    if len(seg_info) > 1:
        L.append('이음새(새 조각이 시작하는 영상 시각): ' + ', '.join(
            f'{si["seg"]["film_start_frame"] / FPS:.3f}초({md_escape(seg_info[k - 1]["seg"]["label"])}→'
            f'{md_escape(si["seg"]["label"])})' for k, si in enumerate(seg_info) if k))
        L.append('')
    L.append('## 계획 구간별 영상 시간')
    L.append('')
    L.append('| 구간 | 이미지 | 계획(초) | 영상(초) | 남은 비율 | 상태 | 움직임 | 시간대 |')
    L.append('|---|---|---|---|---|---|---|---|')
    for r in seg_rows:
        p = r['p']
        film = f'{r["f0"] / FPS:.2f}~{r["f1"] / FPS:.2f}' if r['n'] else '-'
        L.append(f'| {p["seg_id"]} | {p["src_from"]}~{p["src_to"]} | {p["t_start"]:g}~{p["t_end"]:g} | {film} | '
                 f'{r["ratio"]:.2f} | {r["state"]} | {md_escape(p["motion"])} | {md_escape(p["time_of_day"])} |')
    L.append('')
    L.append('## 이미지별 대응')
    L.append('')
    L.append('| 이미지 | 구간 | 분류 | 계획(초) | 영상(초) | 영상 시각 | 상태 | 쓰임 |')
    L.append('|---|---|---|---|---|---|---|---|')
    for r in rows:
        if r['n']:
            film, t = f'{r["f0"] / FPS:.2f}~{r["f1"] / FPS:.2f}', tc(r['f0'] / FPS)
            st = r['state'] + (f' ({r["ratio"]:.0%})' if r['state'] == '일부 잘림' else '') \
                + (' (나뉘어 나옴)' if r['split'] else '')
        else:
            film, t = '-', ''
            st = r['state'] + (f' (가장 가까운 {r["near"] / FPS:.2f}초)' if r.get('near') is not None else '')
        use = (r['use'].split(':', 1)[1].strip() if ':' in r['use'] else r['use'])
        L.append(f'| {r["img"]} | {r["seg"]} | {r["kind"]} | {r["a"]:.1f}~{r["b"]:.1f} | {film} | {t} | {st} | '
                 f'{md_escape(use)} |')
    L.append('')
    L.append('## 요약')
    L.append('')
    kinds = [k for k in ('시작 키프레임', '내용 참조', '색 참조', '제외') if any(r['kind'] == k for r in rows)]
    kinds += sorted({r['kind'] for r in rows} - set(kinds))
    states = ['전부 나옴', '일부 잘림', '잘려서 없음', '원본 없음']
    L.append('| 분류 | ' + ' | '.join(states) + ' | 합계 |')
    L.append('|---|' + '---|' * (len(states) + 1))
    for k in kinds:
        c = [sum(r['kind'] == k and r['state'] == s for r in rows) for s in states]
        L.append(f'| {k} | ' + ' | '.join(map(str, c)) + f' | {sum(c)} |')
    c = [sum(r['state'] == s for r in rows) for s in states]
    L.append('| 합계 | ' + ' | '.join(map(str, c)) + f' | {len(rows)} |')
    L.append('')
    if notes:
        L.append('## 주의')
        L.append('')
        L += [f'- {md_escape(n)}' for n in notes]
        L.append('')
    with open(path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L))


def main():
    ap = argparse.ArgumentParser(description='이미지 번호 ↔ 최종 영상 시간 대응표')
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument('--edit', help='finish.py의 <영상>.edit.json (권장)')
    g.add_argument('--trims', help='자르기 목록 CSV(원본 mp4가 있어야 함)')
    ap.add_argument('--plan', default=PLAN)
    ap.add_argument('--images', default=IMAGES, help='이미지별 계획 시간 CSV(없으면 plan.csv로 계산)')
    ap.add_argument('--out', help='출력 이름(확장자 없이). 기본: 편집 기록 옆 <이름>_대응표')
    a = ap.parse_args()

    plan = load_plan(a.plan)
    images, img_src = load_images(a.images, plan)
    segs, total, src = load_segments(a.edit, a.trims)
    base = a.edit or a.trims
    stem = a.out or re.sub(r'(\.edit)?\.(json|csv)$', '', base) + '_대응표'
    os.makedirs(os.path.dirname(os.path.abspath(stem)) or '.', exist_ok=True)

    rows, seg_rows, seg_info, notes = build(plan, images, segs, total)
    write_csv(stem + '.csv', rows, segs)
    write_md(stem + '.md', rows, seg_rows, seg_info, notes,
             total, src, os.path.relpath(img_src, ROOT) if os.path.exists(img_src) else img_src, a.plan)

    print(f'영상 {total}프레임 = {total / FPS:.3f}초, 편집 조각 {len(segs)}개, 이미지 {len(rows)}장')
    for si in seg_info:
        print(f'  조각 {si["seg"]["index"]} {si["seg"]["label"]}: {si["how"]}')
    for r in seg_rows:
        film = f'영상 {r["f0"] / FPS:.2f}~{r["f1"] / FPS:.2f}초' if r['n'] else '영상에 없음'
        print(f'  {r["p"]["seg_id"]} (계획 {r["p"]["t_start"]:g}~{r["p"]["t_end"]:g}초): {film}, {r["state"]}')
    cnt = {s: sum(r['state'] == s for r in rows) for s in ('전부 나옴', '일부 잘림', '잘려서 없음', '원본 없음')}
    print('  이미지 상태: ' + ', '.join(f'{k} {v}' for k, v in cnt.items()))
    for n in notes:
        print('  주의:', n)
    print(f'저장: {stem}.csv\n      {stem}.md')


if __name__ == '__main__':
    main()
