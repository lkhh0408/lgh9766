"""생성 클립을 크로스페이드 없이 이어 붙인다(오디오 제거, 24fps 고정, 1080p H.264).

다음 클립의 첫 프레임은 앞 클립의 마지막 프레임과 같은 이미지이므로 중복 정지를 막기 위해 버린다.
사용: python3 work/scripts/stitch.py <출력.mp4> <클립1.mp4> <클립2.mp4> ... [--seam-slow 폴더]
--seam-slow 를 주면 각 연결부 앞뒤 1초를 0.25배속(프레임 반복, 보간 없음)으로 따로 저장한다.
"""
import argparse
import os
import subprocess


def nframes(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-count_packets',
                          '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', path],
                         capture_output=True, text=True, check=True).stdout
    return int(out.strip())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('out')
    ap.add_argument('clips', nargs='+')
    ap.add_argument('--seam-slow')
    a = ap.parse_args()
    inputs, parts = [], []
    for k, c in enumerate(a.clips):
        inputs += ['-i', c]
        start = 0 if k == 0 else 1
        parts.append(f'[{k}:v]trim=start_frame={start},setpts=PTS-STARTPTS,'
                     f'scale=1920:1080:flags=lanczos,fps=24,format=yuv420p[v{k}]')
    graph = ';'.join(parts) + ';' + ''.join(f'[v{k}]' for k in range(len(a.clips))) + \
        f'concat=n={len(a.clips)}:v=1:a=0[out]'
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    subprocess.run(['ffmpeg', '-y', '-v', 'error', *inputs, '-filter_complex', graph, '-map', '[out]',
                    '-an', '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-r', '24',
                    '-movflags', '+faststart', a.out], check=True)
    print('저장:', a.out, nframes(a.out), 'frames')
    if a.seam_slow:
        os.makedirs(a.seam_slow, exist_ok=True)
        pos = 0
        for k, c in enumerate(a.clips[:-1]):
            pos += nframes(c) - (0 if k == 0 else 1)
            t = pos / 24
            dst = os.path.join(a.seam_slow, f'seam{k + 1}_slow4x.mp4')
            subprocess.run(['ffmpeg', '-y', '-v', 'error', '-ss', f'{max(t - 1, 0):.3f}', '-t', '2',
                            '-i', a.out, '-vf', 'setpts=4*PTS', '-r', '24', '-an', '-c:v', 'libx264',
                            '-crf', '16', dst], check=True)
            print(f'연결부 {k + 1}: {t:.3f}s → {dst}')


if __name__ == '__main__':
    main()
