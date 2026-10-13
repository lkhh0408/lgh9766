"""Gemini API 유료 생성 호출(이미지 편집, Veo 영상)과 비용 장부.

모든 유료 호출은 실행 전에 예상 비용을 장부(cost_ledger.csv)에 더해 보고,
누적 예상액이 상한(--cap, 기본 COST_CAP_USD 환경변수 또는 30달러)을 넘으면 실행하지 않는다.
단가는 Gemini API 유료 등급 가격표 기준이며, 실제 청구액은 Google 결제 화면에서 확인해야 한다.

사용 예
  # 이미지 편집(첫 이미지가 편집 대상, 나머지는 참조)
  python3 work/scripts/gen_api.py image --out work/test1/keyframes/008c.png \
      --prompt-file work/test1/prompts/008c.txt 008_83Tower.png 002_83Tower.png

  # 시작·끝 프레임을 지정한 Veo 클립
  python3 work/scripts/gen_api.py video --out work/test1/raw/T1.mp4 \
      --first work/test1/keyframes/008c.png --last 011_83Tower.png \
      --prompt-file work/test1/prompts/T1.txt --model veo-3.1-fast-generate-preview
"""
import argparse
import csv
import datetime as dt
import json
import mimetypes
import os
import sys
import time

LEDGER = os.path.join(os.path.dirname(__file__), '..', 'cost_ledger.csv')

# 달러/초 (오디오 포함 가격, Gemini API 유료 등급)
VIDEO_PRICE = {
    'veo-3.1-fast-generate-preview': {'720p': 0.10, '1080p': 0.12, '4k': 0.30},
    'veo-3.1-generate-preview': {'720p': 0.40, '1080p': 0.40, '4k': 0.60},
    'veo-3.1-lite-generate-preview': {'720p': 0.05, '1080p': 0.08},
}
# 달러/출력 이미지
IMAGE_PRICE = {
    'gemini-3.1-flash-image': {'1K': 0.067, '2K': 0.101},
    'gemini-2.5-flash-image': {'1K': 0.039},
}

NEGATIVE = ('cut, scene transition, morphing, warping or melting buildings, flickering, '
            'zoom, crossfade, slideshow, text, watermark')


def ledger_rows():
    if not os.path.exists(LEDGER):
        return []
    with open(LEDGER, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def spent():
    # 실패·차단된 생성은 청구되지 않으므로 status=ok만 합산
    return sum(float(r['est_usd']) for r in ledger_rows() if r['status'] == 'ok')


def log(kind, model, settings, est, status, out, note=''):
    new = not os.path.exists(LEDGER)
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(['time_utc', 'kind', 'model', 'settings', 'est_usd', 'status', 'output', 'note'])
        w.writerow([dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), kind, model,
                    json.dumps(settings, ensure_ascii=False), f'{est:.3f}', status,
                    os.path.relpath(out), note])


def check_cap(est, cap):
    total = spent()
    print(f'누적 예상 비용 ${total:.2f} + 이번 ${est:.2f} / 상한 ${cap:.2f}')
    if total + est > cap:
        sys.exit('상한 초과: 실행하지 않음')


_CLIENT = None


def client():
    # 클라이언트 객체가 먼저 해제되면 연결이 닫히므로 모듈 수준에 보관
    global _CLIENT
    if _CLIENT is None:
        from google import genai
        _CLIENT = genai.Client(api_key=os.environ['GEMINI_API_KEY'])
    return _CLIENT


def load_image(path):
    from google.genai import types
    mime = mimetypes.guess_type(path)[0] or 'image/png'
    with open(path, 'rb') as f:
        return types.Image(image_bytes=f.read(), mime_type=mime)


def read_prompt(args):
    if args.prompt_file:
        with open(args.prompt_file, encoding='utf-8') as f:
            return f.read().strip()
    return args.prompt


def cmd_image(args):
    from google.genai import types
    from PIL import Image
    est = IMAGE_PRICE[args.model][args.size]
    check_cap(est, args.cap)
    prompt = read_prompt(args)
    parts = [prompt] + [Image.open(p) for p in args.images]
    settings = {'inputs': args.images, 'size': args.size, 'aspect': '16:9'}
    try:
        resp = client().models.generate_content(
            model=args.model, contents=parts,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(aspect_ratio='16:9', image_size=args.size)))
    except Exception as e:
        log('image', args.model, settings, 0, 'error', args.out, str(e)[:300])
        raise
    data = None
    for part in resp.candidates[0].content.parts if resp.candidates else []:
        if part.inline_data is not None:
            data = part.inline_data.data
    if data is None:
        log('image', args.model, settings, 0, 'no_image', args.out, str(resp)[:300])
        sys.exit('이미지가 반환되지 않음')
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, 'wb') as f:
        f.write(data)
    log('image', args.model, settings, est, 'ok', args.out)
    print('저장:', args.out)


def cmd_video(args):
    from google.genai import types
    # 연장은 7초가 새로 생성됨(출력 영상은 입력 영상 + 연장분)
    gen_sec = 7 if args.extend else args.duration
    est = VIDEO_PRICE[args.model][args.resolution] * gen_sec
    check_cap(est, args.cap)
    prompt = read_prompt(args)
    cfg = dict(aspect_ratio='16:9', resolution=args.resolution, number_of_videos=1,
               negative_prompt=args.negative)
    if not args.extend:
        cfg['duration_seconds'] = args.duration
    if args.last:
        cfg['last_frame'] = load_image(args.last)
    if args.seed is not None:
        cfg['seed'] = args.seed
    settings = {k: v for k, v in cfg.items() if k != 'last_frame'}
    settings.update(first=args.first, last=args.last, extend=args.extend)
    if args.extend:
        # 앞 클립(Veo 생성본)의 서버 URI가 있으면 사용, 없으면 파일 바이트 전송
        meta = os.path.splitext(args.extend)[0] + '.json'
        uri = json.load(open(meta, encoding='utf-8')).get('video_uri') if os.path.exists(meta) else None
        src = types.GenerateVideosSource(
            prompt=prompt,
            video=types.Video(uri=uri) if uri else
            types.Video(video_bytes=open(args.extend, 'rb').read(), mime_type='video/mp4'))
    else:
        src = types.GenerateVideosSource(prompt=prompt, image=load_image(args.first))
    c = client()
    try:
        op = c.models.generate_videos(model=args.model, source=src,
                                      config=types.GenerateVideosConfig(**cfg))
        t0 = time.time()
        while not op.done:
            time.sleep(10)
            op = c.operations.get(op)
            print(f'  생성 중… {time.time() - t0:.0f}s', flush=True)
    except Exception as e:
        log('video', args.model, settings, 0, 'error', args.out, str(e)[:300])
        raise
    resp = op.response
    vids = getattr(resp, 'generated_videos', None) if resp else None
    if op.error or not vids:
        note = json.dumps(op.error) if op.error else str(resp)[:300]
        log('video', args.model, settings, 0, 'failed', args.out, note[:300])
        sys.exit(f'생성 실패: {note}')
    v = vids[0].video
    c.files.download(file=v)
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    v.save(args.out)
    with open(os.path.splitext(args.out)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump({'model': args.model, 'prompt': prompt, 'video_uri': v.uri, **settings}, f,
                  ensure_ascii=False, indent=1)
    log('video', args.model, settings, est, 'ok', args.out)
    print('저장:', args.out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--cap', type=float, default=float(os.environ.get('COST_CAP_USD', 30)))
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('image')
    p.add_argument('images', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--prompt')
    p.add_argument('--prompt-file')
    p.add_argument('--model', default='gemini-3.1-flash-image')
    p.add_argument('--size', default='2K')
    p.set_defaults(fn=cmd_image)

    p = sub.add_parser('video')
    p.add_argument('--out', required=True)
    p.add_argument('--first')
    p.add_argument('--extend', help='연장할 앞 클립(mp4). 지정하면 --first 대신 사용')
    p.add_argument('--last')
    p.add_argument('--prompt')
    p.add_argument('--prompt-file')
    p.add_argument('--negative', default=NEGATIVE)
    p.add_argument('--model', default='veo-3.1-fast-generate-preview')
    p.add_argument('--resolution', default='1080p')
    p.add_argument('--duration', type=int, default=8)
    p.add_argument('--seed', type=int)
    p.set_defaults(fn=cmd_video)

    args = ap.parse_args()
    args.fn(args)


if __name__ == '__main__':
    main()
