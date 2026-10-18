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
- 유료 실행(생성·되찾기)은 한 번에 하나만 돈다(장부 옆 .paid_run.lock, 잡혀 있으면 13으로 끝냄).
- --resolution은 꼭 적는다(기본값 없음). 연장할 때 앞 결과 json의 해상도와 다르면 보내지 않는다.
- 요청 직전에 장부에 pending 행(예상액, 해상도·길이·연장 설정 포함)을 적고, 끝나면 결과로 바꾼다.
- 예산 파일(work/final/budget.json)의 상한·80% 보고선을 넘으면 보내지 않는다(--allow-over-warn).
  장부에 적기 직전에 장부 잠금 안에서 한 번 더 확인한다.
- 같은 --out에 앞 유료 요청의 json(interaction id·되찾기 정보)이나 미확정(pending·unresolved) 장부 행이 있으면
  보내지 않는다(12). 먼저 --recover-only로 받거나, 결제 화면을 확인한 뒤 --new-attempt-after-billing-check.
- interaction id를 받은 뒤(일반 요청의 응답, --background, --stream 첫 이벤트)에는 서버 결과를 get(무료)으로만 확인한다.
  in_progress·queued·requires_action이면 끝날 때까지 --poll-wait초 동안 기다린다. 그래도 안 끝나면
  unresolved(예상액 유지)로 두고 20으로 끝낸다(--recover-only로 나중에 다시 확인).
  failed·cancelled는 응답 토큰에 영상 출력이 없다고 나올 때만 0달러로 본다.
- 요청이 끊기거나(연결 끊김·시간 초과·5XX 등) 오류가 나고 interaction id가 없으면 **다시 보내지 않는다.**
  대신 files.list()에서 요청 시작 뒤에 생긴 GENERATED 영상(요청 전 목록·기존 json·장부에 이미 적힌 이름 제외)을
  기본 6분 동안 20초마다 찾는다. 후보가 딱 하나이고 다른 미확정 요청이 없을 때만 자동으로 받는다
  (json: interaction_id 없음, 연장 불가 / 장부: ok, 예상액). 후보가 여럿이거나 다른 미확정 요청이 있으면
  고르지 않고 후보를 json에 적은 뒤 20으로 끝낸다(--recover-only --recover-file files/이름 으로 직접 고름).
  못 찾으면 장부에 unresolved(예상액 그대로, 상한·80% 계산에 들어감)로 남기고 20으로 끝낸다.
  0달러로 바꾸는 것은 사람이 결제 화면을 확인한 뒤의 mark-not-billed뿐이다(gen_api.py 머리말).
- 즉시 거절(400·401·403·404·422, invalid_request)은 청구되지 않은 것으로 보고 바로 끝낸다.
- 되찾은 결과(interaction id 없음)나 스트리밍 생성은 다음 연장의 재료로 쓸 수 없어 --extend-from에서 거절한다.

종료 코드: 0 성공(되찾기 포함), 2 인자 오류, 10 상한 초과, 11 80% 보고선, 12 출력 파일·앞 요청 기록·미확정 행 있음,
          13 다른 유료 실행이 진행 중, 20 결과를 확정하지 못함(청구됐을 수 있음, 장부 unresolved), 21 즉시 거절,
          22 서버가 실패·영상 없음으로 끝냄, 23 생성은 됐으나 내려받기 실패(--recover-only로 다시 받기)

사용(저장소 루트):
  python3 work/scripts/omni_gen.py --out work/omni/A.mp4 --first 032_83Tower.png --last 040_83Tower.png \
      --prompt-file work/omni/prompts/A.txt --resolution 360p --duration 8
  # 연장: 앞 결과의 json에 저장된 interaction id 사용(해상도는 앞 결과와 같아야 함)
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --extend-from work/omni/A.json \
      --prompt-file work/omni/prompts/B.txt --resolution 360p --duration 8
  # background: id를 바로 받아 json·장부에 적고, 끝날 때까지 get으로 확인(긴 요청 하나로 기다리지 않음)
  python3 work/scripts/omni_gen.py --out work/omni/T1.mp4 --first 008c.png --prompt-file A1.txt \
      --resolution 360p --duration 4 --background
  # (무료) 끊긴 요청·죽은 프로세스·내려받기 실패 뒤: 서버 결과만 찾아서 받기(json·장부 행의 설정을 그대로 씀)
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --recover-only [--recover-since 2026-10-18T01:23:45]
  python3 work/scripts/omni_gen.py --out work/omni/B.mp4 --recover-only --recover-file files/abc123   # 후보 직접 고르기
  # (사람이 결제 화면을 확인한 뒤에만) 청구 여부를 몰라 예상액으로 잡아 둔 행을 0달러로
  python3 work/scripts/omni_gen.py --mark-not-billed 0123abcd4567 --reason "결제 화면에 그 시각 청구 없음"
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
# 아직 끝나지 않은 상태: 서버가 계속 만들고 청구할 수 있다
WAITING = ('in_progress', 'queued', 'requires_action')
# 응답에 영상 출력 토큰이 없다고 나올 때만 0달러로 보는 실패 상태
FREE_FAIL = ('failed', 'cancelled')


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


def find_candidates(pc, since, exclude, wait, interval, skew):
    """since(UTC) - skew 뒤에 생긴, exclude에 없는 생성 영상을 wait초 동안 찾는다. 찾은 후보 목록(오래된 순, 없으면 [])."""
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
            return ready
        left = wait - (time.time() - t0)
        if left <= 0:
            return []
        print(f'  서버 결과 아직 없음({n}회 확인, {time.time() - t0:.0f}초 경과)', flush=True)
        time.sleep(min(interval, left))


def status_of(it):
    """interaction 상태 문자열(소문자). interaction이 없으면 None."""
    if it is None:
        return None
    v = getattr(it, 'status', 'completed')
    v = getattr(v, 'value', v)
    return str(v or 'unknown').lower()


def poll_interaction(pc, iid, it=None, wait=0.0, interval=20.0):
    """interaction을 get(무료, 다시 해도 안전)으로 확인한다. 아직 안 끝났으면(in_progress 등) wait초 동안 기다린다.
    (마지막으로 받은 interaction, 상태). 한 번도 못 받았고 생성 응답도 없으면 상태는 None."""
    t0, n, errs = time.time(), 0, 0
    while True:
        n += 1
        try:
            got = pc.interactions.get(iid)
            errs = 0
            if got is not None:
                it = got
        except Exception as e:
            errs += 1
            print(f'  결과 확인 실패({n}회): {G.scrub(e)[:150]}', flush=True)
        st = status_of(it)
        if st is not None and st not in WAITING:
            return it, st
        left = wait - (time.time() - t0)
        if left <= 0 or (st is None and errs >= 6):
            return it, st
        print(f'  아직 {st or "확인 못 함"}({time.time() - t0:.0f}초 경과, 최대 {wait:.0f}초 기다림)', flush=True)
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
        prev = _load_json(a.extend_from)
        base = prev.get('chain_seconds') or probe_seconds(os.path.splitext(a.extend_from)[0] + '.mp4')
        return round(base + a.duration, 3) if base else None
    if a.extend_video:
        base = probe_seconds(a.extend_video)
        return round(base + a.duration, 3) if base else None
    return float(a.duration)


def _load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def _write_json(path, meta):
    # background 요청은 영상을 받기 전에 id부터 적으므로, 출력 폴더가 아직 없을 수 있다
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
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
    ap.add_argument('--out', help='출력 mp4(생성·되찾기에 꼭 필요)')
    ap.add_argument('--first')
    ap.add_argument('--last')
    ap.add_argument('--extend-from', help='앞 생성 결과 json(previous interaction id가 들어 있음)')
    ap.add_argument('--extend-video', help='연장할 영상 파일(10초 이하). 업로드해서 이어 만든다')
    ap.add_argument('--prompt-file', help='프롬프트 파일(생성에는 꼭 필요)')
    ap.add_argument('--resolution', default=None, choices=list(VIDEO_TOKENS_PER_SEC),
                    help='해상도(생성에는 꼭 적어야 함. 기본값 없음)')
    ap.add_argument('--duration', type=int, default=None, help='새로 만들 길이(초, 3~10, 생성 기본 8)')
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument('--stream', action='store_true',
                      help='진행 이벤트를 받으며 기다림. 스트리밍 생성은 다음 연장의 재료로 쓸 수 없음')
    mode.add_argument('--background', action='store_true',
                      help='서버에서 돌리고 interaction id를 바로 받아 json·장부에 적은 뒤 get으로 끝날 때까지 확인')
    G.add_safety_args(ap, True)
    ap.add_argument('--overwrite', action='store_true', help='출력 mp4가 이미 있어도 진행(기본은 거절)')
    ap.add_argument('--new-attempt-after-billing-check', action='store_true',
                    help='같은 --out에 앞 요청의 json·미확정 장부 행이 있어도 새 유료 요청을 보냄'
                         '(먼저 --recover-only와 결제 화면을 확인한 뒤에만. 앞 json은 .prev_시각.json으로 옮겨 둠)')
    ap.add_argument('--poll-wait', type=float, default=1800,
                    help='interaction id를 알 때 끝날 때까지 get으로 기다리는 시간(초, 기본 30분)')
    ap.add_argument('--recover-wait', type=float, default=360,
                    help='id 없이 끊긴 뒤 서버 파일 목록에서 결과를 찾는 시간(초, 기본 6분)')
    ap.add_argument('--recover-interval', type=float, default=20, help='상태·파일 목록 확인 간격(초)')
    ap.add_argument('--recover-skew', type=float, default=30, help='시계 차이 여유(초)')
    ap.add_argument('--recover-only', action='store_true',
                    help='유료 요청 없이 서버 결과만 찾아 받기(끊김·프로세스 죽음·내려받기 실패 뒤)')
    ap.add_argument('--recover-since', help='--recover-only: 이 UTC 시각 뒤 결과만(ISO, 예 2026-10-18T01:23:45)')
    ap.add_argument('--recover-file', help='--recover-only: 받을 서버 파일을 직접 고름(예 files/abc123)')
    ap.add_argument('--mark-not-billed', metavar='표식',
                    help='(사람이 결제 화면을 확인한 뒤에만) 미확정 장부 행을 0달러(not_billed)로. --reason 필요')
    ap.add_argument('--reason', help='--mark-not-billed: 결제 화면에서 확인한 내용')
    return ap


def main(argv=None):
    ap = build_parser()
    a = ap.parse_args(argv)
    G.no_debug_env()
    if a.mark_not_billed:
        return G.mark_not_billed(a.mark_not_billed, a.reason)
    if not a.out:
        ap.error('--out이 필요합니다')
    with G.paid_run_lock(('recover-only ' if a.recover_only else 'omni ') + a.out):
        if a.recover_only:
            return recover_only(a)
        return generate(a, ap)


def sidecar(out):
    return os.path.splitext(out)[0] + '.json'


def refuse_unfinished(a):
    """같은 --out에 앞 유료 요청의 json(interaction id·되찾기 정보)이나 미확정 장부 행이 있으면 보내지 않는다(12)."""
    side = sidecar(a.out)
    rows = G.unsettled_rows(a.out)
    has_json = os.path.exists(side)
    if not has_json and not rows:
        return
    if a.new_attempt_after_billing_check:
        if has_json:
            stamp = dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S')
            keep = G.free_path(os.path.splitext(side)[0] + f'.prev_{stamp}.json')
            os.replace(side, keep)
            print(f'주의: 앞 요청 기록을 {keep}(으)로 옮겨 두고 새 요청을 보냅니다(--new-attempt-after-billing-check).',
                  flush=True)
        if rows:
            print('주의: 이 출력의 미확정 장부 행은 예상액 그대로 상한에 남습니다.', flush=True)
        return
    msgs = []
    if has_json:
        msgs.append(f'앞 유료 요청의 기록이 있습니다: {side} (interaction id·서버 파일 이름이 들어 있을 수 있음).\n'
                    f'  먼저 무료로 결과를 받으세요: python3 work/scripts/omni_gen.py --out {a.out} --recover-only')
    if rows:
        msgs.append(G.unsettled_hint(rows))
    print('\n'.join(msgs) + '\n같은 요청을 다시 보내면 두 번 청구될 수 있어 보내지 않습니다.', file=sys.stderr)
    sys.exit(G.EXIT_EXISTS)


def recover_hint(a, start):
    cmd = (f'python3 work/scripts/omni_gen.py --out {a.out} --recover-only '
           f'--resolution {a.resolution} --duration {a.duration}')
    if a.extend_from:
        cmd += f' --extend-from {a.extend_from}'
    if a.extend_video:
        cmd += f' --extend-video {a.extend_video}'
    return cmd + f' --recover-since {start.isoformat(timespec="seconds").replace("+00:00", "")}'


def generate(a, ap):
    if not a.prompt_file:
        ap.error('--prompt-file이 필요합니다')
    if not a.resolution:
        ap.error('--resolution을 꼭 적어 주세요(360p|720p|1080p|4k). 실수로 다른 해상도를 만들지 않도록 기본값이 없습니다')
    if a.duration is None:
        a.duration = 8
    if not 3 <= a.duration <= 10:
        ap.error('--duration은 3~10초입니다')

    extension = bool(a.extend_from or a.extend_video)
    est = estimate_usd(a.resolution, a.duration, extension)
    prev_id = None
    if a.extend_from:
        prev = _load_json(a.extend_from)
        prev_id = prev.get('interaction_id')
        if not prev_id or prev.get('extendable') is False:
            print(f'{a.extend_from}: 이 결과는 연장 재료로 쓸 수 없습니다(되찾은 파일이거나 스트리밍 생성이라 '
                  f'interaction id가 없거나 연장 불가). 유료 요청을 보내지 않음', file=sys.stderr)
            sys.exit(2)
        if prev.get('resolution') and prev['resolution'] != a.resolution:
            print(f'{a.extend_from}: 앞 결과는 {prev["resolution"]}인데 --resolution {a.resolution}입니다. '
                  f'한 줄기 안에서 해상도를 바꾸지 않습니다. 유료 요청을 보내지 않음', file=sys.stderr)
            sys.exit(2)
    refuse_unfinished(a)
    G.refuse_existing(a.out, a.overwrite)
    G.guard(est, a.cap, a.budget_file, a.allow_over_warn)
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
    # 장부 pending 행에도 남겨 --recover-only가 같은 설정·예상액으로 정리할 수 있게 한다
    settings = {'resolution': a.resolution, 'duration': a.duration, 'first': a.first, 'last': a.last,
                'extend_from': a.extend_from, 'extend_video': a.extend_video,
                'mode': 'background' if a.background else 'stream' if a.stream else 'normal',
                'expected_seconds': expected_seconds(a)}

    # 되찾기 준비(무료): 지금 서버에 있는 생성 영상 + 이미 기록된 이름은 후보에서 뺀다
    exclude = referenced_names([os.path.dirname(os.path.abspath(a.out))])
    try:
        exclude |= {file_name(f) for f in list_generated(pc)}
    except Exception as e:
        print(f'주의: 요청 전 서버 파일 목록을 못 받음(시각 조건만으로 되찾기): {G.scrub(e)[:150]}', flush=True)

    paid = make_paid_client()
    G.once('omni')
    token = G.log_pending('video', MODEL, settings, est, a.out, f'{a.resolution} {a.duration}초 요청',
                          limits=dict(cap=a.cap, budget_file=a.budget_file, allow_over_warn=a.allow_over_warn))
    start = dt.datetime.now(dt.timezone.utc)
    t0 = time.time()
    print(f'요청 시작 {start.isoformat(timespec="seconds")} (UTC), 예상 ${est:.3f}, 장부 표식 {token}', flush=True)
    meta = {'model': MODEL, 'interaction_id': None, 'extendable': not a.stream, 'prompt': prompt,
            'request_start_utc': start.isoformat(timespec='seconds'), 'call_token': token, **settings}
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
        elif a.background:
            it = paid.interactions.create(background=True, **kwargs)
            iid = getattr(it, 'id', None)
            if not iid:
                raise RuntimeError('interaction id를 받지 못함(background)')
            meta['interaction_id'] = iid
            # 바로 남긴다: 이 뒤로 프로세스가 죽어도 --recover-only가 이 id로 결과를 받는다
            _write_json(a.out, {**meta, 'downloaded': False, 'status': status_of(it), 'ledger': 'pending'})
            G.annotate(token, f'background interaction {iid}')
            print(f'background 요청 접수: interaction {iid}. 끝날 때까지 {a.recover_interval:.0f}초마다 확인합니다'
                  f'(무료, 최대 {a.poll_wait:.0f}초)', flush=True)
        else:
            it = paid.interactions.create(**kwargs)
            iid = getattr(it, 'id', None)
            if not iid:
                raise RuntimeError('interaction id를 받지 못함')
    except Exception as e:
        return after_failure(a, pc, token, est, e, start, t0, exclude, meta, iid)
    meta['create_seconds'] = round(time.time() - t0)
    return settle(a, pc, token, est, iid, it, meta, t0)


def settle(a, pc, token, est, iid, it, meta, t0):
    """interaction id를 아는 유료 요청을 마무리한다(무료 확인만): 끝날 때까지 기다리고, 받고, json·장부를 정리한다."""
    it, status = poll_interaction(pc, iid, it, a.poll_wait, a.recover_interval)
    usage = usage_dict(getattr(it, 'usage', None)) if it is not None else None
    actual, detail = usage_cost(usage)
    cost = actual if actual is not None else est
    meta.update(interaction_id=iid, status=status, usage=usage)
    meta['cost'] = {'estimate_usd': est, 'actual_usd': actual, 'used_usd': cost, 'tokens': detail,
                    'basis': '응답 토큰 x 단가' if actual is not None else '사전 추정(토큰 정보 없음)'}
    if status is None or status in WAITING:
        what = '상태를 확인하지 못함' if status is None else f'아직 {status}'
        meta['cost']['used_usd'] = est
        _write_json(a.out, {**meta, 'downloaded': False, 'ledger': 'unresolved'})
        G.finalize(token, est, 'unresolved', f'interaction {iid}: {what}({a.poll_wait:.0f}초 기다림). '
                                             f'청구됐을 수 있음 → 예상 ${est:.3f} 유지. --recover-only로 다시 확인')
        print(f'경고: interaction {iid}: {what}. 서버는 계속 만들고 청구할 수 있습니다(예상 ${est:.2f}, 장부 unresolved).\n'
              f'  다시 보내지 말고, 나중에 무료로 다시 확인하세요:\n'
              f'  python3 work/scripts/omni_gen.py --out {a.out} --recover-only', file=sys.stderr)
        sys.exit(G.EXIT_UNKNOWN)
    if status != 'completed':
        if actual:
            G.finalize(token, actual, 'ok', f'status={status}, 응답에 영상 출력 토큰 있음(청구된 것으로 봄). interaction {iid}')
            code = G.EXIT_FAILED
        elif status in FREE_FAIL and isinstance(usage, dict):
            G.finalize(token, 0, 'failed', f'status={status}, 응답 토큰에 영상 출력 없음. interaction {iid}')
            code = G.EXIT_FAILED
        else:
            meta['cost']['used_usd'] = est
            _write_json(a.out, {**meta, 'downloaded': False, 'ledger': 'unresolved'})
            G.finalize(token, est, 'unresolved', f'status={status}, 토큰 정보로 청구 여부를 알 수 없음 → 예상 ${est:.3f} 유지. '
                                                 f'interaction {iid}')
            code = G.EXIT_UNKNOWN
        print(f'생성 실패: status={status}' + (' (청구 여부 모름: 장부 unresolved, 결제 화면 확인 필요)'
                                              if code == G.EXIT_UNKNOWN else ''), file=sys.stderr)
        sys.exit(code)
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
        _write_json(a.out, {**meta, 'downloaded': False, 'ledger': 'ok'})
        G.finalize(token, cost, 'ok', f'생성됨, 내려받기 실패({e}). --recover-only로 다시 받기. interaction {iid}')
        print('경고: 생성은 됐지만 내려받기에 실패했습니다. --recover-only로 다시 받으세요(무료).', file=sys.stderr)
        sys.exit(G.EXIT_FETCH)
    meta['download_seconds'] = round(time.time() - t1)
    meta['seconds_taken'] = round(time.time() - t0)
    meta['output_path'] = os.path.relpath(path)
    meta['ledger'] = 'ok'
    _length_check(meta, path, meta.get('expected_seconds'))
    _write_json(path, meta)
    create_sec = meta.get('create_seconds')
    if actual is not None:
        note = f'응답 토큰 기준 ${actual:.3f}(사전 추정 ${est:.3f}), 생성 {create_sec}초'
    else:
        note = f'사전 추정 ${est:.3f}(토큰 정보 없음), 생성 {create_sec}초'
    G.finalize(token, cost, 'ok', f'{note}, interaction {iid}')
    print('저장:', path, '| 걸린 시간', meta['seconds_taken'], '초 | 비용', f'${cost:.3f}', '| interaction', iid)
    return 0


def after_failure(a, pc, token, est, e, start, t0, exclude, meta, iid=None):
    """유료 요청이 오류로 끝났을 때: 다시 보내지 않고, 서버에서 완성됐는지 확인한다."""
    code = G.status_code_of(e)
    msg = G.scrub(f'{type(e).__name__}: {e}')[:300]
    took = time.time() - t0
    meta['error'] = msg
    if iid:
        # 스트림 첫 이벤트·background 응답으로 id를 이미 받았으면 그 id로만 확인한다(파일 목록으로 짐작하지 않음)
        print(f'요청 오류({took:.0f}초 뒤): {msg}\n'
              f'  interaction id({iid})를 이미 받았으므로 다시 보내지 않고 get으로 결과를 확인합니다(무료).', flush=True)
        return settle(a, pc, token, est, iid, None, meta, t0)
    if code in G.REJECT_CODES or (code is None and 'invalid_request' in msg):
        G.finalize(token, 0, 'error', f'즉시 거절 {msg}')
        print(f'요청이 즉시 거절됨({code or "invalid_request"}, {took:.0f}초): {msg}', file=sys.stderr)
        sys.exit(G.EXIT_REJECTED)
    print(f'요청 오류({took:.0f}초 뒤): {msg}\n'
          f'  같은 요청을 다시 보내지 않습니다. 서버에서 끝까지 만들어졌는지 파일 목록을 '
          f'최대 {a.recover_wait:.0f}초 동안 {a.recover_interval:.0f}초마다 확인합니다(무료).', flush=True)
    cands = find_candidates(pc, start, exclude, a.recover_wait, a.recover_interval, a.recover_skew)
    others = [r for r in G.unsettled_rows() if r['token'] != token]
    if len(cands) == 1 and not others:
        return adopt(a, pc, cands[0], token, est, meta, t0,
                     lambda name: f'오류 뒤 서버 파일 {name} 되찾음(interaction id 없음, 연장 불가). '
                                  f'비용은 추정 ${est:.3f}. 오류: {msg[:120]}')
    # 못 찾았거나, 이 요청의 결과인지 확실하지 않음 → 청구 여부 모름(예상액 그대로 상한에 남김)
    names = [file_name(f) for f in cands]
    _write_json(a.out, {**meta, 'downloaded': False, 'ledger': 'unresolved', 'candidates': names,
                        'cost': {'estimate_usd': est, 'actual_usd': None, 'used_usd': est, 'basis': '사전 추정'}})
    hint = recover_hint(a, start)
    if not cands:
        G.finalize(token, est, 'unresolved', f'{msg} | 서버 결과 {a.recover_wait:.0f}초 동안 못 찾음. '
                                             f'청구됐는지 모름 → 예상 ${est:.3f} 유지')
        print(f'경고: 서버 결과를 찾지 못했습니다. 그래도 생성·청구됐을 수 있습니다(추정 ${est:.2f}).\n'
              f'  장부에는 unresolved(예상액 그대로, 상한·80% 계산에 들어감)로 남겼습니다. 표식: {token}\n'
              f'  다시 보내지 말고, 몇 분 뒤 무료 확인을 먼저 하세요:\n'
              f'  {hint}\n'
              f'  결과가 끝내 없으면 Google 결제 화면을 확인하고, 청구가 없었을 때만:\n'
              f'  python3 work/scripts/omni_gen.py --mark-not-billed {token} --reason "확인 내용"', file=sys.stderr)
    else:
        why = (f'후보가 {len(names)}개' if len(names) > 1 else
               f'다른 미확정 요청({", ".join(str(r["token"]) for r in others)})의 늦은 결과일 수 있음')
        G.finalize(token, est, 'unresolved', f'{msg} | 서버 결과 후보를 자동으로 고르지 않음({why}, 후보는 json에). '
                                             f'예상 ${est:.3f} 유지')
        print(f'경고: 서버 결과 후보를 자동으로 고르지 않았습니다({why}): {names}\n'
              f'  장부에는 unresolved(예상액 그대로)로 남겼습니다. 표식: {token}. 후보는 {sidecar(a.out)}에 적었습니다.\n'
              f'  길이·만든 시각으로 이 요청의 것을 확인한 뒤 직접 고르세요(무료):\n'
              f'  python3 work/scripts/omni_gen.py --out {a.out} --recover-only --recover-file <후보 이름>',
              file=sys.stderr)
    sys.exit(G.EXIT_UNKNOWN)


def adopt(a, pc, f, token, est, meta, t0, note_fn):
    """id 없이 찾은 서버 파일 하나를 이 요청의 결과로 받는다(장부 ok, 예상액)."""
    name = file_name(f)
    meta = {**meta, 'interaction_id': None, 'recovered_file': name, 'extendable': False,
            'file_create_time': str(getattr(f, 'create_time', '')),
            'cost': {'estimate_usd': est, 'actual_usd': None, 'used_usd': est,
                     'basis': '사전 추정(되찾은 파일은 토큰 정보 없음)'}}
    meta.pop('candidates', None)
    try:
        path = save_video(pc, f, a.out, getattr(f, 'mime_type', None), a.overwrite)
    except DownloadError as de:
        _write_json(a.out, {**meta, 'downloaded': False, 'ledger': 'ok'})
        G.finalize(token, est, 'ok', f'서버 파일 {name} 찾음, 내려받기 실패({de}). 추정 ${est:.3f}')
        print(f'경고: 서버 결과 {name}를 찾았지만 내려받지 못했습니다. --recover-only로 다시 받으세요(무료).',
              file=sys.stderr)
        sys.exit(G.EXIT_FETCH)
    meta.update(downloaded=True, ledger='ok', output_path=os.path.relpath(path), seconds_taken=round(time.time() - t0))
    _length_check(meta, path, meta.get('expected_seconds'))
    _write_json(path, meta)
    G.finalize(token, est, 'ok', note_fn(name))
    print(f'되찾음: {path} (서버 파일 {name}). interaction id가 없어 이 결과는 더 연장할 수 없습니다.', flush=True)
    return 0


def recover_only(a):
    """유료 요청 없이 서버 결과만 찾아 받는다(무료).

    설정·예상액은 json → 이 출력의 미확정 장부 행 → 명령줄 순서로 쓴다. 장부에 맞는 행이 있으면 그 행을 ok로 바꾸고,
    json도 장부 행도 없으면 --resolution과 --duration을 꼭 받아 새 ok 행을 적는다(예상액이 틀리지 않게).
    """
    side = sidecar(a.out)
    meta = _load_json(side) if os.path.exists(side) else None
    if os.path.exists(a.out) and not a.overwrite:
        print(f'출력 파일이 이미 있습니다: {a.out}. 되찾을 것이 없거나 다른 --out을 써야 합니다(덮어쓰려면 --overwrite).',
              file=sys.stderr)
        sys.exit(G.EXIT_EXISTS)
    rows = G.unsettled_rows(a.out)
    tok = (meta or {}).get('call_token')
    row = next((r for r in rows if tok and r['token'] == tok), rows[-1] if rows else None)
    rs = G.row_settings(row) if row else {}

    def pick(k):
        for src in (meta or {}, rs):
            if src.get(k) is not None:
                return src[k]
        return getattr(a, k, None)
    if meta is None and row is None and (a.resolution is None or a.duration is None):
        print('이 --out의 json도 미확정 장부 행도 없습니다. 장부에 맞는 금액을 적으려면 '
              '--resolution과 --duration(연장이면 --extend-from 또는 --extend-video도)을 꼭 적어 주세요.', file=sys.stderr)
        sys.exit(2)
    resolution, duration = pick('resolution'), pick('duration')
    settings = {k: pick(k) for k in ('resolution', 'duration', 'first', 'last', 'extend_from', 'extend_video', 'mode',
                                     'expected_seconds')}
    settings['recover_only'] = True
    if row is not None:
        est = float(row['est_usd'])
    elif meta and (meta.get('cost') or {}).get('estimate_usd') is not None:
        est = float(meta['cost']['estimate_usd'])
    else:
        est = estimate_usd(resolution, int(duration), bool(pick('extend_from') or pick('extend_video')))
    settled = meta is not None and row is None and meta.get('ledger', 'ok') == 'ok'  # 장부는 이미 ok(내려받기만 실패)

    own = set()
    if meta:
        own = {f'files/{m}' for m in NAME_RE.findall(json.dumps(meta, default=str))}
    pc = make_poll_client()
    iid = (meta or {}).get('interaction_id')
    ref, mime, actual, f_obj, extendable = None, None, None, None, False
    if a.recover_file:
        ref = file_name(a.recover_file)
        taken = referenced_names([os.path.dirname(os.path.abspath(a.out))]) - own
        if ref in taken:
            print(f'{ref}는 이미 다른 결과(json·장부)에 기록된 파일입니다. 받지 않음', file=sys.stderr)
            sys.exit(2)
    elif iid:
        it, st = poll_interaction(pc, iid, None, a.poll_wait, a.recover_interval)
        if st is None or st in WAITING:
            print(f'interaction {iid}: {"확인 못 함" if st is None else "아직 " + st}. 장부는 그대로 둡니다. 나중에 다시 확인하세요.',
                  file=sys.stderr)
            sys.exit(G.EXIT_UNKNOWN)
        usage = usage_dict(getattr(it, 'usage', None))
        actual, _ = usage_cost(usage)
        if st != 'completed':
            if row is not None and actual:
                G.finalize(row['token'], actual, 'ok', f'status={st}, 응답에 영상 출력 토큰 있음. interaction {iid}')
            elif row is not None and st in FREE_FAIL and isinstance(usage, dict):
                G.finalize(row['token'], 0, 'failed', f'status={st}, 응답 토큰에 영상 출력 없음. interaction {iid}')
            print(f'interaction {iid}: status={st}. 받을 영상이 없습니다.', file=sys.stderr)
            sys.exit(G.EXIT_FAILED)
        ov = getattr(it, 'output_video', None)
        ref, mime = getattr(ov, 'uri', None), getattr(ov, 'mime_type', None)
        extendable = bool((meta or {}).get('extendable', True))
        if not ref:
            print(f'interaction {iid}: 완료됐지만 영상 주소가 없습니다.', file=sys.stderr)
            sys.exit(G.EXIT_FAILED)
    elif meta and (meta.get('recovered_file') or meta.get('output_file')):
        ref = meta.get('recovered_file') or meta.get('output_file')
    else:
        if a.recover_since:
            since = _utc(a.recover_since)
        elif meta and meta.get('request_start_utc'):
            since = _utc(meta['request_start_utc'])
        elif row is not None:
            since = _utc(row['time_utc'])
        else:
            sys.exit('--recover-since(UTC 시각)가 필요합니다(이 --out의 json·미확정 장부 행이 없음)')
        exclude = referenced_names([os.path.dirname(os.path.abspath(a.out))]) - own
        print(f'{since.isoformat(timespec="seconds")} 뒤에 생긴 서버 결과를 찾습니다(무료).', flush=True)
        cands = find_candidates(pc, since, exclude, a.recover_wait, a.recover_interval, a.recover_skew)
        others = [r for r in G.unsettled_rows() if not G.same_output(r['output'], a.out)]
        if not cands:
            print('서버 결과를 찾지 못했습니다. 장부의 미확정 행은 그대로 둡니다(상한 계산에 예상액으로 남음).',
                  file=sys.stderr)
            sys.exit(G.EXIT_UNKNOWN)
        if len(cands) > 1 or others:
            names = [file_name(f) for f in cands]
            if meta is not None:
                _write_json(a.out, {**meta, 'candidates': names})
            why = (f'후보가 {len(names)}개' if len(names) > 1 else
                   f'다른 미확정 요청({", ".join(str(r["token"]) for r in others)})의 늦은 결과일 수 있음')
            print(f'자동으로 고르지 않았습니다({why}): {names}\n'
                  f'  길이·만든 시각으로 확인한 뒤 --recover-file <이름>으로 직접 고르세요. 장부는 그대로 둡니다.',
                  file=sys.stderr)
            sys.exit(G.EXIT_UNKNOWN)
        f_obj = cands[0]
        ref, mime = f_obj, getattr(f_obj, 'mime_type', None)

    path = save_video(pc, ref, a.out, mime, a.overwrite)
    name = file_name(ref)
    cost = actual if actual is not None else est
    new = dict(meta or {})
    new.pop('candidates', None)
    new.update({k: v for k, v in settings.items() if v is not None})
    new.update(model=MODEL, downloaded=True, ledger='ok', output_path=os.path.relpath(path))
    if iid and not a.recover_file:
        new.update(interaction_id=iid, output_file=name, extendable=extendable)
    else:
        new.update(interaction_id=None, recovered_file=name, extendable=False)
    if f_obj is not None:
        new['file_create_time'] = str(getattr(f_obj, 'create_time', ''))
    if not settled:
        new['cost'] = {'estimate_usd': est, 'actual_usd': actual, 'used_usd': cost,
                       'basis': '응답 토큰 x 단가' if actual is not None else '사전 추정'}
    _length_check(new, path, pick('expected_seconds'))
    _write_json(path, new)
    note = (f'따로 되찾음: 서버 파일 {name}' + (f'(interaction {iid})' if iid and not a.recover_file else
                                          '(interaction id 없음, 연장 불가)') + f'. 비용 ${cost:.3f}'
            + (' 응답 토큰 기준' if actual is not None else ' 추정'))
    if row is not None:
        G.finalize(row['token'], cost, 'ok', note)
    elif not settled:
        G.log('video', MODEL, settings, cost, 'ok', path, note)
    print(f'되찾음: {path} (서버 파일 {name})')
    return 0


if __name__ == '__main__':
    sys.exit(main())
