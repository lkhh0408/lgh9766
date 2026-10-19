"""4K 조각을 손볼 때 쓰는 영상 읽기·쓰기(색 왕복 오차 없음).

OpenCV VideoCapture로 읽고 ffmpeg 기본 설정으로 다시 저장하면 밝기가 약 1.5~2(0~255) 어두워진다
(OpenCV의 YUV→BGR 변환 반올림·색차 보간과 ffmpeg 기본 RGB→YUV 변환이 정확히 서로 반대가 아님).
원본은 BT.601(smpte170m)·tv 범위로 표시돼 있으므로, 읽기와 쓰기 모두 ffmpeg에서 같은 행렬·범위와
accurate_rnd+full_chroma_int로 변환한다. 이렇게 하면 왕복 뒤 Y 평균 차이가 0.01 안팎이다.
"""
import json
import subprocess

import numpy as np

READ_VF = 'scale=in_color_matrix=bt601:in_range=tv:out_range=pc:flags=accurate_rnd+full_chroma_int'
WRITE_VF = 'scale=out_color_matrix=bt601:out_range=tv:flags=accurate_rnd+full_chroma_int'
COLOR_TAGS = ['-color_primaries', 'bt709', '-color_trc', 'iec61966-2-1', '-colorspace', 'smpte170m', '-color_range', 'tv']


def size(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height',
                          '-of', 'json', path], capture_output=True, text=True, check=True).stdout
    s = json.loads(out)['streams'][0]
    return s['width'], s['height']


def read_frames(path, start=0, count=None):
    """start번째부터 count장(없으면 끝까지)의 BGR 프레임 목록. 프레임 번호는 디코드 순서(0부터)."""
    w, h = size(path)
    sel = f"select='gte(n\\,{start})'" if count is None else f"select='between(n\\,{start}\\,{start + count - 1})'"
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', path, '-vf', f'{sel},{READ_VF}', '-vsync', '0',
                          '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-'], stdout=subprocess.PIPE)
    frames, n = [], w * h * 3
    while True:
        buf = p.stdout.read(n)
        if len(buf) < n:
            break
        frames.append(np.frombuffer(buf, np.uint8).reshape(h, w, 3).copy())
    p.wait()
    return frames


def frame_count(path):
    out = subprocess.run(['ffprobe', '-v', 'error', '-count_frames', '-select_streams', 'v:0', '-show_entries',
                          'stream=nb_read_frames', '-of', 'csv=p=0', path], capture_output=True, text=True, check=True)
    return int(out.stdout.strip())


def read_frame(path, idx):
    """idx번째 프레임(-1 = 마지막)."""
    if idx < 0:
        idx += frame_count(path)
    return read_frames(path, idx, 1)[0]


def writer(path, w, h, crf=16, preset='slow'):
    """BGR 프레임을 stdin으로 받는 ffmpeg 인코더(24fps, yuv420p, 원본과 같은 색 표시)."""
    return subprocess.Popen(['ffmpeg', '-y', '-v', 'error', '-f', 'rawvideo', '-pix_fmt', 'bgr24', '-s', f'{w}x{h}',
                             '-r', '24', '-i', '-', '-vf', WRITE_VF, '-c:v', 'libx264', '-preset', preset,
                             '-crf', str(crf), '-pix_fmt', 'yuv420p'] + COLOR_TAGS + [path], stdin=subprocess.PIPE)
