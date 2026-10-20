"""완성본 맨 앞에 페이드 인(검은 화면에서 나타남), 맨 끝에 페이드 아웃(검은 화면으로 사라짐)을 넣는다. 무료(로컬 계산만 함).

finish_chunked.py로 만든 완성본은 조각마다 첫 프레임이 키프레임이다. 그래서
- 첫 조각과 마지막 조각만 원본(4K)에서 같은 필터·인코더 설정으로 다시 인코딩하면서 페이드를 넣고,
- 가운데는 완성본에서 다시 압축하지 않고(-c copy) 잘라 와서 이어 붙인다(가운데 화질은 그대로).
검사: 프레임 수, 가운데 프레임이 원래 완성본과 화소까지 같은지, 첫·끝 프레임 밝기, 페이드 경계 앞뒤가 원래와 거의 같은지.

사용(저장소 루트): python3 work/scripts/fade_edges.py --film 완성본.mp4 --trims 자르기.csv --out 결과.mp4 \
                    --size 3840x2160 --clamp 1.6 --crf 18 --maxrate 30 [--fade-in 1.5 --fade-out 2.0]
"""
import argparse
import os
import subprocess
import sys
import tempfile

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import finish as F  # noqa: E402


def encode(s, out, a, fade):
    kept = s['kept']
    if kept == list(range(kept[0], kept[-1] + 1)):
        cut = f'trim=start_frame={kept[0]}:end_frame={kept[-1] + 1}'
    else:
        cut = f"select='{F.select_expr(kept)}'"
    graph = (f'[0:v]{cut},setpts=N/({F.FPS}*TB),scale={F.OUT_W}:{F.OUT_H}:flags=lanczos,setsar=1[s0];'
             + F.post_filter('s0', 'c0', 0, 0, a.clamp) + f';[c0]{fade}[f0]')
    subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', s['raw'], '-filter_complex', graph, '-map', '[f0]',
                    *F.enc_args(a.crf, a.preset, a.maxrate), out], check=True)


def frames(path, idx):
    want, out, i = set(idx), {}, 0
    cap = cv2.VideoCapture(path)
    while len(out) < len(want):
        ok, f = cap.read()
        if not ok:
            break
        if i in want:
            out[i] = f.astype(np.float32)
        i += 1
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--film', required=True)
    ap.add_argument('--trims', required=True)
    ap.add_argument('--out', required=True)
    ap.add_argument('--size', default='3840x2160')
    ap.add_argument('--clamp', type=float, default=0.0)
    ap.add_argument('--crf', type=int, default=18)
    ap.add_argument('--preset', default='slow')
    ap.add_argument('--maxrate', type=int)
    ap.add_argument('--fade-in', type=float, default=1.5)
    ap.add_argument('--fade-out', type=float, default=2.0)
    a = ap.parse_args()
    F.OUT_W, F.OUT_H = (int(v) for v in a.size.lower().split('x'))
    segs = F.load_trims(a.trims)
    n0, nl = len(segs[0]['kept']), len(segs[-1]['kept'])
    total = sum(len(s['kept']) for s in segs)
    assert a.fade_in * F.FPS <= n0 and a.fade_out * F.FPS <= nl, '페이드가 첫·끝 조각보다 김'
    assert F.count_packets(a.film) == total, '완성본 프레임 수가 자르기 목록과 다름'
    with tempfile.TemporaryDirectory(dir=os.path.dirname(os.path.abspath(a.out))) as tmp:
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-i', a.film, '-map', '0:v', '-c', 'copy', '-f', 'segment',
                        '-segment_frames', f'{n0},{total - nl}', '-reset_timestamps', '1',
                        os.path.join(tmp, 'seg%d.mp4')], check=True)
        mid = os.path.join(tmp, 'seg1.mp4')
        assert F.count_packets(mid) == total - n0 - nl, f'가운데 자르기가 키프레임에 맞지 않음: {F.count_packets(mid)}'
        head, tail = os.path.join(tmp, 'head.mp4'), os.path.join(tmp, 'tail.mp4')
        encode(segs[0], head, a, f'fade=t=in:st=0:d={a.fade_in}')
        encode(segs[-1], tail, a, f'fade=t=out:st={nl / F.FPS - a.fade_out:.4f}:d={a.fade_out}')
        lst = os.path.join(tmp, 'list.txt')
        with open(lst, 'w', encoding='utf-8') as f:
            f.writelines(f"file '{p}'\n" for p in (head, mid, tail))
        subprocess.run(['ffmpeg', '-y', '-v', 'error', '-f', 'concat', '-safe', '0', '-i', lst, '-c', 'copy',
                        '-movflags', '+faststart', a.out], check=True)

    got = F.count_packets(a.out)
    fin = int(a.fade_in * F.FPS)
    fout = total - int(a.fade_out * F.FPS)
    idx = [0, fin - 1, fin + 5, n0 - 1, n0, n0 + 500, total - nl - 1, total - nl, fout - 5, total - 1]
    A, B = frames(a.out, idx), frames(a.film, idx)
    d = {i: float(np.abs(A[i] - B[i]).mean()) for i in idx}
    checks = [('프레임 수', got == total, f'{got} / {total}'),
              ('첫 프레임이 검은 화면에 가까움', A[0].mean() < 20, f'평균 밝기 {A[0].mean():.1f}'),
              ('끝 프레임이 검은 화면에 가까움', A[total - 1].mean() < 20, f'평균 밝기 {A[total - 1].mean():.1f}'),
              ('가운데는 원래 완성본과 같음', d[n0] == 0 and d[n0 + 500] == 0 and d[total - nl - 1] == 0,
               f'차이 {d[n0]:.2f}, {d[n0 + 500]:.2f}, {d[total - nl - 1]:.2f}'),
              ('페이드 밖 앞뒤 조각은 원래와 거의 같음', max(d[fin + 5], d[n0 - 1], d[total - nl], d[fout - 5]) < 2.0,
               ', '.join(f'{d[i]:.2f}' for i in (fin + 5, n0 - 1, total - nl, fout - 5)))]
    for name, ok, det in checks:
        print(f'  [{"통과" if ok else "실패"}] {name}: {det}')
    print('결과:', '모든 검사 통과' if all(c[1] for c in checks) else '실패한 검사가 있음')


if __name__ == '__main__':
    main()
