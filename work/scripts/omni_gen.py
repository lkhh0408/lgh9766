"""Gemini Omni 1.1 Flash 영상 생성(Interactions API) + 비용 장부.

시작·끝 프레임 지정, 앞 생성 이어서 연장(previous interaction), 해상도·길이 지정을 지원한다.
단가(초당, 2026-10 기사 기준, 공식 가격표 미확인): 360p $0.03, 720p $0.10, 1080p $0.15, 4k $0.30.

사용(저장소 루트):
  python3 work/scripts/omni_gen.py --out work/omni/A.mp4 --first 032_83Tower.png --last 040_83Tower.png \
      --prompt-file work/omni/prompts/A.txt --resolution 360p --duration 8
  # 연장: 앞 결과의 json에 저장된 interaction id 사용
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --extend-from work/omni/A.json \
      --prompt-file work/omni/prompts/B.txt --resolution 360p --duration 8
"""
import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_api import check_cap, log  # noqa: E402

MODEL = 'gemini-omni-1.1-flash'
PRICE = {'360p': 0.03, '720p': 0.10, '1080p': 0.15, '4k': 0.30}


def upload(client, path):
    from google.genai import types
    f = client.files.upload(file=path)
    for _ in range(60):
        f = client.files.get(name=f.name)
        state = getattr(f.state, 'name', str(f.state))
        if state == 'ACTIVE':
            return f.uri, f.mime_type
        if state == 'FAILED':
            raise RuntimeError(f'업로드 실패: {path}')
        time.sleep(2)
    raise TimeoutError(f'업로드 대기 시간 초과: {path}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--first')
    ap.add_argument('--last')
    ap.add_argument('--extend-from', help='앞 생성 결과 json(previous interaction id가 들어 있음)')
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--resolution', default='360p', choices=list(PRICE))
    ap.add_argument('--duration', type=int, default=8)
    ap.add_argument('--cap', type=float, default=float(os.environ.get('COST_CAP_USD', 30)))
    a = ap.parse_args()
    from google import genai
    from google.genai import types

    est = PRICE[a.resolution] * a.duration
    check_cap(est, a.cap)
    with open(a.prompt_file, encoding='utf-8') as f:
        prompt = f.read().strip()
    client = genai.Client(api_key=os.environ['GEMINI_API_KEY'],
                          http_options=types.HttpOptions(timeout=1200 * 1000))
    parts, prev_id = [], None
    if a.extend_from:
        prev_id = json.load(open(a.extend_from, encoding='utf-8'))['interaction_id']
    else:
        if a.first:
            uri, mime = upload(client, a.first)
            parts.append({'type': 'image', 'uri': uri, 'mime_type': mime})
        if a.last:
            uri, mime = upload(client, a.last)
            parts.append({'type': 'image', 'uri': uri, 'mime_type': mime})
        tags = ('<FIRST_FRAME> <LAST_FRAME> ' if a.first and a.last else '<FIRST_FRAME> ' if a.first else '')
        if tags and '<FIRST_FRAME>' not in prompt:
            prompt = tags + prompt
    parts.append({'type': 'text', 'text': prompt})
    fmt = {'type': 'video', 'delivery': 'uri', 'aspect_ratio': '16:9',
           'duration': f'{a.duration}s', 'resolution': a.resolution}
    kwargs = dict(model=MODEL, input=parts, response_format=fmt)
    if prev_id:
        kwargs['previous_interaction_id'] = prev_id
    settings = {'resolution': a.resolution, 'duration': a.duration, 'first': a.first, 'last': a.last,
                'extend_from': a.extend_from}
    t0 = time.time()
    try:
        it = client.interactions.create(**kwargs)
    except Exception as e:
        log('video', MODEL, settings, 0, 'error', a.out, str(e)[:300])
        raise
    ov = getattr(it, 'output_video', None)
    if not ov or not getattr(ov, 'uri', None):
        log('video', MODEL, settings, 0, 'no_video', a.out, str(it)[:300])
        sys.exit('영상이 반환되지 않음')
    data = client.files.download(file=ov.uri)
    os.makedirs(os.path.dirname(a.out) or '.', exist_ok=True)
    with open(a.out, 'wb') as f:
        f.write(data)
    usage = getattr(it, 'usage', None)
    meta = {'model': MODEL, 'interaction_id': it.id, 'prompt': prompt, 'seconds_taken': round(time.time() - t0),
            'usage': usage.model_dump() if hasattr(usage, 'model_dump') else str(usage), **settings}
    with open(os.path.splitext(a.out)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=str)
    log('video', MODEL, settings, est, 'ok', a.out, 'Omni 단가는 기사 기준 추정')
    print('저장:', a.out, '| 생성 시간', meta['seconds_taken'], '초 | interaction', it.id)


if __name__ == '__main__':
    main()
