"""Gemini Omni 1.1 Flash 영상 생성(Interactions API) + 비용 장부 + 끊긴 요청의 서버 결과 되찾기.

시작·끝 프레임 지정, 앞 생성 이어서 연장(previous interaction), 해상도·길이(3~10초) 지정을 지원한다.

비용(이 프로젝트 측정): 영상 출력 토큰 x $17.5/100만(기사 기준 단가, 공식 가격표 미확인).
  초당 출력 토큰 360p 1,931 / 1080p 8,688 / 4k 17,376 (= 초당 $0.034 / $0.152 / $0.304), 720p는 미측정.
  요청 전 예상액 = 초당 단가 x 길이 + 연장 입력 추정 + 여유 $0.02.
  성공하면 응답의 실제 토큰 수로 계산한 값을 장부에 적고, 예상액도 json과 장부 메모에 함께 남긴다.

유료 요청 안전 규칙(gen_api.py 머리말도 참고)
- 생성 요청은 한 번 실행에 한 번만 보낸다. SDK 자동 재시도는 끈다:
  interactions 쪽은 RetryConfig('none')으로 덮어쓰고 꺼졌는지 확인한 뒤에만 보낸다.
  (기본값은 503 등에 같은 요청을 최대 4번 보내 중복 청구 위험. HttpRetryOptions(attempts=0/1)로는 안 꺼짐)
  상태 확인·파일 목록·내려받기·업로드(모두 무료)는 기본 설정의 별도 클라이언트로 한다.
- 요청 직전에 장부에 pending 행(예상액)을 적고, 끝나면 결과로 바꾼다.
- 예산 파일(work/final/budget.json)의 상한·80% 보고선을 넘으면 보내지 않는다(--allow-over-warn).
- 요청이 끊기거나(연결 끊김·시간 초과·5XX 등) 오류가 나면 **다시 보내지 않는다.**
  대신 files.list()에서 요청 시작 뒤에 생긴 GENERATED 영상(요청 전 목록·기존 json·장부에 이미 적힌 이름 제외)을
  기본 6분 동안 20초마다 찾는다. 찾으면 --out으로 내려받고 json(interaction_id 없음, 연장 불가)과 장부(ok, 예상액)를
  남긴다. 못 찾으면 장부에 error(0달러)로 적고 "청구됐을 수 있음" 경고를 낸다. 다시 시도하기 전에 꼭 확인할 것.
- 즉시 거절(400·401·403·404·422, invalid_request)은 청구되지 않은 것으로 보고 바로 끝낸다.
- 되찾은 결과(interaction_id 없음)나 스트리밍 생성은 다음 연장의 재료로 쓸 수 없어 --extend-from에서 거절한다.

종료 코드: 0 성공(되찾기 포함), 2 인자 오류, 10 상한 초과, 11 80% 보고선, 12 출력 파일 있음,
          20 오류 뒤 결과 못 찾음(청구됐을 수 있음), 21 즉시 거절, 22 서버가 실패·영상 없음으로 끝냄,
          23 생성은 됐으나 내려받기 실패(--recover-only로 다시 받기)

사용(저장소 루트):
  python3 work/scripts/omni_gen.py --out work/omni/A.mp4 --first 032_83Tower.png --last 040_83Tower.png \
      --prompt-file work/omni/prompts/A.txt --resolution 360p --duration 8
  # 연장: 앞 결과의 json에 저장된 interaction id 사용
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --extend-from work/omni/A.json \
      --prompt-file work/omni/prompts/B.txt --resolution 360p --duration 8
  # (무료) 프로세스가 중간에 죽었거나 내려받기에 실패했을 때: 서버 결과만 찾아서 받기
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --recover-only [--recover-since 2026-10-18T01:23:45]
"""
import argparse
import datetime as dt
import json
import os
import re
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gen_api as G  # noqa: E402
from gen_api import check_cap, log  # noqa: E402,F401  (예전 호출 호환)

MODEL = 'gemini-omni-1.1-flash'
# 측정한 초당 영상 출력 토큰. 720p는 미측정이라 기사 단가($0.10/초)를 토큰으로 환산한 값
VIDEO_TOKENS_PER_SEC = {'360p': 1931, '720p': 5715, '1080p': 8688, '4k': 17376}
VIDEO_OUT_PER_M = 17.5   # 영상 출력 $/100만 토큰
OTHER_OUT_PER_M = 17.5   # 글자·생각 출력 토큰(단가 모름, 보수적으로 영상과 같게)
INPUT_PER_M = 2.0        # 입력 토큰(단가 모름, 보수적. 장부 보정값으로 보면 약 1.5)
EXT_INPUT_USD = {'360p': 0.04, '720p': 0.10, '1080p': 0.10, '4k': 0.10}  # 연장 때 앞 영상 입력 추정
MARGIN_USD = 0.02
# 초당 단가(예전 이름 호환)
PRICE = {r: round(t * VIDEO_OUT_PER_M / 1e6, 4) for r, t in VIDEO_TOKENS_PER_SEC.items()}
NAME_RE = re.compile(r'files/([A-Za-z0-9_-]+)')


class DownloadError(RuntimeError):
    pass


# ---------------------------------------------------------------- 비용

def estimate_usd(resolution, duration, extension=False):
    usd = VIDEO_TOKENS_PER_SEC[resolution] * duration * VIDEO_OUT_PER_M / 1e6 + MARGIN_USD
    return round(usd + (EXT_INPUT_USD[resolution] if extension else 0), 3)


def usage_dict(usage):
    if usage is None:
        return None
    if isinstance(usage, dict):
        return usage
    if hasattr(usage, 'model_dump'):
        return usage.model_dump()
    return {'raw': str(usage)}


def _tokens(lst, modality):
    return sum(int((x or {}).get('tokens') or 0) for x in (lst or [])
               if str((x or {}).get('modality', '')).lower() == modality)


def usage_cost(u):
    """응답 토큰으로 계산한 실제 비용(달러). 영상 출력 토큰이 없으면 None."""
    if not isinstance(u, dict):
        return None, {}
    vid = _tokens(u.get('output_tokens_by_modality'), 'video')
    if not vid:
        return None, {}
    out_total = int(u.get('total_output_tokens') or vid)
    other = max(out_total - vid, 0) + int(u.get('total_thought_tokens') or 0)
    inp = int(u.get('total_input_tokens') or sum(int((x or {}).get('tokens') or 0)
                                                 for x in (u.get('input_tokens_by_modality') or [])))
    usd = vid * VIDEO_OUT_PER_M / 1e6 + other * OTHER_OUT_PER_M / 1e6 + inp * INPUT_PER_M / 1e6
    return round(usd, 4), {'video_output_tokens': vid, 'other_output_tokens': other, 'input_tokens': inp}


# ---------------------------------------------------------------- 클라이언트

def make_paid_client(key=None, **http_kw):
    """유료 생성 전용: 자동 재시도를 완전히 끈 클라이언트(시간 제한 20분). 꺼졌는지 확인 못 하면 예외."""
    from google import genai
    from google.genai import types
    from google.genai._gaos.utils import RetryConfig
    G.no_debug_env()
    http_kw.setdefault('timeout', 1200 * 1000)
    http_kw.pop('retry_options', None)
    c = genai.Client(api_key=key or G.api_key(), http_options=types.HttpOptions(**http_kw))
    c.interactions.sdk_configuration.retry_config = RetryConfig('none', None, False)
    rc = c.interactions.sdk_configuration.retry_config
    if getattr(rc, 'strategy', None) != 'none' or getattr(rc, 'retry_connection_errors', True) is not False:
        raise RuntimeError('SDK 자동 재시도를 끄지 못함: 유료 요청을 보내지 않음')
    return c


def make_poll_client(key=None, **http_kw):
    """상태 확인·파일 목록·내려받기·업로드 전용(무료, 재시도해도 안전): 기본 재시도 설정 그대로."""
    from google import genai
    from google.genai import types
    G.no_debug_env()
    http_kw.setdefault('timeout', 600 * 1000)
    return genai.Client(api_key=key or G.api_key(), http_options=types.HttpOptions(**http_kw))


def upload(client, path):
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


# ---------------------------------------------------------------- 서버 결과 되찾기

def _enum(v):
    v = getattr(v, 'value', v)
    return str(v or '').upper()


def _utc(t):
    if t is None:
        return None
    if isinstance(t, str):
        try:
            t = dt.datetime.fromisoformat(t.replace('Z', '+00:00'))
        except ValueError:
            return None
    if t.tzinfo is None:
        t = t.replace(tzinfo=dt.timezone.utc)
    return t.astimezone(dt.timezone.utc)


def file_name(ref):
    s = getattr(ref, 'name', None) or str(ref or '')
    m = NAME_RE.search(s)
    return f'files/{m.group(1)}' if m else (s or None)


def list_generated(pc):
    """서버 파일 중 생성된 영상만(업로드한 파일 제외)."""
    out = []
    for f in pc.files.list(config={'page_size': 100}):
        mime = str(getattr(f, 'mime_type', '') or '')
        if _enum(getattr(f, 'source', None)) == 'GENERATED' and (not mime or mime.startswith('video/')):
            out.append(f)
    return out


def referenced_names(extra_dirs=()):
    """이미 어떤 결과로 기록된 서버 파일 이름(json·장부에 적힌 files/…)."""
    names = set()
    roots = {G.WORK} | {os.path.abspath(d) for d in extra_dirs if d}
    for root in roots:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if not d.startswith('.') and d != '__pycache__']
            for fn in fns:
                if not fn.endswith('.json'):
                    continue
                fp = os.path.join(dp, fn)
                try:
                    if os.path.getsize(fp) > 5_000_000:
                        continue
                    with open(fp, encoding='utf-8', errors='ignore') as f:
                        names |= {f'files/{m}' for m in NAME_RE.findall(f.read())}
                except OSError:
                    pass
    if os.path.exists(G.ledger_path()):
        with open(G.ledger_path(), encoding='utf-8', errors='ignore') as f:
            names |= {f'files/{m}' for m in NAME_RE.findall(f.read())}
    return names


def find_recovered(pc, since, exclude, wait, interval, skew):
    """since(UTC) - skew 뒤에 생긴, exclude에 없는 생성 영상을 wait초 동안 찾는다. (가장 새것, 나머지 후보)"""
    cut = _utc(since) - dt.timedelta(seconds=skew)
    t0, n = time.time(), 0
    while True:
        n += 1
        try:
            files = list_generated(pc)
        except Exception as e:  # 목록 확인은 무료이므로 다음 차례에 다시 본다
            print(f'  파일 목록 확인 실패(다시 확인함): {G.scrub(e)[:150]}', flush=True)
            files = []
        cands = [f for f in files if file_name(f) not in exclude and _utc(getattr(f, 'create_time', None))
                 and _utc(f.create_time) >= cut and _enum(getattr(f, 'state', None)) != 'FAILED']
        ready = [f for f in cands if _enum(getattr(f, 'state', None)) in ('', 'ACTIVE', 'STATE_UNSPECIFIED')]
        if ready:
            ready.sort(key=lambda f: _utc(f.create_time))
            if len(ready) > 1:
                print(f'  주의: 후보가 {len(ready)}개입니다. 가장 새 것을 씁니다: '
                      f'{[file_name(f) for f in ready]}', flush=True)
            return ready[-1], ready[:-1]
        left = wait - (time.time() - t0)
        if left <= 0:
            return None, []
        print(f'  서버 결과 아직 없음({n}회 확인, {time.time() - t0:.0f}초 경과)', flush=True)
        time.sleep(min(interval, left))


def save_video(pc, ref, out, mime, overwrite):
    """서버 영상을 내려받아 저장(무료라 3번까지 다시 받음). 형식에 맞게 확장자를 고치고, 기존 파일은 덮지 않는다."""
    ext = {'video/mp4': '.mp4', 'video/webm': '.webm', 'video/quicktime': '.mov'}.get(str(mime or ''))
    path = out
    if ext and os.path.splitext(out)[1].lower() != ext:
        path = os.path.splitext(out)[0] + ext
        print(f'  받은 형식({mime})에 맞춰 확장자를 바꿈: {path}', flush=True)
    path = G.free_path(path, overwrite)  # 이미 돈을 냈으므로 실패하지 말고 빈 이름을 고른다
    data, err = None, None
    for i in range(3):
        try:
            data = pc.files.download(file=ref)
            break
        except Exception as e:
            err = e
            print(f'  내려받기 실패({i + 1}/3): {G.scrub(e)[:150]}', flush=True)
            if i < 2:
                time.sleep(10 * (i + 1))
    if data is None:
        raise DownloadError(G.scrub(err)[:300])
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    tmp = path + '.downloading'
    with open(tmp, 'wb') as f:
        f.write(data)
    os.replace(tmp, path)
    return path


def probe_seconds(path):
    if not path or not os.path.exists(path):
        return None
    try:
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', path],
                           capture_output=True, text=True, timeout=60)
        return round(float(r.stdout.strip()), 3)
    except (OSError, ValueError, subprocess.SubprocessError):
        return None


def expected_seconds(a):
    """나와야 할 영상 길이(연장이면 줄기 전체). 알 수 없으면 None."""
    if a.extend_from:
        prev = json.load(open(a.extend_from, encoding='utf-8'))
        base = prev.get('chain_seconds') or probe_seconds(os.path.splitext(a.extend_from)[0] + '.mp4')
        return round(base + a.duration, 3) if base else None
    if a.extend_video:
        base = probe_seconds(a.extend_video)
        return round(base + a.duration, 3) if base else None
    return float(a.duration)


def _write_json(path, meta):
    with open(os.path.splitext(path)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=1, default=str)


def _length_check(meta, path, expected):
    chain = probe_seconds(path)
    meta['chain_seconds'], meta['expected_seconds'] = chain, expected
    if chain and expected and abs(chain - expected) > 1.0:
        meta['length_mismatch'] = True
        print(f'  주의: 영상 길이 {chain}초가 예상 {expected}초와 다릅니다. 다른 요청의 결과일 수 있으니 눈으로 확인하세요.',
              flush=True)


# ---------------------------------------------------------------- 실행

def build_parser():
    ap = argparse.ArgumentParser(description='Gemini Omni 영상 생성(유료, 1회 시도) / 서버 결과 되찾기(무료)')
    ap.add_argument('--out', required=True)
    ap.add_argument('--first')
    ap.add_argument('--last')
    ap.add_argument('--extend-from', help='앞 생성 결과 json(previous interaction id가 들어 있음)')
    ap.add_argument('--extend-video', help='연장할 영상 파일(10초 이하). 업로드해서 이어 만든다')
    ap.add_argument('--prompt-file', help='프롬프트 파일(생성에는 꼭 필요)')
    ap.add_argument('--resolution', default='360p', choices=list(VIDEO_TOKENS_PER_SEC))
    ap.add_argument('--duration', type=int, default=8, help='새로 만들 길이(초, 3~10)')
    ap.add_argument('--stream', action='store_true',
                    help='진행 이벤트를 받으며 기다림. 스트리밍 생성은 다음 연장의 재료로 쓸 수 없음')
    G.add_safety_args(ap, True)
    ap.add_argument('--overwrite', action='store_true', help='출력 파일이 이미 있어도 진행(기본은 거절)')
    ap.add_argument('--recover-wait', type=float, default=360, help='오류 뒤 서버 결과를 찾는 시간(초, 기본 6분)')
    ap.add_argument('--recover-interval', type=float, default=20, help='서버 파일 목록 확인 간격(초)')
    ap.add_argument('--recover-skew', type=float, default=30, help='시계 차이 여유(초)')
    ap.add_argument('--recover-only', action='store_true',
                    help='유료 요청 없이 서버 결과만 찾아 받기(프로세스가 죽었거나 내려받기 실패 뒤)')
    ap.add_argument('--recover-since', help='--recover-only: 이 UTC 시각 뒤 결과만(ISO, 예 2026-10-18T01:23:45)')
    return ap


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    G.no_debug_env()
    if a.recover_only:
        return recover_only(a)
    if not a.prompt_file:
        ap.error('--prompt-file이 필요합니다')
    if not 3 <= a.duration <= 10:
        ap.error('--duration은 3~10초입니다')

    extension = bool(a.extend_from or a.extend_video)
    est = estimate_usd(a.resolution, a.duration, extension)
    prev_id = None
    if a.extend_from:
        prev = json.load(open(a.extend_from, encoding='utf-8'))
        prev_id = prev.get('interaction_id')
        if not prev_id or prev.get('extendable') is False:
            print(f'{a.extend_from}: 이 결과는 연장 재료로 쓸 수 없습니다(되찾은 파일이거나 스트리밍 생성이라 '
                  f'interaction id가 없거나 연장 불가). 유료 요청을 보내지 않음', file=sys.stderr)
            sys.exit(2)
    G.guard(est, a.cap, a.budget_file, a.allow_over_warn)
    G.refuse_existing(a.out, a.overwrite)
    with open(a.prompt_file, encoding='utf-8') as f:
        prompt = f.read().strip()

    pc = make_poll_client()
    parts = []
    if a.extend_video:
        uri, mime = upload(pc, a.extend_video)
        parts.append({'type': 'video', 'uri': uri, 'mime_type': mime})
        if '[# Sources' not in prompt:
            prompt = '[# Sources <VIDEO_0>@Video1] ' + prompt
    elif not a.extend_from:
        if a.first:
            uri, mime = upload(pc, a.first)
            parts.append({'type': 'image', 'uri': uri, 'mime_type': mime})
        if a.last:
            uri, mime = upload(pc, a.last)
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

    # 되찾기 준비(무료): 지금 서버에 있는 생성 영상 + 이미 기록된 이름은 후보에서 뺀다
    exclude = referenced_names([os.path.dirname(os.path.abspath(a.out))])
    try:
        exclude |= {file_name(f) for f in list_generated(pc)}
    except Exception as e:
        print(f'주의: 요청 전 서버 파일 목록을 못 받음(시각 조건만으로 되찾기): {G.scrub(e)[:150]}', flush=True)

    paid = make_paid_client()
    G.once('omni')
    token = G.log_pending('video', MODEL, settings, est, a.out, f'{a.resolution} {a.duration}초 요청')
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.time()
    print(f'요청 시작 {start.isoformat(timespec="seconds")} (UTC), 예상 ${est:.3f}', flush=True)
    it, iid = None, None
    try:
        if a.stream:
            last = None
            for ev in paid.interactions.create(stream=True, **kwargs):
                last = ev
                obj = getattr(ev, 'interaction', None)
                iid = iid or getattr(obj, 'id', None) or getattr(ev, 'interaction_id', None)
                print(f'  이벤트 {getattr(ev, "event_type", type(ev).__name__)} {time.time() - t0:.0f}s', flush=True)
            if not iid:
                raise RuntimeError(f'interaction id를 받지 못함: {str(last)[:300]}')
        else:
            it = paid.interactions.create(**kwargs)
            iid = getattr(it, 'id', None)
            if not iid:
                raise RuntimeError('interaction id를 받지 못함')
    except Exception as e:
        return after_failure(a, pc, token, est, e, start, t0, exclude, settings, prompt)
    create_sec = round(time.time() - t0)

    # 결과 확인(무료, 다시 해도 안전). 실패하면 생성 응답을 그대로 쓴다
    got = None
    for i in range(3):
        try:
            got = pc.interactions.get(iid)
            break
        except Exception as e:
            print(f'  결과 확인 실패({i + 1}/3): {G.scrub(e)[:150]}', flush=True)
            if i < 2:
                time.sleep(5 * (i + 1))
    it = got or it
    meta = {'model': MODEL, 'interaction_id': iid, 'extendable': not a.stream, 'prompt': prompt,
            'request_start_utc': start.isoformat(timespec='seconds'), 'create_seconds': create_sec, **settings}
    if it is None:
        G.finalize(token, est, 'ok', f'생성 요청은 끝났으나 결과 확인 실패(interaction {iid}). 추정 ${est:.3f}')
        _write_json(a.out, {**meta, 'downloaded': False, 'cost': {'estimate_usd': est, 'used_usd': est}})
        print('경고: 생성은 끝났지만 결과를 확인하지 못했습니다. 나중에 --recover-only로 받으세요.', file=sys.stderr)
        sys.exit(G.EXIT_FETCH)
    status = str(getattr(getattr(it, 'status', 'completed'), 'value', getattr(it, 'status', 'completed'))).lower()
    usage = usage_dict(getattr(it, 'usage', None))
    actual, detail = usage_cost(usage)
    cost = actual if actual is not None else est
    meta['usage'] = usage
    meta['cost'] = {'estimate_usd': est, 'actual_usd': actual, 'used_usd': cost, 'tokens': detail,
                    'basis': '응답 토큰 x 단가' if actual is not None else '사전 추정(토큰 정보 없음)'}
    if status != 'completed':
        # 영상 출력 토큰이 잡혔으면 청구된 것으로 본다
        G.finalize(token, actual or 0, 'ok' if actual else 'failed', f'status={status}')
        print(f'생성 실패: status={status}', file=sys.stderr)
        sys.exit(G.EXIT_FAILED)
    ov = getattr(it, 'output_video', None)
    uri = getattr(ov, 'uri', None)
    if not uri:
        G.finalize(token, actual or 0, 'ok' if actual else 'no_video', '영상이 반환되지 않음 ' + str(it)[:200])
        print('영상이 반환되지 않음', file=sys.stderr)
        sys.exit(G.EXIT_FAILED)
    meta['output_file'] = file_name(uri)
    t1 = time.time()
    try:
        path = save_video(pc, uri, a.out, getattr(ov, 'mime_type', None), a.overwrite)
    except DownloadError as e:
        _write_json(a.out, {**meta, 'downloaded': False})
        G.finalize(token, cost, 'ok', f'생성됨, 내려받기 실패({e}). --recover-only로 다시 받기')
        print('경고: 생성은 됐지만 내려받기에 실패했습니다. --recover-only로 다시 받으세요(무료).', file=sys.stderr)
        sys.exit(G.EXIT_FETCH)
    meta['download_seconds'] = round(time.time() - t1)
    meta['seconds_taken'] = round(time.time() - t0)
    meta['output_path'] = os.path.relpath(path)
    _length_check(meta, path, expected_seconds(a))
    _write_json(path, meta)
    if actual is not None:
        note = f'응답 토큰 기준 ${actual:.3f}(사전 추정 ${est:.3f}), 생성 {create_sec}초'
    else:
        note = f'사전 추정 ${est:.3f}(토큰 정보 없음), 생성 {create_sec}초'
    G.finalize(token, cost, 'ok', note)
    print('저장:', path, '| 생성 시간', meta['seconds_taken'], '초 | 비용', f'${cost:.3f}', '| interaction', iid)
    return 0


def after_failure(a, pc, token, est, e, start, t0, exclude, settings, prompt):
    """유료 요청이 오류로 끝났을 때: 다시 보내지 않고, 서버에서 완성됐는지 찾아본다."""
    code = G.status_code_of(e)
    msg = G.scrub(f'{type(e).__name__}: {e}')[:300]
    took = time.time() - t0
    if code in G.REJECT_CODES or (code is None and 'invalid_request' in msg):
        G.finalize(token, 0, 'error', f'즉시 거절 {msg}')
        print(f'요청이 즉시 거절됨({code or "invalid_request"}, {took:.0f}초): {msg}', file=sys.stderr)
        sys.exit(G.EXIT_REJECTED)
    print(f'요청 오류({took:.0f}초 뒤): {msg}\n'
          f'  같은 요청을 다시 보내지 않습니다. 서버에서 끝까지 만들어졌는지 파일 목록을 '
          f'최대 {a.recover_wait:.0f}초 동안 {a.recover_interval:.0f}초마다 확인합니다(무료).', flush=True)
    f, others = find_recovered(pc, start, exclude, a.recover_wait, a.recover_interval, a.recover_skew)
    if f is None:
        G.finalize(token, 0, 'error', f'{msg} | 서버 결과 {a.recover_wait:.0f}초 동안 못 찾음. '
                                      f'청구됐을 수 있음(추정 ${est:.2f}). 다시 시도 전 확인')
        print(f'경고: 서버 결과를 찾지 못했습니다. 그래도 생성·청구됐을 수 있습니다(추정 ${est:.2f}).\n'
              f'  다시 시도하기 전에 몇 분 뒤 무료 확인을 먼저 하세요:\n'
              f'  python3 work/scripts/omni_gen.py --out {a.out} --recover-only '
              f'--recover-since {start.isoformat(timespec="seconds").replace("+00:00", "")}\n'
              f'  그리고 Google 결제 화면을 확인하세요.', file=sys.stderr)
        sys.exit(G.EXIT_UNKNOWN)
    name = file_name(f)
    meta = {'model': MODEL, 'interaction_id': None, 'recovered_file': name, 'extendable': False,
            'other_candidates': [file_name(o) for o in others], 'error': msg, 'prompt': prompt,
            'request_start_utc': start.isoformat(timespec='seconds'),
            'file_create_time': str(getattr(f, 'create_time', '')),
            'cost': {'estimate_usd': est, 'actual_usd': None, 'used_usd': est, 'basis': '사전 추정(되찾은 파일은 토큰 정보 없음)'},
            **settings}
    try:
        path = save_video(pc, f, a.out, getattr(f, 'mime_type', None), a.overwrite)
    except DownloadError as de:
        _write_json(a.out, {**meta, 'downloaded': False})
        G.finalize(token, est, 'ok', f'오류 뒤 서버 파일 {name} 찾음, 내려받기 실패({de}). 추정 ${est:.3f}')
        print(f'경고: 서버 결과 {name}를 찾았지만 내려받지 못했습니다. --recover-only로 다시 받으세요(무료).',
              file=sys.stderr)
        sys.exit(G.EXIT_FETCH)
    meta['output_path'] = os.path.relpath(path)
    meta['seconds_taken'] = round(time.time() - t0)
    _length_check(meta, path, expected_seconds(a))
    _write_json(path, meta)
    G.finalize(token, est, 'ok', f'오류 뒤 서버 파일 {name} 되찾음(interaction id 없음, 연장 불가). '
                                 f'비용은 추정 ${est:.3f}. 오류: {msg[:120]}')
    print(f'되찾음: {path} (서버 파일 {name}). interaction id가 없어 이 결과는 더 연장할 수 없습니다.', flush=True)
    return 0


def recover_only(a):
    """유료 요청 없이 서버 결과만 찾아 받는다."""
    pc = make_poll_client()
    side = os.path.splitext(a.out)[0] + '.json'
    meta = json.load(open(side, encoding='utf-8')) if os.path.exists(side) else None
    if meta and meta.get('downloaded') is False:
        # 생성·장부 기록은 끝났고 내려받기만 실패한 경우
        mime = None
        if meta.get('interaction_id'):
            it = pc.interactions.get(meta['interaction_id'])
            ov = getattr(it, 'output_video', None)
            ref, mime = getattr(ov, 'uri', None), getattr(ov, 'mime_type', None)
        else:
            ref = meta.get('recovered_file') or meta.get('output_file')
        if not ref:
            sys.exit('받을 서버 결과를 json에서 찾지 못함')
        path = save_video(pc, ref, a.out, mime, a.overwrite)
        meta['downloaded'] = True
        meta['output_path'] = os.path.relpath(path)
        _length_check(meta, path, meta.get('expected_seconds'))
        _write_json(path, meta)
        print('받음:', path)
        return 0
    G.refuse_existing(a.out, a.overwrite)
    pend = G.pending_rows(a.out)
    if a.recover_since:
        since = _utc(a.recover_since)
    elif pend:
        since = _utc(pend[-1]['time_utc'])
    else:
        sys.exit('--recover-since(UTC 시각)가 필요합니다(이 --out에 진행 중 장부 행이 없음)')
    exclude = referenced_names([os.path.dirname(os.path.abspath(a.out))])
    print(f'{since.isoformat(timespec="seconds")} 뒤에 생긴 서버 결과를 찾습니다(무료).', flush=True)
    f, others = find_recovered(pc, since, exclude, a.recover_wait, a.recover_interval, a.recover_skew)
    if f is None:
        print('서버 결과를 찾지 못했습니다. 장부의 진행 중 행은 그대로 둡니다(상한 계산에 예상액으로 남음).',
              file=sys.stderr)
        sys.exit(G.EXIT_UNKNOWN)
    name = file_name(f)
    extension = bool(a.extend_from or a.extend_video)
    est = float(pend[-1]['est_usd']) if pend else estimate_usd(a.resolution, a.duration, extension)
    path = save_video(pc, f, a.out, getattr(f, 'mime_type', None), a.overwrite)
    settings = {'resolution': a.resolution, 'duration': a.duration, 'recover_only': True}
    meta = {'model': MODEL, 'interaction_id': None, 'recovered_file': name, 'extendable': False,
            'other_candidates': [file_name(o) for o in others], 'request_start_utc': since.isoformat(timespec='seconds'),
            'file_create_time': str(getattr(f, 'create_time', '')), 'output_path': os.path.relpath(path),
            'cost': {'estimate_usd': est, 'actual_usd': None, 'used_usd': est, 'basis': '사전 추정'}, **settings}
    _length_check(meta, path, None)
    _write_json(path, meta)
    note = f'따로 되찾음: 서버 파일 {name}(interaction id 없음, 연장 불가). 비용은 추정 ${est:.3f}'
    if pend and pend[-1]['token']:
        G.finalize(pend[-1]['token'], est, 'ok', note)
    else:
        G.log('video', MODEL, settings, est, 'ok', path, note)
    print(f'되찾음: {path} (서버 파일 {name})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
