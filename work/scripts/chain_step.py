"""연쇄 클립 한 단계: 4K 생성 → 1080p 축소 → 측정 → 마지막 프레임 추출.

사용(저장소 루트):
  python3 work/scripts/chain_step.py --dir work/test2 --name C2 \
      --first work/test2/keyframes/C1_last.png --last 040_83Tower.png [--cap 30.44]
결과: <dir>/raw/<name>.mp4(4K 원본), <dir>/raw/<name>_1080p.mp4(축소본),
      <dir>/keyframes/<name>_last.png(1080p 마지막 프레임), <dir>/check/ 측정 결과
"""
import argparse
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def run(cmd):
    print('$', ' '.join(cmd), flush=True)
    subprocess.run(cmd, check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dir', required=True)
    ap.add_argument('--name', required=True)
    ap.add_argument('--first', required=True)
    ap.add_argument('--last')
    ap.add_argument('--resolution', default='4k')
    ap.add_argument('--model', default='veo-3.1-fast-generate-preview')
    ap.add_argument('--cap', type=float, default=float(os.environ.get('COST_CAP_USD', 30)))
    a = ap.parse_args()
    raw = os.path.join(a.dir, 'raw', f'{a.name}.mp4')
    small = os.path.join(a.dir, 'raw', f'{a.name}_1080p.mp4')
    last = os.path.join(a.dir, 'keyframes', f'{a.name}_last.png')
    prompts = os.path.join(a.dir, 'prompts')
    with open(os.path.join(prompts, 'negative.txt'), encoding='utf-8') as f:
        negative = f.read().strip()
    cmd = [sys.executable, '-B', os.path.join(HERE, 'gen_api.py'), '--cap', str(a.cap), 'video',
           '--model', a.model, '--resolution', a.resolution, '--out', raw, '--first', a.first,
           '--prompt-file', os.path.join(prompts, f'{a.name.split("_")[0]}.txt'), '--negative', negative]
    if a.last:
        cmd += ['--last', a.last]
    run(cmd)
    run(['ffmpeg', '-y', '-v', 'error', '-i', raw, '-vf', 'scale=1920:1080:flags=lanczos', '-an',
         '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', small])
    os.makedirs(os.path.dirname(last), exist_ok=True)
    run([sys.executable, '-B', os.path.join(HERE, 'last_frame.py'), small, last])
    check = [sys.executable, '-B', os.path.join(HERE, 'clip_check.py'), small, '--first', a.first,
             '--out', os.path.join(a.dir, 'check')]
    if a.last:
        check += ['--last', a.last]
    run(check)


if __name__ == '__main__':
    main()
