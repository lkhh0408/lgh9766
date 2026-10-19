"""큰 해상도(4K판) 마감: finish.py와 같은 자르기 목록·필터·인코더 설정으로 조각을 하나씩 인코딩한 뒤,
다시 압축하지 않고(-c copy) 이어 붙인다. 무료(로컬 계산만 함).

finish.py는 모든 조각을 한 번에 열어 한 번만 인코딩한다. 4K에서는 조각 24개를 동시에 디코딩·필터링하느라
메모리가 모자라 ffmpeg가 강제 종료됐다(SIGKILL). 여기서는 조각마다 따로 인코딩하므로 메모리는 조각 하나 분량이다.
조각마다 첫 프레임이 키프레임이 되므로 이음새 위치에 키프레임을 넣는 finish.py와 결과 구조가 같다.

검사: 해상도·fps·프레임 수(조각 합과 같은지)·오디오 없음·색 표시 정보, 그리고 같은 목록으로 만든 1080p판과
프레임을 대조한다(4K판을 1080p로 줄인 프레임이 1080p판의 같은 번호 프레임과 가장 닮았는지, 이음새마다 앞뒤 확인).

사용(저장소 루트): python3 work/scripts/finish_chunked.py --trims 자르기.csv --out 4K판.mp4 --size 3840x2160 \
                    --clamp 1.6 --crf 18 --maxrate 45 [--ref-1080 1080p판.mp4]
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile
import time

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finish as F  # noqa: E402


def encode_piece(s, k, out, a):
    kept = s['kept']
    if kept == list(range(kept[0], kept[-1] + 1)):
        cut = f'trim=start_frame={kept[0]}:end_frame={kept[-1] + 1}'
    else:
        cut = f"select='{F.select_expr(kept)}'"
    graph = (f'[0:v]{cut},setpts=N/({F.FPS}*TB),scale={F.OUT_W}:{F.OUT_H}:flags=lanczos,setsar=1[s0];'
             + F.post_filter('s0', 'c0', 0, a.dehalo, a.clamp))
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', s['raw'], '-filter_complex', graph, '-map', '[c0]',
                    *F.enc_args(a.crf, a.preset, a.maxrate), out], check=True)


def frames_at(path, idx, size=(960, 540)):
    """idx 번호 프레임들(회색조, 작게)을 순서대로 읽는다."""
    want = sorted(set(idx))
    cap = cv2.VideoCapture(path)
    out, i = {}, 0
    while want and i <= want[-1]:
        ok, f = cap.read()
        if not ok:
            break
        if i in want:
            out[i] = cv2.cvtColor(cv2.resize(f, size, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY).astype(np.float32)
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trims', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', default='3840x2160')
    ap.add_argument('--clamp', type=float, default=0.0)
    ap.add_argument('--dehalo', type=float, default=0.0)
    ap.add_argument('--crf', type=int, default=18)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--maxrate', type=int)
    ap.add_argument('--ref-1080', help='같은 자르기 목록으로 만든 1080p판(프레임 대조용)')
    a = ap.parse_args()
    F.OUT_W, F.OUT_H = (int(v) for v in a.size.lower().split('x'))
    segs = F.load_trims(a.trims)
    total = sum(len(s['kept']) for s in segs)
    print(f'조각 {len(segs)}개, 합계 {total}프레임 = {total / F.FPS:.3f}초, 출력 {F.OUT_W}×{F.OUT_H}')
    t0 = time.time()
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(a.out))) as tmp:
        parts = []
        for k, s in enumerate(segs):
            p = os.path.join(tmp, f'{k:02d}.mp4')
            encode_piece(s, k, p, a)
            n = F.count_packets(p)
            print(f'  {k + 1:2d}. {s["label"]:<8} {os.path.basename(s["raw"])} → {n}장 (기대 {len(s["kept"])})', flush=True)
            if n != len(s['kept']):
                sys.exit(f'프레임 수가 다름: 조각 {k + 1}')
            parts.append(p)
        lst = os.path.join(tmp, 'list.txt')
        with open(lst, 'w', encoding='utf-8') as f:
            f.writelines(f"file '{p}'\n" for p in parts)
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                        '-movflags', '+faststart', a.out], check=True)
    print(f'인코딩·이어 붙이기 완료: {a.out} ({time.time() - t0:.0f}초)')

    info = F.probe(a.out)
    frames = F.count_packets(a.out)
    want_color = F.probe(segs[0]['raw'])['color']
    checks = [(f'해상도 {F.OUT_W}×{F.OUT_H}', (info['width'], info['height']) == (F.OUT_W, F.OUT_H), f'{info["width"]}×{info["height"]}'),
              ('24fps', info['fps_str'] == f'{F.FPS}/1', info['fps_str']),
              ('yuv420p', info['pix_fmt'] == 'yuv420p', info['pix_fmt']),
              ('오디오 없음', not info['has_audio'], '오디오 있음' if info['has_audio'] else '없음'),
              ('프레임 수 = 조각 합', frames == total, f'{frames} / {total}'),
              ('색 표시 정보 = 원본', info['color'] == want_color, '/'.join(info['color'].values()))]
    if a.ref_1080:
        # 이음새마다 앞뒤 프레임과 영상 처음·끝: 4K판을 줄인 프레임이 1080p판 같은 번호 프레임과 가장 닮았는지(±1 비교)
        bounds, acc = [], 0
        for s in segs:
            bounds += [acc, acc + len(s['kept']) - 1]
            acc += len(s['kept'])
        idx = sorted(set(b + d for b in bounds for d in (-1, 0, 1) if 0 <= b + d < total))
        A, B = frames_at(a.out, idx), frames_at(a.ref_1080, idx)
        ok = 0
        for b in bounds:
            d0 = np.abs(A[b] - B[b]).mean()
            dn = min(np.abs(A[b] - B[j]).mean() for j in (b - 1, b + 1) if j in B)
            ok += d0 < dn
        checks.append(('1080p판과 프레임 대조(이음새 앞뒤)', ok == len(bounds), f'{ok}/{len(bounds)} 일치'))
    print('검사')
    for name, good, detail in checks:
        print(f'  [{"통과" if good else "실패"}] {name}: {detail}')
    json.dump(dict(film=a.out, frames=total, seconds=total / F.FPS, size=a.size, clamp_sigma=a.clamp, crf=a.crf,
                   maxrate_mbps=a.maxrate, trims=a.trims, checks=[dict(name=n, ok=bool(g), detail=d) for n, g, d in checks]),
              open(os.path.splitext(a.out)[0] + '.edit.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('결과:', '모든 검사 통과' if all(g for _, g, _ in checks) else '실패한 검사가 있음')


if __name__ == '__main__':
    main()
