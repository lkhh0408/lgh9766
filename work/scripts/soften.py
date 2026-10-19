"""선명도 맞추기: 조각 전체에 아주 약한 가우시안 흐림을 주되, 세기(σ, 4K 화소)를 첫 프레임 --start에서
끝 프레임 --end까지 고르게 바꾼다. 연장으로 다시 그린 부분처럼 앞뒤 조각보다 날카로운 조각을
이웃 조각의 선명도에 맞출 때 쓴다(이음새에서 화면 전체가 갑자기 날카로워지는 튐을 없앰). 무료(로컬 계산만 함).

σ 고르는 법: 1080p로 줄인 회색조의 라플라시안 절댓값 평균(선명도 지수)이 이웃 조각의 이음새 쪽 프레임과
같아지는 값을 찾는다(work/final/R/최종_보고서.md의 선명도 맞추기 표 참고).

사용: python3 work/scripts/soften.py <입력.mp4> <출력.mp4> --start 0.94 --end 0.58
"""
import argparse

import cv2

from vio import read_frames, writer


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('src')
    ap.add_argument('dst')
    ap.add_argument('--start', type=float, required=True, help='첫 프레임 흐림 σ(4K 화소)')
    ap.add_argument('--end', type=float, required=True, help='끝 프레임 흐림 σ(4K 화소)')
    a = ap.parse_args()
    frames = read_frames(a.src)
    n = len(frames)
    h, w = frames[0].shape[:2]
    enc = writer(a.dst, w, h, crf=12)
    for k, f in enumerate(frames):
        s = a.start + (a.end - a.start) * k / max(n - 1, 1)
        enc.stdin.write((cv2.GaussianBlur(f, (0, 0), s) if s > 0.05 else f).tobytes())
    enc.stdin.close()
    enc.wait()
    print(f'{a.dst}: {n}프레임, 흐림 σ {a.start} → {a.end}')


if __name__ == '__main__':
    main()
