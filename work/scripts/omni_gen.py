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
    ap.add_argument('--extend-video', help='연장할 영상 파일(10초 이하). 업로드해서 이어 만든다')
    ap.add_argument('--prompt-file', required=True)
    ap.add_argument('--resolution', default='360p', choices=list(PRICE))
    ap.add_argument('--duration', type=int, default=8)
    ap.add_argument('--stream', action='store_true',
                    help='진행 이벤트를 받으며 기다림(4K 연장처럼 오래 걸릴 때). 스트리밍 생성은 다음 연장의 재료로 쓸 수 없음')
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
    elif a.extend_video:
        uri, mime = upload(client, a.extend_video)
        parts.append({'type': 'video', 'uri': uri, 'mime_type': mime})
        if '[# Sources' not in prompt:
            prompt = '[# Sources <VIDEO_0>@Video1] ' + prompt
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
    kwargs = dict(model=MODEL, input=parts, response_format=fmt, store=True)  # 다음 연장이 이 결과를 불러올 수 있게 저장
    if prev_id:
        kwargs['previous_interaction_id'] = prev_id
    settings = {'resolution': a.resolution, 'duration': a.duration, 'first': a.first, 'last': a.last,
                'extend_from': a.extend_from, 'extend_video': a.extend_video}
    t0 = time.time()
    try:
        # 오래 걸리는 생성(4K·연장)은 응답 없이 기다리면 연결이 끊길 수 있어, 스트리밍으로 진행 이벤트를 받으며 기다린다
        # (background=True는 영상 입력이 있는 요청을 지원하지 않음)
        iid, last = None, None
        events = client.interactions.create(stream=True, **kwargs) if a.stream else []
        if not a.stream:
            it0 = client.interactions.create(**kwargs)
            iid = it0.id
        for ev in events:
            last = ev
            obj = getattr(ev, 'interaction', None)
            iid = iid or getattr(obj, 'id', None) or getattr(ev, 'interaction_id', None)
            print(f'  이벤트 {getattr(ev, "event_type", type(ev).__name__)} {time.time() - t0:.0f}s', flush=True)
        if not iid:
            raise RuntimeError(f'interaction id를 받지 못함: {str(last)[:300]}')
        it = client.interactions.get(iid)
    except Exception as e:
        log('video', MODEL, settings, 0, 'error', a.out, str(e)[:300])
        raise
    if getattr(it, 'status', 'completed') != 'completed':
        log('video', MODEL, settings, 0, 'failed', a.out, f'status={it.status}')
        sys.exit(f'생성 실패: status={it.status}')
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
