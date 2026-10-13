"""원본 이미지와 생성 영상 프레임의 화질(선명도·세부 묘사) 비교.

측정
- 선명도: 원본 크기(1672x941)로 맞춘 뒤 라플라시안 분산(클수록 선명)
- 고주파 비율: 1920x1080 기준 파워 스펙트럼에서 나이퀴스트 0.67~1.0 구간 에너지 / 0.33~0.67 구간 에너지
  (720p를 1080p로 키운 영상은 0.67 이상 구간이 거의 비어 이 값이 작아진다)
- 재인코딩 손실: 생성 원본 프레임 대비 편집본·사본 프레임의 PSNR
- 확대 비교: 같은 위치를 원본 크기 그대로 잘라 나란히 저장

사용: python3 work/scripts/quality_check.py  (저장소 루트, 결과는 work/test1/quality/)
"""
import os

import cv2
import numpy as np

OUT = 'work/test1/quality'
SRC_SIZE = (1672, 941)


def frames(path, idx):
    cap = cv2.VideoCapture(path)
    n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    want = {i if i >= 0 else n + i for i in idx}
    got, i = {}, 0
    while True:
        ok, f = cap.read()
        if not ok:
            break
        if i in want:
            got[i] = f
        i += 1
    return [got[i if i >= 0 else n + i] for i in idx]


def lap_var(img):
    g = cv2.cvtColor(cv2.resize(img, SRC_SIZE, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


def hf_ratio(img):
    g = cv2.cvtColor(cv2.resize(img, (1920, 1080), interpolation=cv2.INTER_LANCZOS4),
                     cv2.COLOR_BGR2GRAY).astype(np.float64)
    g -= g.mean()
    win = np.outer(np.hanning(g.shape[0]), np.hanning(g.shape[1]))
    p = np.abs(np.fft.fftshift(np.fft.fft2(g * win))) ** 2
    h, w = p.shape
    yy, xx = np.mgrid[0:h, 0:w]
    r = np.maximum(np.abs(yy - h / 2) / (h / 2), np.abs(xx - w / 2) / (w / 2))
    hi = p[(r >= 0.67) & (r < 1.0)].sum()
    mid = p[(r >= 0.33) & (r < 0.67)].sum()
    return float(hi / mid)


def psnr(a, b):
    return float(cv2.PSNR(a, b))


def main():
    os.makedirs(OUT, exist_ok=True)
    rows = []

    def add(name, img):
        rows.append((name, img.shape[1], img.shape[0], lap_var(img), hf_ratio(img)))

    o008, o011 = cv2.imread('008_83Tower.png'), cv2.imread('011_83Tower.png')
    add('원본 008', o008)
    add('원본 011', o011)
    add('키프레임 008ᶜ(재조명·정렬)', cv2.imread('work/test1/keyframes/008c.png'))
    t1 = frames('work/test1/raw/T1_v1.mp4', [0, 96, -1])
    add('T1 1080p 첫 프레임', t1[0])
    add('T1 1080p 4초', t1[1])
    add('T1 1080p 마지막(≈011)', t1[2])
    t720 = frames('work/test1/raw/T1_720_v1.mp4', [0, 96, -1])
    add('T1 720p 첫 프레임', t720[0])
    add('T1 720p 4초', t720[1])
    add('T1 720p 마지막', t720[2])
    t2 = frames('work/test1/raw/T2d_v2.mp4', [0, 96, -1])
    add('T2 1080p 첫 프레임(=T1 마지막)', t2[0])
    add('T2 1080p 4초', t2[1])
    add('T2 1080p 마지막', t2[2])
    add('T2 끝 키프레임(낮 재조명)', cv2.imread('work/test1/keyframes/T2c_v2_last_day.png'))
    add('비교용: 원본 011을 720p로 줄였다 다시 키움',
        cv2.resize(cv2.resize(o011, (1280, 720), interpolation=cv2.INTER_AREA), SRC_SIZE,
                   interpolation=cv2.INTER_LANCZOS4))

    with open(os.path.join(OUT, 'sharpness.csv'), 'w', encoding='utf-8') as f:
        f.write('대상,가로,세로,라플라시안분산,고주파비율\n')
        for r in rows:
            f.write(f'{r[0]},{r[1]},{r[2]},{r[3]:.1f},{r[4]:.4f}\n')
    for r in rows:
        print(f'{r[0]:<32s} {r[1]}x{r[2]}  선명도 {r[3]:8.1f}  고주파비율 {r[4]:.4f}')

    # 재인코딩 손실 (편집본 앞 192프레임 = T1)
    raw = frames('work/test1/raw/T1_v1.mp4', [48, 144])
    ed = frames('work/test1/edit/test1_T1_T2d_1080p.mp4', [48, 144])
    print('편집본(CRF18) vs 생성 원본 PSNR:', [round(psnr(a, b), 2) for a, b in zip(raw, ed)])
    copy = '/tmp/claude-0/-home-user-lgh9766/dc9b2f1e-bb87-5bb9-88b1-7bff31f8376e/scratchpad/test1_T1_T2d_1080p_고화질.mp4'
    if os.path.exists(copy):
        cp = frames(copy, [48, 144])
        print('27MB 사본 vs 생성 원본 PSNR:', [round(psnr(a, b), 2) for a, b in zip(raw, cp)])

    # 확대 비교: 원본 011과 T1 마지막 프레임(011에 맞춰 생성됨)을 원본 크기로 맞춰 같은 위치 자르기
    last = cv2.resize(t1[2], SRC_SIZE, interpolation=cv2.INTER_AREA)
    l720 = cv2.resize(t720[2], SRC_SIZE, interpolation=cv2.INTER_LANCZOS4)
    for name, (x, y, w, h) in {'tower': (700, 120, 420, 300), 'park': (950, 560, 420, 300),
                               'city': (1250, 420, 420, 300)}.items():
        tiles = [o011[y:y + h, x:x + w], last[y:y + h, x:x + w], l720[y:y + h, x:x + w]]
        tiles = [cv2.resize(t, (w * 2, h * 2), interpolation=cv2.INTER_NEAREST) for t in tiles]
        for t, lab in zip(tiles, ['original 011', 'Veo 1080p last frame', 'Veo 720p last frame']):
            cv2.rectangle(t, (0, 0), (260, 30), (0, 0, 0), -1)
            cv2.putText(t, lab, (6, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
        cv2.imwrite(os.path.join(OUT, f'crop_{name}.jpg'), np.hstack(tiles), [cv2.IMWRITE_JPEG_QUALITY, 92])
    print('저장:', OUT)


if __name__ == '__main__':
    main()
