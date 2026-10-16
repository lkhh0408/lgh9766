"""4K 원본 영상들을 잘라 이어 1080p 24fps 최종 편집본으로 마감한다. 무료(로컬 계산만 함, API 호출 없음).

하는 일
1. 자르기 목록 CSV를 읽는다. 한 줄이 한 조각(원본 파일 하나의 구간)이다.
2. 조각마다 프레임 단위로 정확히 자르고(trim/select), 1920×1080 lanczos로 줄인다.
   필요하면 윤곽(흰 테두리) 완화 필터를 건다.
3. 조각들을 크로스페이드 없이 그대로 이어(concat) 한 번만 인코딩한다.
   x264 crf 16, preset slow, yuv420p, 24fps, 소리 없음, faststart.
   조각 경계(이음새)에는 키프레임을 넣어 둔다. 그래서 조각별 파일은 완성본에서 재인코딩 없이 그대로 잘라 낸다.
4. 이음새마다 앞뒤 1초를 4배 느리게(프레임 반복, 보간 없음) 만든 확인용 영상을 따로 저장한다.
5. 검사: 해상도·fps·프레임 수(조각 합과 같은지)·오디오 없음, 그리고 조각마다 첫·끝 프레임이
   원본의 바로 그 프레임인지(앞뒤 프레임보다 더 닮았는지) 확인한다. 조각별 파일은 완성본과 프레임 단위로 똑같은지 확인한다.

자르기 목록 CSV (UTF-8, 첫 줄은 열 이름, '#'으로 시작하는 줄은 무시)
  필수 열: raw,in_s,out_s,label
    raw   : 4K 원본 mp4 경로(저장소 루트 기준, 없으면 CSV가 있는 폴더 기준)
    in_s  : 남길 첫 프레임. 초(예: 0, 15.5) 또는 프레임 번호(예: f372 또는 372f, 0부터 셈). 비우면 처음.
    out_s : 잘라 낼 첫 프레임(이 프레임은 안 들어감). 초 또는 프레임 번호. 비우면 끝까지.
            음수는 끝에서 거꾸로 셈(-1.0 = 끝 1초 전, -25f = 끝에서 25프레임 전).
            예) 0~16초 원본 전체 = in_s 0, out_s 16 (프레임 0~383, 384장)
    label : 조각 이름(예: A, B, A1-A2). mapping_table.py가 계획 구간을 찾을 때도 쓴다.
  선택 열
    plan_t0 : 이 원본의 0초가 계획표(plan.csv) 시간으로 몇 초인지(mapping_table.py가 씀).
              비우면 label(A, B, A1-A2 같은 구간·묶음 이름)로 계획 구간을 찾아 그 묶음 첫 구간의 시작 시각을 쓴다.
              겹침 재시작 묶음도 보통 비워 둔다(프롬프트 내용은 그 원본 0초부터 계획대로 나오므로).
    plan_segs : 원본 안에서 계획 구간이 차지하는 초(mapping_table.py가 씀). 예) F1:0-8;F2:8-18 (F2를 10초로 만든 경우).
              비우면 label의 구간들이 8초씩(plan.csv 길이) 0초부터 차례로 들어 있다고 본다.
              이 열들은 편집 결과에는 영향이 없다.
    ff_s, ff_x : 조각 앞부분 빨리 감기(재시작 '느린 출발' 보정). in_s부터 ff_s초(원본 기준) 동안
              속도를 ff_x배에서 1배로 고르게 줄이며 정수 프레임만 골라 쓴다(건너뛰기만 함, 보간·잔상 없음).
              예) ff_s 1.5, ff_x 1.6. ff_x는 1 이상이어야 한다(느리게 하기는 프레임 반복 = 멈칫이라 금지).

사용(저장소 루트)
  python3 work/scripts/finish.py --trims 자르기.csv --out work/final/edit/최종_1080p.mp4
  python3 work/scripts/finish.py --trims 자르기.csv --out 완화판.mp4 --clamp 0.8      # 윤곽 넘침 자르기(권장 완화판)
  python3 work/scripts/finish.py --trims 자르기.csv --out 완화판.mp4 --dehalo 0.2     # unsharp=5:5:-0.2:5:5:0
  선택: --crf 16 --preset slow --no-segments(조각별 파일 생략) --no-seam-clips --no-verify(원본 대조 생략)

결과
  <출력>.mp4                 최종 편집본
  <출력>.edit.json           조각·이음새·설정·검사 결과(seam_check.py, mapping_table.py가 읽음)
  <출력>_segments/NN_라벨.mp4 조각별 파일(완성본에서 그대로 잘라 낸 것)
  <출력>_seams/seamK_..._slow4x.mp4  이음새 앞뒤 1초, 4배 느리게
종료 코드: 모든 검사 통과 0, 하나라도 실패 1.
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time

import numpy as np

FPS = 24
OUT_W, OUT_H = 1920, 1080
FONT = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


# ---------------------------------------------------------------- 영상 정보

COLOR_KEYS = ('color_range', 'color_space', 'color_transfer', 'color_primaries')


def probe(path):
    """영상 정보(머리 정보 기준): 폭·높이·fps·프레임 수·오디오 유무·길이·색 표시 정보."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-show_entries',
                          'stream=index,codec_type,codec_name,width,height,r_frame_rate,nb_frames,pix_fmt,'
                          + ','.join(COLOR_KEYS),
                          '-show_entries', 'format=duration', '-of', 'json', path],
                         capture_output=True, text=True, check=True).stdout
    j = json.loads(out)
    vs = [s for s in j['streams'] if s['codec_type'] == 'video']
    if not vs:
        raise SystemExit(f'영상 스트림이 없음: {path}')
    v = vs[0]
    num, den = map(int, v['r_frame_rate'].split('/'))
    return dict(width=int(v['width']), height=int(v['height']), fps=num / den, fps_str=v['r_frame_rate'],
                codec=v.get('codec_name'), pix_fmt=v.get('pix_fmt'), nb_frames=int(v.get('nb_frames') or 0),
                has_audio=any(s['codec_type'] == 'audio' for s in j['streams']),
                duration=float(j['format'].get('duration') or 0),
                color={k: v.get(k, 'unknown') for k in COLOR_KEYS})


def count_packets(path):
    """머리 정보 대신 실제 영상 패킷 수(디코드 없이 빠름)."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets',
                          '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().split(',')[0])


def frame_md5s(path):
    """디코드한 프레임마다의 md5 목록(ffmpeg framemd5). 프레임 수 확인과 '똑같은 프레임인지' 비교에 쓴다."""
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0', '-f', 'framemd5', '-'],
                         capture_output=True, text=True, check=True).stdout
    return [ln.split(',')[-1].strip() for ln in out.splitlines() if ln and not ln.startswith('#')]


def grab_frames(path, indices, size=(960, 540)):
    """지정한 프레임 번호(0부터, 표시 순서)들을 회색조 작은 그림으로 꺼낸다. {번호: 배열}."""
    idx = sorted(set(int(i) for i in indices))
    if not idx:
        return {}
    expr = '+'.join(f'eq(n,{i})' for i in idx)
    w, h = size
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0',
                          '-vf', f"select='{expr}',scale={w}:{h}:flags=area,format=gray",
                          '-fps_mode', 'passthrough', '-frames:v', str(len(idx)),
                          '-f', 'rawvideo', '-pix_fmt', 'gray', '-'],
                         capture_output=True, check=True).stdout
    arr = np.frombuffer(out, np.uint8)
    n = arr.size // (w * h)
    if n != len(idx):
        raise RuntimeError(f'{path}: 프레임 {len(idx)}장을 요청했는데 {n}장만 나옴 (번호 {idx[:5]}...)')
    arr = arr.reshape(n, h, w)
    return {i: arr[k] for k, i in enumerate(idx)}


# ---------------------------------------------------------------- 자르기 목록

def parse_point(spec, n_frames, default, fps=FPS):
    """'15.5'(초), 'f372'/'372f'(프레임), 음수(끝에서), ''(기본값) → 프레임 번호."""
    s = (spec or '').strip()
    if s == '':
        return default, None
    m = re.fullmatch(r'(-?)\s*(?:[fF](\d+)|(\d+)[fF])', s)
    note = None
    if m:
        idx = int(m.group(2) or m.group(3))
        neg = m.group(1) == '-'
    else:
        x = float(s)
        neg = x < 0
        exact = abs(x) * fps
        idx = int(round(exact))
        if abs(exact - idx) > 0.01:
            note = f'{s}초는 프레임 경계가 아니라 프레임 {idx}로 반올림함'
    return (n_frames - idx if neg else idx), note


def kept_frames(in_f, out_f, ff_n=0, ff_x=1.0):
    """남길 원본 프레임 번호 목록. 빨리 감기 구간에서는 속도 ff_x→1 로 정수 프레임만 건너뛰며 고른다."""
    if not ff_n or ff_x <= 1.0:
        return list(range(in_f, out_f))
    out, p = [], float(in_f)
    while True:
        i = int(round(p))
        if i >= out_f:
            break
        if not out or i > out[-1]:
            out.append(i)
        rel = (p - in_f) / ff_n
        p += ff_x + (1.0 - ff_x) * rel if rel < 1 else 1.0
    return out


def resolve_raw(raw, csv_dir):
    if os.path.isabs(raw) or os.path.exists(raw):
        return raw
    alt = os.path.join(csv_dir, raw)
    return alt if os.path.exists(alt) else raw


def load_trims(csv_path, probe_raws=True):
    """자르기 목록 CSV → 조각 목록(dict). 원본을 읽어 프레임 수·fps를 확인한다."""
    with open(csv_path, encoding='utf-8-sig', newline='') as f:
        lines = [ln for ln in f if ln.strip() and not ln.lstrip().startswith('#')]
    rows = list(csv.DictReader(lines))
    need = {'raw', 'in_s', 'out_s', 'label'}
    if not rows or not need <= set(rows[0]):
        raise SystemExit(f'{csv_path}: 열 {sorted(need)} 이 필요함 (있는 열: {list(rows[0]) if rows else "없음"})')
    csv_dir = os.path.dirname(os.path.abspath(csv_path))
    segs = []
    for k, r in enumerate(rows):
        raw = resolve_raw(r['raw'].strip(), csv_dir)
        info = probe(raw) if probe_raws else None
        if info:
            if abs(info['fps'] - FPS) > 0.01:
                raise SystemExit(f'{raw}: {info["fps_str"]} fps. 24fps 원본만 받음(프레임 번호가 어긋나지 않게)')
            n = count_packets(raw)
        else:
            n = None
        notes = []
        in_f, nt = parse_point(r['in_s'], n, 0)
        notes += [nt] if nt else []
        if (r['out_s'] or '').strip() == '' and n is None:
            raise SystemExit(f'{csv_path} {k + 2}행: out_s가 비어 있으면 원본을 읽어야 함')
        out_f, nt = parse_point(r['out_s'], n, n)
        notes += [nt] if nt else []
        if n is not None and not (0 <= in_f < out_f <= n):
            raise SystemExit(f'{csv_path} {k + 2}행 ({r["label"]}): 구간 프레임 {in_f}~{out_f} 이 원본 0~{n} 밖이거나 비어 있음')
        ff_s = float(r.get('ff_s') or 0)
        ff_x = float(r.get('ff_x') or 1)
        if ff_s and ff_x < 1:
            raise SystemExit(f'{r["label"]}: ff_x {ff_x} < 1 (느리게 하기는 프레임 반복이라 금지)')
        if ff_x > 3:
            notes.append(f'ff_x {ff_x}는 큼(프레임 건너뛰기가 눈에 띌 수 있음)')
        ff_n = int(round(ff_s * FPS))
        kept = kept_frames(in_f, out_f, ff_n, ff_x)
        if len(kept) < 12:
            notes.append(f'조각이 {len(kept)}프레임(0.5초 미만)으로 짧음')
        pt = (r.get('plan_t0') or '').strip()
        extra = {kk: (v or '').strip() for kk, v in r.items()
                 if kk and kk not in ('raw', 'in_s', 'out_s', 'label', 'plan_t0', 'ff_s', 'ff_x') and (v or '').strip()}
        segs.append(dict(index=k + 1, label=r['label'].strip(), raw=raw, raw_frames=n, raw_info=info,
                         in_frame=in_f, out_frame=out_f, ff_s=ff_s, ff_x=ff_x, ff_n=ff_n, kept=kept,
                         plan_t0=float(pt) if pt else None, extra=extra, notes=notes))
    pos = 0
    for s in segs:
        s['film_start_frame'] = pos
        pos += len(s['kept'])
        s['film_end_frame'] = pos  # 이 프레임은 다음 조각의 첫 프레임
    return segs


# ---------------------------------------------------------------- 필터 그래프

def select_expr(kept):
    """프레임 목록 → select 식(연속 구간은 between으로 묶음)."""
    runs, s = [], kept[0]
    for a, b in zip(kept, kept[1:] + [None]):
        if b != a + 1:
            runs.append((s, a))
            s = b
    return '+'.join(f'between(n,{a},{b})' if b > a else f'eq(n,{a})' for a, b in runs)


def post_filter(src, dst, k, dehalo, clamp):
    """1080p로 줄인 뒤의 마감 필터(밝기 윤곽 완화). 크로마는 건드리지 않는다."""
    if clamp:
        # 윤곽 넘침 자르기(환경개선_방법.md 5절): 살짝 흐린 밝기의 3×3 최대·최소 범위 밖으로 튀는 밝기만 잘라 냄
        return (f'[{src}]format=yuv444p,split=3[o{k}][b1{k}][b2{k}];'
                f'[b1{k}]gblur=sigma={clamp},dilation[mx{k}];[b2{k}]gblur=sigma={clamp},erosion[mn{k}];'
                f'[o{k}][mx{k}]blend=c0_mode=darken:c1_mode=normal:c2_mode=normal[t{k}];'
                f'[t{k}][mn{k}]blend=c0_mode=lighten:c1_mode=normal:c2_mode=normal,format=yuv420p[{dst}]')
    if dehalo:
        return f'[{src}]unsharp=5:5:-{dehalo}:5:5:0,format=yuv420p[{dst}]'
    return f'[{src}]format=yuv420p[{dst}]'


def build_graph(segs, dehalo, clamp):
    parts = []
    for k, s in enumerate(segs):
        kept = s['kept']
        if kept == list(range(kept[0], kept[-1] + 1)):
            cut = f'trim=start_frame={kept[0]}:end_frame={kept[-1] + 1}'
        else:
            cut = f"select='{select_expr(kept)}'"
        parts.append(f'[{k}:v]{cut},setpts=N/({FPS}*TB),scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1[s{k}]')
        parts.append(post_filter(f's{k}', f'c{k}', k, dehalo, clamp))
    parts.append(''.join(f'[c{k}]' for k in range(len(segs))) + f'concat=n={len(segs)}:v=1:a=0[out]')
    return ';\n'.join(parts)


def enc_args(crf, preset):
    return ['-an', '-c:v', 'libx264', '-preset', preset, '-crf', str(crf), '-pix_fmt', 'yuv420p',
            '-r', str(FPS), '-movflags', '+faststart']


# ---------------------------------------------------------------- 이음새 확인 영상

def esc_text(s):
    return s.replace('\\', '\\\\').replace(':', '\\:').replace("'", '').replace('%', '\\%')


def seam_clip(film, n_total, seam_f, k, lab_a, lab_b, dst, crf):
    """이음새 앞뒤 1초를 4배 느리게(프레임을 4번씩 반복, 보간 없음)."""
    a, b = max(0, seam_f - FPS), min(n_total, seam_f + FPS)
    vf = f'trim=start_frame={a}:end_frame={b},setpts=N/({FPS}*TB)'
    if os.path.exists(FONT):
        lab = esc_text(f'seam {k}  {lab_a} > {lab_b}  ({seam_f / FPS:.3f}s, film f{seam_f})')
        box = f"fontfile={FONT}:fontsize=30:fontcolor=white:box=1:boxcolor=black@0.6:boxborderw=6"
        vf += (f",drawtext={box}:x=20:y=20:text='{lab}'"
               f",drawtext={box}:x=20:y=64:text='film f%{{eif\\:n+{a}\\:d}}'"
               f",drawtext={box}:fontcolor=yellow:x=20:y=108:text='BEFORE seam':enable='lt(n,{seam_f - a})'"
               f",drawtext={box}:fontcolor=red:x=20:y=108:text='AFTER seam':enable='gte(n,{seam_f - a})'")
    vf += f',setpts=4*PTS,fps={FPS}'
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', film, '-vf', vf, '-an', '-c:v', 'libx264',
                    '-preset', 'medium', '-crf', str(crf), '-pix_fmt', 'yuv420p', '-movflags', '+faststart', dst],
                   check=True)
    return (b - a) * 4


# ---------------------------------------------------------------- 검사

def verify_against_raw(film, segs):
    """조각마다 첫·끝 프레임이 원본의 그 프레임인지: 앞뒤 원본 프레임보다 평균제곱차가 작아야 함."""
    film_idx = []
    for s in segs:
        film_idx += [s['film_start_frame'], s['film_end_frame'] - 1]
    ff = grab_frames(film, film_idx)
    res, ok = [], True
    for s in segs:
        n = s['raw_frames']
        want = {}
        for where, fidx, ridx in (('첫', s['film_start_frame'], s['kept'][0]),
                                  ('끝', s['film_end_frame'] - 1, s['kept'][-1])):
            want[(where, fidx)] = [r for r in (ridx - 1, ridx, ridx + 1) if 0 <= r < n]
        raw_need = sorted({r for v in want.values() for r in v})
        rf = grab_frames(s['raw'], raw_need)
        for (where, fidx), cands in want.items():
            ridx = s['kept'][0] if where == '첫' else s['kept'][-1]
            mse = {r: float(((ff[fidx].astype(np.float32) - rf[r].astype(np.float32)) ** 2).mean()) for r in cands}
            others = [v for r, v in mse.items() if r != ridx]
            margin = (min(others) / max(mse[ridx], 1e-6)) if others else float('inf')
            good = bool(mse[ridx] <= min(mse.values()) + 1e-9)
            ok &= good
            res.append(dict(label=s['label'], where=where, film_frame=fidx, raw_frame=ridx,
                            mse=round(mse[ridx], 2), neighbor_mse=round(min(others), 2) if others else None,
                            margin=round(margin, 2), ok=good, weak=bool(good and margin < 1.1)))
    return ok, res


def main():
    ap = argparse.ArgumentParser(description='4K 원본 → 1080p 최종 편집본(크로스페이드 없음)')
    ap.add_argument('--trims', required=True, help='자르기 목록 CSV(raw,in_s,out_s,label[,plan_t0,ff_s,ff_x])')
    ap.add_argument('--out', required=True, help='출력 mp4')
    g = ap.add_mutually_exclusive_group()
    g.add_argument('--dehalo', type=float, default=0.0, help='unsharp=5:5:-값:5:5:0 (예: 0.2, 0.35)')
    g.add_argument('--clamp', type=float, default=0.0, help='윤곽 넘침 자르기 흐림 σ (권장 0.8)')
    ap.add_argument('--crf', type=int, default=16)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--no-segments', action='store_true', help='조각별 파일을 만들지 않음')
    ap.add_argument('--no-seam-clips', action='store_true', help='이음새 4배 느린 영상을 만들지 않음')
    ap.add_argument('--no-verify', action='store_true', help='원본 프레임 대조 검사 생략')
    a = ap.parse_args()

    t_start = time.time()
    segs = load_trims(a.trims)
    stem = os.path.splitext(a.out)[0]
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    total = segs[-1]['film_end_frame']
    print(f'조각 {len(segs)}개, 합계 {total}프레임 = {total / FPS:.3f}초')
    for s in segs:
        ff = f', 빨리감기 {s["ff_s"]}초 {s["ff_x"]}배→1배' if s['ff_n'] and s['ff_x'] > 1 else ''
        print(f'  {s["index"]:2d}. {s["label"]:<10} {os.path.basename(s["raw"])} 프레임 {s["in_frame"]}~{s["out_frame"] - 1}'
              f' ({s["in_frame"] / FPS:.3f}~{s["out_frame"] / FPS:.3f}초) → {len(s["kept"])}장{ff}'
              f' | 영상 {s["film_start_frame"] / FPS:.3f}~{s["film_end_frame"] / FPS:.3f}초')
        for nt in s['notes']:
            print(f'      주의: {nt}')

    # 1) 한 번만 인코딩: 모든 조각 → concat → 출력. 이음새 위치에 키프레임을 강제한다.
    graph = build_graph(segs, a.dehalo, a.clamp)
    inputs = []
    for s in segs:
        inputs += ['-i', s['raw']]
    seams = [s['film_start_frame'] for s in segs[1:]]
    kf = ['-force_key_frames', ','.join(f'{(f - 0.25) / FPS:.6f}' for f in seams)] if seams else []
    cmd = ['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', graph, '-map', '[out]',
           *enc_args(a.crf, a.preset), *kf, a.out]
    t0 = time.time()
    subprocess.run(cmd, check=True)
    print(f'인코딩 완료: {a.out} ({time.time() - t0:.0f}초)')

    # 2) 검사: 형식·프레임 수·오디오
    checks = []
    info = probe(a.out)
    md5 = frame_md5s(a.out)
    checks.append(('해상도 1920×1080', (info['width'], info['height']) == (OUT_W, OUT_H), f'{info["width"]}×{info["height"]}'))
    checks.append(('24fps', info['fps_str'] == f'{FPS}/1', info['fps_str']))
    checks.append(('yuv420p', info['pix_fmt'] == 'yuv420p', info['pix_fmt']))
    checks.append(('오디오 없음', not info['has_audio'], '오디오 있음' if info['has_audio'] else '없음'))
    checks.append(('프레임 수 = 조각 합', len(md5) == total, f'디코드 {len(md5)} / 조각 합 {total}'))
    checks.append(('길이', abs(info['duration'] - total / FPS) < 0.5 / FPS, f'{info["duration"]:.4f}초'))
    # 색 표시 정보: 원본(지금까지 Omni 4K는 smpte170m 행렬·tv 범위)과 같아야 재생기에서 색이 그대로 보인다
    raw_colors = {json.dumps(s['raw_info']['color'], sort_keys=True) for s in segs}
    same_color = len(raw_colors) == 1 and info['color'] == segs[0]['raw_info']['color']
    checks.append(('색 표시 정보 = 원본', same_color,
                   '/'.join(info['color'][k] for k in COLOR_KEYS)
                   + ('' if len(raw_colors) == 1 else f' (원본끼리 다름: {len(raw_colors)}가지)')))

    # 3) 조각별 파일: 완성본에서 이음새 키프레임 기준으로 재인코딩 없이 잘라 냄 → 프레임 md5가 같아야 함
    seg_dir = stem + '_segments'
    if not a.no_segments:
        os.makedirs(seg_dir, exist_ok=True)
        for s in segs:
            safe = re.sub(r'[^\w.-]+', '_', s['label'])
            dst = os.path.join(seg_dir, f'{s["index"]:02d}_{safe}.mp4')
            n = len(s['kept'])
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{s["film_start_frame"] / FPS:.6f}', '-i', a.out,
                            '-map', '0:v:0', '-frames:v', str(n), '-c', 'copy', '-an', '-movflags', '+faststart', dst],
                           check=True)
            got = frame_md5s(dst)
            same = got == md5[s['film_start_frame']:s['film_end_frame']]
            s['file'] = dst
            checks.append((f'조각 파일 {s["index"]:02d} {s["label"]} = 완성본 그 구간', same,
                           f'{len(got)}프레임' + ('' if same else ' (프레임이 다름)')))

    # 4) 원본 대조(프레임 정확도·크로스페이드 없음)
    vres = []
    if not a.no_verify:
        t0 = time.time()
        ok, vres = verify_against_raw(a.out, segs)
        weak = [r for r in vres if r['weak']]
        checks.append(('조각 첫·끝 프레임 = 원본의 그 프레임', ok,
                       f'{sum(r["ok"] for r in vres)}/{len(vres)} 일치' + (f', 구분 약함 {len(weak)}곳(움직임 아주 작음)' if weak else '')
                       + f' ({time.time() - t0:.0f}초)'))
        for r in vres:
            mark = '일치' if r['ok'] else '어긋남'
            print(f'    {r["label"]:<10} {r["where"]} 프레임: 영상 f{r["film_frame"]} ↔ 원본 f{r["raw_frame"]} '
                  f'MSE {r["mse"]} (앞뒤 프레임 {r["neighbor_mse"]}, {r["margin"]}배) {mark}')

    # 5) 이음새 확인 영상
    seam_list = []
    seam_dir = stem + '_seams'
    for k, s in enumerate(segs[1:], 1):
        prev = segs[k - 1]
        item = dict(index=k, frame=s['film_start_frame'], time_s=round(s['film_start_frame'] / FPS, 4),
                    before=prev['label'], after=s['label'])
        if not a.no_seam_clips:
            os.makedirs(seam_dir, exist_ok=True)
            safe = re.sub(r'[^\w.-]+', '_', f'{prev["label"]}-{s["label"]}')
            dst = os.path.join(seam_dir, f'seam{k}_{safe}_slow4x.mp4')
            want = seam_clip(a.out, total, s['film_start_frame'], k, prev['label'], s['label'], dst, a.crf)
            got = count_packets(dst)
            checks.append((f'이음새 {k} 느린 영상', got == want, f'{got}프레임 ({got / FPS:.2f}초)'))
            item['slow_clip'] = dst
        seam_list.append(item)

    all_ok = all(c[1] for c in checks)
    print('검사')
    for name, good, detail in checks:
        print(f'  [{"통과" if good else "실패"}] {name}: {detail}')
    for it in seam_list:
        print(f'  이음새 {it["index"]}: {it["before"]} → {it["after"]} 영상 {it["time_s"]:.3f}초 (프레임 {it["frame"]})')

    doc = dict(film=a.out, frames=total, seconds=round(total / FPS, 4), fps=FPS, trims=a.trims,
               color=info['color'],
               settings=dict(scale='1920:1080 lanczos', dehalo_unsharp=a.dehalo or None, clamp_sigma=a.clamp or None,
                             crf=a.crf, preset=a.preset, audio=False, crossfade=False),
               segments=[dict(index=s['index'], label=s['label'], raw=s['raw'], raw_frames=s['raw_frames'],
                              in_frame=s['in_frame'], out_frame=s['out_frame'], frames=len(s['kept']),
                              ff_s=s['ff_s'] or None, ff_x=s['ff_x'] if s['ff_n'] else None,
                              kept=s['kept'] if s['ff_n'] and s['ff_x'] > 1 else None,
                              plan_t0=s['plan_t0'], film_start_frame=s['film_start_frame'],
                              film_end_frame=s['film_end_frame'], film_start_s=round(s['film_start_frame'] / FPS, 4),
                              film_end_s=round(s['film_end_frame'] / FPS, 4), file=s.get('file'),
                              extra=s['extra'] or None, notes=s['notes'])
                         for s in segs],
               seams=seam_list, verify=vres,
               checks=[dict(name=n, ok=bool(g), detail=d) for n, g, d in checks], all_ok=all_ok,
               seconds_taken=round(time.time() - t_start, 1))
    with open(stem + '.edit.json', 'w', encoding='utf-8') as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
    print(f'기록: {stem}.edit.json  (전체 {time.time() - t_start:.0f}초)')
    print('결과: ' + ('모든 검사 통과' if all_ok else '실패한 검사가 있음'))
    sys.exit(0 if all_ok else 1)


if __name__ == '__main__':
    main()
