"""GitHub 한도(파일당 100MB)를 넘는 영상을 90MB 조각으로 나누고 원본은 git에서 제외한다.

사용: python3 work/scripts/split_large.py <폴더> [<폴더> ...]
- 95MB를 넘는 .mp4마다 <이름>.mp4.part00, .part01 ... 을 만들고, 원본 경로를 .gitignore에 추가한다.
- 합치는 방법
  Windows: copy /b 이름.mp4.part00 + 이름.mp4.part01 이름.mp4
  macOS·Linux: cat 이름.mp4.part* > 이름.mp4
"""
import glob
import hashlib
import os
import sys

LIMIT = 95 * 1024 * 1024
PART = 90 * 1024 * 1024
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))


def main():
    ignore = os.path.join(ROOT, '.gitignore')
    listed = open(ignore, encoding='utf-8').read().splitlines() if os.path.exists(ignore) else []
    for d in sys.argv[1:]:
        for path in sorted(glob.glob(os.path.join(d, '*.mp4'))):
            if os.path.getsize(path) <= LIMIT:
                continue
            for old in glob.glob(path + '.part*'):
                os.remove(old)
            sha = hashlib.sha256()
            with open(path, 'rb') as f:
                k = 0
                while True:
                    chunk = f.read(PART)
                    if not chunk:
                        break
                    sha.update(chunk)
                    with open(f'{path}.part{k:02d}', 'wb') as out:
                        out.write(chunk)
                    k += 1
            with open(path + '.sha256', 'w') as f:
                f.write(f'{sha.hexdigest()}  {os.path.basename(path)}\n')
            rel = os.path.relpath(os.path.abspath(path), ROOT)
            if rel not in listed:
                listed.append(rel)
            print(f'{rel}: {os.path.getsize(path) / 1e6:.1f}MB → {k}조각')
    with open(ignore, 'w', encoding='utf-8') as f:
        f.write('\n'.join(listed).strip() + '\n')


if __name__ == '__main__':
    main()
