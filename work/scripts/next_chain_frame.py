"""다음 묶음의 첫 장면으로 쓸 4K 프레임을 원본에서 정확히 꺼내 무손실 PNG로 저장한다. 무료(로컬 계산만 함).

하는 일
1. 4K 원본(mp4)의 프레임을 처음부터 끝까지 실제로 디코드해 진짜 프레임 수를 센다.
   (머리 정보의 프레임 수·길이는 틀릴 수 있으므로 '진짜 마지막 프레임'은 디코드한 수로 정한다.)
2. 묶음 확인: 연장 결과 파일에는 묶음 전체(예: 16초)가 들어 있고, 연장은 앞 영상의 마지막 몇 프레임도 고친다.
   그래서 같은 폴더에 이 파일을 이어 만든 더 긴 연장 파일(옆 .json의 extend_from이 이 파일)이 있으면
   그 파일의 끝이 진짜 묶음 끝이다. 이런 경우 알려 주고 멈춘다(--allow-partial이면 계속).
3. 고른 프레임 하나를 원본 크기 그대로(보통 3840×2160) RGB 8비트 PNG로 저장한다. 크기 변경 없음.
   색 변환은 원본의 색 표시 정보(Omni 4K는 smpte170m 행렬, tv 범위)를 그대로 따른다.
4. 검사: 저장한 PNG가 같은 방법으로 디코드한 그 프레임과 화소 하나까지 같은지, 앞뒤 프레임과는 다른지 확인한다.
5. md5(PNG 파일, 화소 데이터)와 프레임 번호·시각을 출력하고, 같은 이름의 .json에 기록한다.

프레임 고르기(--at)
  last        진짜 마지막 프레임(기본)
  -1.0        마지막 프레임보다 1초(24프레임) 앞. 겹침 재시작에 쓰는 프레임(장면계획.md: N = 전체 프레임 수 − 25)
  15.5        처음부터 15.5초 위치의 프레임(프레임 경계로 반올림)
  f359        359번 프레임(0부터 셈). -f24 = 마지막 프레임보다 24프레임 앞

사용(저장소 루트)
  python3 work/scripts/next_chain_frame.py work/final/A/raw/A12_4k.mp4 --at -1.0 \
      --out work/final/B/keyframes/A_overlap.png
  python3 work/scripts/next_chain_frame.py work/final/A/raw/A12_4k.mp4 --out work/final/B/keyframes/A_last.png
  선택: --also-1080 (같은 프레임의 1920×1080 PNG도 저장, 4K 업로드가 거부될 때 대신 씀)
        --allow-partial (더 긴 연장 파일이 있어도 이 파일에서 꺼냄)  --overwrite

결과: <출력>.png, <출력>.json(원본·프레임 번호·시각·md5·색 변환), 선택 시 <출력>_1080.png
종료 코드: 0 정상, 1 검사 실패, 2 더 긴 연장 파일이 있어 멈춤, 3 출력 파일이 이미 있음
"""
import argparse
import datetime as dt
import glob
import hashlib
import json
import os
import re
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from finish import FPS, count_packets, probe  # noqa: E402

# ffprobe 색 행렬 이름 → swscale in_color_matrix 이름
MATRIX = {'smpte170m': 'bt601', 'bt470bg': 'bt601', 'bt709': 'bt709', 'smpte240m': 'smpte240m',
          'bt2020nc': 'bt2020', 'bt2020c': 'bt2020', 'fcc': 'fcc'}


def md5_file(path, chunk=1 << 22):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for b in iter(lambda: f.read(chunk), b''):
            h.update(b)
    return h.hexdigest()


def decoded_count(path):
    """실제로 디코드되는 프레임 수(시간이 좀 걸림: 4K 16초에 수십 초)."""
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_frames',
                          '-show_entries', 'stream=nb_read_frames', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip().split(',')[0])


def parse_at(spec, n):
    """--at 값 → 프레임 번호(0~n-1)."""
    s = spec.strip().lower()
    if s in ('last', 'end', '끝'):
        return n - 1
    m = re.fullmatch(r'(-?)f(\d+)|(-?)(\d+)f', s)
    if m:
        neg = (m.group(1) or m.group(3)) == '-'
        k = int(m.group(2) or m.group(4))
        return n - 1 - k if neg else k
    x = float(s)
    k = int(round(abs(x) * FPS))
    if abs(abs(x) * FPS - k) > 0.01:
        print(f'주의: {spec}초는 프레임 경계가 아니라 {k}프레임으로 반올림함')
    return n - 1 - k if x < 0 or s.startswith('-') else k


def color_filter(info):
    """원본 색 표시 정보에 맞춘 RGB 변환 필터(정확한 반올림, 크로마 전체 보간)."""
    c = info['color']
    mat = MATRIX.get(c['color_space'])
    note = None
    if mat is None:
        mat = 'bt709' if info['height'] >= 720 else 'bt601'
        note = f'색 행렬 정보가 없음({c["color_space"]}): {mat}로 가정'
    rng = 'pc' if c['color_range'] in ('pc', 'jpeg') else 'tv'
    return (f'scale=in_color_matrix={mat}:in_range={rng}:out_range=pc:'
            f'flags=accurate_rnd+full_chroma_int+bitexact'), mat, rng, note


def decode_rgb(path, indices, vf_color, w, h):
    """지정한 프레임들을 원본 크기 RGB24로 디코드. {번호: (h, w, 3) 배열}."""
    idx = sorted(set(indices))
    expr = '+'.join(f'eq(n\\,{i})' for i in idx)
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-map', '0:v:0',
                          '-vf', f'select={expr},{vf_color},format=rgb24', '-fps_mode', 'passthrough',
                          '-frames:v', str(len(idx)), '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    per = w * h * 3
    if len(out) != per * len(idx):
        raise RuntimeError(f'프레임 {idx}를 디코드했는데 {len(out) / per:.2f}장 분량만 나옴')
    arr = np.frombuffer(out, np.uint8).reshape(len(idx), h, w, 3)
    return {i: arr[k] for k, i in enumerate(idx)}


def read_png_rgb(path, w, h):
    """PNG를 ffmpeg로 다시 읽어 RGB24 배열로(저장이 손실 없이 됐는지 확인용)."""
    out = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, np.uint8).reshape(h, w, 3)


def find_longer_chain(raw):
    """같은 폴더의 .json 중 extend_from이 이 원본의 .json을 가리키는 것(= 이어 만든 더 긴 연장 파일)."""
    me = os.path.normpath(os.path.abspath(os.path.splitext(raw)[0] + '.json'))
    found = []
    for js in glob.glob(os.path.join(os.path.dirname(os.path.abspath(raw)), '*.json')):
        try:
            d = json.load(open(js, encoding='utf-8'))
        except (OSError, ValueError):
            continue
        ef = d.get('extend_from') if isinstance(d, dict) else None
        if not ef:
            continue
        cand = [ef, os.path.join(os.getcwd(), ef), os.path.join(os.path.dirname(js), os.path.basename(ef))]
        if any(os.path.normpath(os.path.abspath(c)) == me for c in cand):
            mp4 = os.path.splitext(js)[0] + '.mp4'
            found.append(mp4 if os.path.exists(mp4) else js)
    return found


def main():
    ap = argparse.ArgumentParser(description='다음 묶음 첫 장면용 4K 프레임을 무손실 PNG로 꺼냄')
    ap.add_argument('raw', help='4K 원본 mp4(묶음 전체가 든 마지막 연장 결과)')
    ap.add_argument('--out', required=True, help='출력 PNG')
    ap.add_argument('--at', default='last', help="last(기본), -1.0(끝 1초 앞), 15.5(초), f359(프레임), -f24")
    ap.add_argument('--also-1080', action='store_true', help='같은 프레임의 1920×1080 lanczos PNG도 저장')
    ap.add_argument('--allow-partial', action='store_true', help='더 긴 연장 파일이 있어도 계속')
    ap.add_argument('--overwrite', action='store_true')
    a = ap.parse_args()

    if not a.out.lower().endswith('.png'):
        raise SystemExit('--out 은 .png 여야 함(무손실)')
    stem = os.path.splitext(a.out)[0]
    outs = [a.out, stem + '.json'] + ([stem + '_1080.png'] if a.also_1080 else [])
    if not a.overwrite and any(os.path.exists(p) for p in outs):
        print(f'출력 파일이 이미 있음: {[p for p in outs if os.path.exists(p)]} (--overwrite로 덮어씀)')
        sys.exit(3)

    # 1) 묶음 확인
    longer = find_longer_chain(a.raw)
    side = os.path.splitext(a.raw)[0] + '.json'
    meta = json.load(open(side, encoding='utf-8')) if os.path.exists(side) else None
    if longer:
        print(f'주의: 이 파일을 이어 만든 더 긴 연장 결과가 있음: {longer}')
        print('      연장 결과에는 묶음 전체가 들어 있고 앞 영상의 끝 몇 프레임도 고쳐지므로, 그 파일에서 꺼내야 함.')
        if not a.allow_partial:
            sys.exit(2)

    # 2) 진짜 프레임 수
    info = probe(a.raw)
    if abs(info['fps'] - FPS) > 0.01:
        raise SystemExit(f'{a.raw}: {info["fps_str"]} fps. 24fps 원본만 받음')
    n_pk = count_packets(a.raw)
    print(f'{a.raw}: {info["width"]}×{info["height"]} {info["fps_str"]}fps, 프레임 세는 중(전체 디코드)...')
    n = decoded_count(a.raw)
    warn = []
    if n != n_pk or (info['nb_frames'] and n != info['nb_frames']):
        warn.append(f'프레임 수가 서로 다름: 디코드 {n}, 패킷 {n_pk}, 머리 정보 {info["nb_frames"]} → 디코드 수를 씀')
    if abs(info['duration'] - n / FPS) > 1.5 / FPS:
        warn.append(f'머리 정보 길이 {info["duration"]:.3f}초 ≠ 디코드 {n / FPS:.3f}초 → 디코드 기준')
    if meta:
        exp = meta.get('chain_seconds') or meta.get('expected_seconds')
        if exp and abs(float(exp) - n / FPS) > 0.5:
            warn.append(f'옆 .json의 묶음 길이 {exp}초와 실제 {n / FPS:.3f}초가 다름')
    for w_ in warn:
        print('주의:', w_)

    idx = parse_at(a.at, n)
    if not 0 <= idx < n:
        raise SystemExit(f'--at {a.at} → 프레임 {idx}: 범위 0~{n - 1} 밖')

    # 3) 저장: 원본 크기 그대로, 색 표시 정보대로 RGB 변환
    vf_color, mat, rng, cnote = color_filter(info)
    if cnote:
        print('주의:', cnote)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)) or '.', exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.raw, '-map', '0:v:0',
                    '-vf', f'select=eq(n\\,{idx}),{vf_color},format=rgb24', '-fps_mode', 'passthrough',
                    '-frames:v', '1', '-pix_fmt', 'rgb24', '-compression_level', '6', a.out], check=True)

    # 4) 검사: 같은 방법으로 디코드한 그 프레임과 화소까지 같고, 앞뒤 프레임과는 달라야 함
    w, h = info['width'], info['height']
    near = [i for i in (idx - 1, idx, idx + 1) if 0 <= i < n]
    ref = decode_rgb(a.raw, near, vf_color, w, h)
    png = read_png_rgb(a.out, w, h)
    exact = bool(np.array_equal(png, ref[idx]))
    diffs = {i: float(np.abs(png.astype(np.int16) - ref[i].astype(np.int16)).mean()) for i in near}
    distinct = all(diffs[i] > 0 for i in near if i != idx)
    ok = exact and distinct and png.shape == (h, w, 3)
    px_md5 = hashlib.md5(png.tobytes()).hexdigest()
    file_md5 = md5_file(a.out)
    t = idx / FPS

    small = None
    if a.also_1080:
        small = stem + '_1080.png'
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.out, '-vf', 'scale=1920:1080:flags=lanczos',
                        '-pix_fmt', 'rgb24', small], check=True)

    from_end = n - 1 - idx
    print(f'저장: {a.out}  {w}×{h} RGB 8비트 PNG ({os.path.getsize(a.out) / 1e6:.1f}MB)')
    print(f'  프레임 {idx} / 전체 {n}장(0~{n - 1}), 시각 {t:.4f}초 (pts {idx}/{FPS}), '
          f'마지막 프레임보다 {from_end}프레임({from_end / FPS:.3f}초) 앞')
    print(f'  md5(파일) {file_md5}')
    print(f'  md5(화소 RGB) {px_md5}')
    print(f'  색 변환: {mat} 행렬, {rng} 범위 → RGB 전체 범위')
    print(f'  검사: 디코드한 프레임 {idx}와 화소 일치 {"예" if exact else "아니오"}; 앞뒤 프레임과 평균 차 '
          + ', '.join(f'f{i}: {d:.2f}' for i, d in diffs.items() if i != idx))
    if from_end:
        print(f'  겹침 재시작이면: 새 묶음 원본의 0초 ≈ 이 원본의 {t:.3f}초. 이 원본의 남은 {from_end / FPS:.3f}초와 '
              f'새 묶음의 처음 부분이 겹치므로, seam_check·align_to로 자를 곳을 고른다.')
    if small:
        print(f'  1920×1080 대체본: {small} (md5 {md5_file(small)})')

    rec = dict(source=a.raw, source_md5=md5_file(a.raw), source_frames_decoded=n, source_packets=n_pk,
               source_header_frames=info['nb_frames'], source_size=[w, h], source_color=info['color'],
               source_interaction_id=(meta or {}).get('interaction_id'),
               source_extendable=(meta or {}).get('extendable', bool((meta or {}).get('interaction_id'))),
               at=a.at, frame=idx, time_s=round(t, 4), frames_before_end=from_end,
               seconds_before_end=round(from_end / FPS, 4), png=a.out, png_md5=file_md5, pixel_md5=px_md5,
               png_size=[w, h], color_conversion=dict(matrix=mat, in_range=rng, out='rgb24 full range', filter=vf_color),
               pixel_exact=exact, neighbor_mean_abs_diff={str(i): round(d, 3) for i, d in diffs.items() if i != idx},
               png_1080=small, png_1080_md5=md5_file(small) if small else None,
               longer_chain_files=longer or None, warnings=warn or None, ok=ok,
               created_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'))
    with open(stem + '.json', 'w', encoding='utf-8') as f:
        json.dump(rec, f, ensure_ascii=False, indent=1)
    print(f'기록: {stem}.json')
    print('결과: ' + ('정상' if ok else '검사 실패'))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
