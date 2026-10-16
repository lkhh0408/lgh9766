"""Gemini API 유료 생성 호출(이미지 편집, Veo 영상)과 비용 장부·예산 지킴이.

모든 유료 호출은 실행 전에 예상 비용을 장부(cost_ledger.csv)에 더해 보고,
누적액이 상한을 넘으면 실행하지 않는다. 단가는 Gemini API 유료 등급 가격표 기준이며,
실제 청구액은 Google 결제 화면에서 확인해야 한다.

안전 규칙(2026-10-16 보강, omni_gen.py도 같은 규칙을 쓴다)
- 유료 생성 요청은 한 번 실행에 한 번만 보낸다. SDK 자동 재시도는 끄고, 꺼졌는지 확인한 뒤에만 보낸다.
  (이미지·Veo 경로는 SDK 기본이 1회 시도. 그래도 매번 확인한다.)
- 유료 실행(생성·되찾기·'청구 없음' 표시)은 한 번에 하나만 돈다. 장부 옆 잠금 파일(.paid_run.lock)을
  실행 내내 잡고, 이미 잡혀 있으면 바로 끝낸다(종료 코드 13). 두 실행이 함께 상한 검사를 통과하거나
  서로의 서버 결과를 가져가는 일을 막는다.
- 요청 직전에 장부에 'pending' 행(예상액)을 먼저 적는다. 적기 직전에 장부 잠금 안에서 상한·80% 보고선을 한 번 더 본다.
  pending 행은 상한 계산에 들어간다. 요청이 끝나면 그 행을 결과로 바꾼다.
  - ok: 청구됨(응답 토큰 또는 예상액) / error·failed·no_image·no_video: 즉시 거절·서버 실패로 청구 안 된 것으로 봄(0달러)
  - unresolved: 오류가 났는데 결과를 못 찾음 = **청구됐는지 모름.** 예상액 그대로 상한·80% 계산에 남는다.
    서버 결과를 나중에 찾으면 omni_gen.py --recover-only가 ok로 바꾼다.
    0달러로 바꾸는 길은 하나뿐이다: 사람이 Google 결제 화면에서 청구가 없음을 확인한 뒤
      python3 work/scripts/gen_api.py mark-not-billed <표식> --reason "결제 화면 확인 내용"
    (표식 = 장부 메모의 [call:…] 안 12자리. 결과 행은 not_billed 0달러가 된다.)
  프로세스가 중간에 죽으면 pending이 남아 예상액만큼 계속 잡히므로(보수적), omni_gen.py --recover-only로 정리한다.
- 같은 출력 파일에 미확정(pending·unresolved) 장부 행이 있으면 새 유료 요청을 보내지 않는다(종료 코드 12).
- 예산 파일(기본 work/final/budget.json, 있으면 자동 사용)
    {"ledger_cap_usd": 상한, "warn_at_usd": 80% 보고선, "note": "..."}
  장부 누적(ok+pending+unresolved) + 이번 예상액이 ledger_cap_usd를 넘으면 거절(종료 코드 10),
  warn_at_usd를 넘으면 --allow-over-warn 없이는 거절(종료 코드 11). 보고선에서 멈추고 사용자에게 알리기 위함.
- --cap(또는 COST_CAP_USD)도 그대로 쓸 수 있다. 예산 파일이 없고 --cap도 없으면 30달러.
- API 키 값은 어디에도 출력·기록하지 않는다(오류 문구에서도 지움).
  GOOGLE_GENAI_DEBUG는 요청 머리글(키 포함)을 기록하므로 실행 시 꺼 버린다.
- 장부의 output 칸은 저장소 루트 기준 경로로 적고, 비교할 때는 절대 경로로 맞춰 본다(어느 폴더에서 실행해도 같음).
- 시험용: 장부 경로는 COST_LEDGER_PATH, 예산 파일은 COST_BUDGET_PATH 환경변수로 바꿀 수 있다
  (COST_BUDGET_PATH=none 이면 예산 파일을 쓰지 않음). 잠금 파일은 장부와 같은 폴더에 생긴다.

종료 코드: 10 상한 초과, 11 80% 보고선, 12 출력 파일·미확정 장부 행이 이미 있음, 13 다른 유료 실행이 진행 중,
          20 요청 오류(청구됐을 수 있음, 결과 없음 → unresolved), 21 즉시 거절(4xx, 청구 안 된 것으로 봄),
          22 서버가 실패·결과 없음으로 끝냄, 23 생성은 됐으나 상태 확인·내려받기 실패

사용 예
  # 이미지 편집(첫 이미지가 편집 대상, 나머지는 참조). Pro 모델은 4K 가능($0.24)
  python3 work/scripts/gen_api.py image --model gemini-3-pro-image --size 4K \
      --out work/final/k0/K0_A_raw.png --prompt-file work/final/plan/prompts/keyframe_photoreal_A.txt \
      work/final/s1/keyframes/008c_clean_raw.png

  # 시작·끝 프레임을 지정한 Veo 클립
  python3 work/scripts/gen_api.py video --out work/test1/raw/T1.mp4 \
      --first work/test1/keyframes/008c.png --last 011_83Tower.png \
      --prompt-file work/test1/prompts/T1.txt --model veo-3.1-fast-generate-preview

  # (사람이 결제 화면을 확인한 뒤에만) 청구 여부를 몰라 예상액으로 잡아 둔 행을 0달러로
  python3 work/scripts/gen_api.py mark-not-billed 0123abcd4567 --reason "10/18 결제 화면에 해당 시각 청구 없음"
"""
import argparse
import contextlib
import csv
import datetime as dt
import io
import json
import mimetypes
import os
import re
import sys
import time
import uuid

WORK = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
REPO = os.path.dirname(WORK)
LEDGER = os.path.join(WORK, 'cost_ledger.csv')
DEFAULT_BUDGET = os.path.join(WORK, 'final', 'budget.json')
HEADER = ['time_utc', 'kind', 'model', 'settings', 'est_usd', 'status', 'output', 'note']
# 아직 결과가 확정되지 않은 상태: 진행 중(pending)과 청구 여부 모름(unresolved). 둘 다 예상액으로 잡는다
UNSETTLED = ('pending', 'unresolved')
# 상한·80% 계산에 들어가는 상태: 완료(ok) + 미확정(예상액, 보수적)
BILLED = ('ok',) + UNSETTLED

EXIT_CAP, EXIT_WARN, EXIT_EXISTS, EXIT_BUSY = 10, 11, 12, 13
EXIT_UNKNOWN, EXIT_REJECTED, EXIT_FAILED, EXIT_FETCH = 20, 21, 22, 23
# 즉시 거절로 보는 응답 코드(지금까지 이런 응답은 청구되지 않았음, 장부 기준 추정).
# 408·409·429·5XX·연결 끊김·시간 초과는 서버가 계속 만들 수 있으므로 '모름'으로 다룬다.
REJECT_CODES = {400, 401, 403, 404, 422}

# 달러/초 (오디오 포함 가격, Gemini API 유료 등급)
VIDEO_PRICE = {
    'veo-3.1-fast-generate-preview': {'720p': 0.10, '1080p': 0.12, '4k': 0.30},
    'veo-3.1-generate-preview': {'720p': 0.40, '1080p': 0.40, '4k': 0.60},
    'veo-3.1-lite-generate-preview': {'720p': 0.05, '1080p': 0.08},
}
# 달러/출력 이미지 (Pro 4K = 출력 2,000토큰 x $120/100만)
IMAGE_PRICE = {
    'gemini-3.1-flash-image': {'1K': 0.067, '2K': 0.101},
    'gemini-3-pro-image': {'1K': 0.134, '2K': 0.134, '4K': 0.24},
    'gemini-2.5-flash-image': {'1K': 0.039},
}

NEGATIVE = ('cut, scene transition, morphing, warping or melting buildings, flickering, '
            'zoom, crossfade, slideshow, text, watermark')


# ---------------------------------------------------------------- 키·로그 안전

def no_debug_env():
    # GOOGLE_GENAI_DEBUG가 켜져 있으면 SDK가 요청 머리글(API 키 포함)을 로그로 찍으므로 끈다
    if os.environ.pop('GOOGLE_GENAI_DEBUG', None) is not None:
        print('주의: GOOGLE_GENAI_DEBUG 환경변수는 API 키를 기록할 수 있어 이 실행에서 껐습니다.', file=sys.stderr)


def api_key():
    key = os.environ.get('GEMINI_API_KEY')
    if not key:
        sys.exit('GEMINI_API_KEY 환경변수가 없습니다(값은 출력하지 않음).')
    return key


def scrub(text):
    """문자열에서 API 키 값을 지운다(오류 문구·장부 메모·출력용)."""
    text = str(text)
    for name in ('GEMINI_API_KEY', 'GOOGLE_API_KEY'):
        val = os.environ.get(name)
        if val and len(val) >= 8 and val in text:
            text = text.replace(val, '***')
    return re.sub(r'([?&]key=)[^&\s"\']+', r'\1***', text)


def status_code_of(exc):
    """SDK 예외에서 HTTP 응답 코드를 꺼낸다(없으면 None)."""
    for attr in ('status_code', 'code'):
        v = getattr(exc, attr, None)
        if isinstance(v, int):
            return v
    m = re.match(r'Error code: (\d{3})', str(exc))
    return int(m.group(1)) if m else None


_PAID_ATTEMPTS = {}


def once(kind):
    """유료 생성 요청을 보내기 직전에 부른다. 한 실행에서 두 번째 요청은 막는다."""
    _PAID_ATTEMPTS[kind] = _PAID_ATTEMPTS.get(kind, 0) + 1
    if sum(_PAID_ATTEMPTS.values()) > 1:
        raise RuntimeError('한 번 실행에 유료 요청은 한 번만 보낼 수 있습니다(중복 청구 방지).')


# ---------------------------------------------------------------- 장부

def ledger_path():
    return os.environ.get('COST_LEDGER_PATH') or LEDGER


def ledger_rows():
    p = ledger_path()
    if not os.path.exists(p):
        return []
    with open(p, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def spent():
    # 실패·차단된 생성은 청구되지 않으므로 빼고, ok + 미확정(pending·unresolved, 예상액)을 더한다(보수적)
    return sum(float(r['est_usd']) for r in ledger_rows() if r['status'] in BILLED)


def rel_out(out):
    """장부 output 칸: 저장소 루트 기준 경로(실행 폴더와 상관없이 같은 값)."""
    return os.path.relpath(os.path.abspath(out), REPO)


def same_output(stored, out):
    """장부에 적힌 output이 out과 같은 파일인지. 저장소 루트 기준과 지금 폴더 기준을 모두 맞춰 본다."""
    if not stored or not out:
        return False
    o = os.path.abspath(out)
    if os.path.isabs(stored):
        return os.path.abspath(stored) == o
    return o in (os.path.abspath(stored), os.path.normpath(os.path.join(REPO, stored)))


@contextlib.contextmanager
def _locked():
    # 장부가 있는 폴더 자체에 잠금(잠금 파일을 따로 만들지 않음). 동시에 두 프로세스가 고쳐 쓰지 않게
    import fcntl
    d = os.path.dirname(os.path.abspath(ledger_path()))
    os.makedirs(d, exist_ok=True)
    fd = os.open(d, os.O_RDONLY)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)


def _now():
    return dt.datetime.now(dt.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds')


def _one_line(s):
    return scrub(s).replace('\r', ' ').replace('\n', ' ')


def _row(kind, model, settings, est, status, out, note, when=None):
    return [when or _now(), kind, model, scrub(json.dumps(settings, ensure_ascii=False, default=str)),
            f'{est:.3f}', status, rel_out(out), scrub(note)]


def _append(row):
    p = ledger_path()
    new = not os.path.exists(p)
    with open(p, 'a', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        if new:
            w.writerow(HEADER)
        w.writerow(row)


def log(kind, model, settings, est, status, out, note=''):
    with _locked():
        _append(_row(kind, model, settings, est, status, out, note))


def log_pending(kind, model, settings, est, out, note='', limits=None):
    """요청 직전에 '진행 중' 행을 적고, 나중에 finalize()에 넘길 표식을 돌려준다.

    limits(dict: cap, budget_file, allow_over_warn)를 주면, 장부 잠금 안에서 지금 장부로 상한·80% 보고선을
    한 번 더 확인하고 넘으면 행을 적지 않고 끝낸다(guard()와 요청 사이에 장부가 바뀐 경우 대비).
    """
    token = uuid.uuid4().hex[:12]
    row = _row(kind, model, settings, est, 'pending', out,
               f'[call:{token}] 진행 중(상한 계산에 예상액으로 들어감). {_one_line(note)}'.strip())
    row = [_one_line(c) for c in row]
    with _locked():
        if limits is not None:
            code, msg = limit_check(spent(), est, **limits)[:2]
            if code:
                print(f'요청 직전 다시 확인: {msg}', file=sys.stderr)
                sys.exit(code)
        _append(row)
    return token


def _rewrite(token, change, statuses=UNSETTLED):
    """표식이 붙은 미확정 행 하나를 change(칸 목록)로 고쳐 쓴다. 다른 행은 한 글자도 바꾸지 않는다. 찾으면 True."""
    tag = f'[call:{token}]'
    p = ledger_path()
    if not os.path.exists(p):
        return False
    with open(p, newline='', encoding='utf-8') as f:
        text = f.read()
    lines = text.splitlines(keepends=True)
    for i, line in enumerate(lines):
        if tag not in line:
            continue
        try:
            old = next(csv.reader([line]))
        except (csv.Error, StopIteration):
            continue
        if len(old) != len(HEADER) or old[5] not in statuses or tag not in old[7]:
            continue
        change(old)
        buf = io.StringIO()
        csv.writer(buf).writerow([_one_line(c) for c in old])
        lines[i] = buf.getvalue()
        tmp = p + '.tmp'
        with open(tmp, 'w', newline='', encoding='utf-8') as f:
            f.write(''.join(lines))
        os.replace(tmp, p)
        return True
    return False


def finalize(token, est, status, note=''):
    """미확정(pending·unresolved) 행을 결과 행으로 바꾼다(다른 행은 그대로). 못 찾으면 새 행으로 덧붙인다."""
    tag = f'[call:{token}]'

    def change(old):
        old[4], old[5] = f'{est:.3f}', status
        old[7] = _one_line(f'{tag} {note}')
    with _locked():
        if not _rewrite(token, change):
            # 미확정 행이 사라졌으면(누가 지움) 결과를 새 행으로 남긴다
            _append([_now(), '', '', '{}', f'{est:.3f}', status, '', _one_line(f'{tag} 미확정 행 없음. {note}')])


def annotate(token, extra):
    """미확정 행의 상태·금액은 그대로 두고 메모만 덧붙인다(예: background 요청의 interaction id)."""
    def change(old):
        old[7] = _one_line(f'{old[7]} | {extra}')
    with _locked():
        return _rewrite(token, change)


def pending_rows(out=None, statuses=('pending',)):
    """상태가 statuses인 행(기본: 진행 중). out을 주면 그 출력 파일의 행만. 각 행에 'token'을 붙여 준다."""
    rows = [r for r in ledger_rows() if r['status'] in statuses]
    if out is not None:
        rows = [r for r in rows if same_output(r['output'], out)]
    for r in rows:
        m = re.search(r'\[call:([0-9a-f]+)\]', r['note'])
        r['token'] = m.group(1) if m else None
    return rows


def unsettled_rows(out=None):
    """미확정(pending·unresolved) 행. 청구됐을 수 있어 예상액으로 상한에 들어가 있는 행들."""
    return pending_rows(out, UNSETTLED)


def row_settings(row):
    try:
        v = json.loads(row.get('settings') or '{}')
        return v if isinstance(v, dict) else {}
    except ValueError:
        return {}


# ---------------------------------------------------------------- 예산

def load_budget(path=None):
    """예산 파일을 읽는다. 지정이 없으면 COST_BUDGET_PATH, 그다음 기본 경로(있을 때만)."""
    path = path or os.environ.get('COST_BUDGET_PATH') or (DEFAULT_BUDGET if os.path.exists(DEFAULT_BUDGET) else None)
    if not path or path.lower() == 'none':
        return None
    with open(path, encoding='utf-8') as f:
        b = json.load(f)
    for k in ('ledger_cap_usd', 'warn_at_usd'):
        if not isinstance(b.get(k), (int, float)):
            sys.exit(f'예산 파일 {path}에 숫자 {k}가 없습니다: 실행하지 않음')
    b['_path'] = path
    return b


def limit_check(total, est, cap=None, budget_file=None, allow_over_warn=False):
    """상한·80% 보고선 판정(출력 없음). (종료 코드 또는 0, 이유, 요약, 보고선을 넘지만 허락됨 여부)"""
    budget = load_budget(budget_file)
    if cap is None and budget is None:
        cap = float(os.environ.get('COST_CAP_USD', 30))
    after = total + est
    summary = f'장부 누적 ${total:.2f}(미확정 포함) + 이번 예상 ${est:.2f} = ${after:.2f}'
    if cap is not None:
        summary += f' / --cap ${cap:.2f}'
    if budget:
        summary += f' / 예산 상한 ${budget["ledger_cap_usd"]:.2f}, 80% 보고선 ${budget["warn_at_usd"]:.2f}'
    if cap is not None and after > cap:
        return EXIT_CAP, f'상한(--cap) 초과: 실행하지 않음 ({summary})', summary, False
    if budget and after > budget['ledger_cap_usd']:
        return EXIT_CAP, f'예산 상한 초과({budget["_path"]}): 실행하지 않음 ({summary})', summary, False
    if budget and after > budget['warn_at_usd']:
        if not allow_over_warn:
            return (EXIT_WARN, '80% 보고선을 넘습니다: 멈추고 사용자에게 보고하세요. 사용자가 허락한 뒤에만 '
                    f'--allow-over-warn을 붙여 다시 실행합니다. (실행하지 않음, {summary})', summary, False)
        return 0, '', summary, True
    return 0, '', summary, False


def guard(est, cap=None, budget_file=None, allow_over_warn=False):
    """유료 요청 전 확인. 넘으면 프로그램을 끝낸다(10 상한, 11 80% 보고선)."""
    total = spent()
    code, msg, summary, over_warn = limit_check(total, est, cap, budget_file, allow_over_warn)
    print(summary, flush=True)
    if code:
        print(msg, file=sys.stderr)
        sys.exit(code)
    if over_warn:
        print('주의: 80% 보고선을 넘는 요청입니다(--allow-over-warn 지정됨).', flush=True)
    return total


def check_cap(est, cap):
    # 예전 호출 방식 호환(예산 파일이 있으면 그것도 함께 확인)
    return guard(est, cap)


def free_path(path, overwrite=False):
    """이미 있는 파일을 덮어쓰지 않도록 _2, _3… 을 붙인 경로를 돌려준다."""
    if overwrite or not os.path.exists(path):
        return path
    stem, ext = os.path.splitext(path)
    n = 2
    while os.path.exists(f'{stem}_{n}{ext}'):
        n += 1
    return f'{stem}_{n}{ext}'


def refuse_existing(out, overwrite):
    if os.path.exists(out) and not overwrite:
        print(f'출력 파일이 이미 있습니다: {out} (덮어쓰려면 --overwrite). 유료 요청을 보내지 않음', file=sys.stderr)
        sys.exit(EXIT_EXISTS)


def unsettled_hint(rows):
    toks = ', '.join(f'{r["token"]}({r["status"]} ${float(r["est_usd"]):.2f}, {r["time_utc"]})' for r in rows)
    return (f'장부에 이 출력의 미확정 행이 있습니다: {toks}. 청구됐을 수 있어 예상액으로 상한에 들어가 있습니다.\n'
            f'  - 결제 화면에서 청구가 없었음을 확인했다면(사람이 확인한 뒤에만):\n'
            f'    python3 work/scripts/gen_api.py mark-not-billed <표식> --reason "확인 내용"\n'
            f'  - 새로 만들려면 다른 --out 이름을 쓰거나, 확인 뒤 --new-attempt-after-billing-check를 붙입니다.')


def refuse_unsettled(out, allow_new_attempt=False):
    """같은 출력에 미확정(pending·unresolved) 장부 행이 있으면 새 유료 요청을 막는다(12)."""
    rows = unsettled_rows(out)
    if not rows:
        return []
    if allow_new_attempt:
        print('주의: 이 출력의 미확정 장부 행이 있지만 --new-attempt-after-billing-check로 새 요청을 보냅니다. '
              '앞 행은 예상액 그대로 상한에 남습니다.', flush=True)
        return rows
    print(unsettled_hint(rows) + '\n유료 요청을 보내지 않음', file=sys.stderr)
    sys.exit(EXIT_EXISTS)


def lock_path():
    return os.path.join(os.path.dirname(os.path.abspath(ledger_path())), '.paid_run.lock')


@contextlib.contextmanager
def paid_run_lock(what=''):
    """유료 실행(생성·되찾기·'청구 없음' 표시)은 한 번에 하나만. 상한 확인부터 장부 정리까지 잠금을 잡는다.
    이미 다른 실행이 잡고 있으면 기다리지 않고 끝낸다(13)."""
    import fcntl
    p = lock_path()
    os.makedirs(os.path.dirname(p), exist_ok=True)
    fd = os.open(p, os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            try:
                who = os.pread(fd, 300, 0).decode('utf-8', 'replace').strip()
            except OSError:
                who = ''
            print(f'다른 유료 실행이 진행 중입니다({who or p}). 겹쳐 돌리면 상한 확인과 서버 결과 되찾기가 '
                  f'틀어질 수 있어 실행하지 않습니다. 앞 실행이 끝난 뒤 다시 실행하세요.', file=sys.stderr)
            sys.exit(EXIT_BUSY)
        os.ftruncate(fd, 0)
        os.pwrite(fd, f'pid {os.getpid()} {what} {_now()}Z'.encode('utf-8'), 0)
        yield
    finally:
        os.close(fd)  # 닫으면 잠금도 풀린다


# ---------------------------------------------------------------- 클라이언트

def make_client(key=None, **http_kw):
    """이미지·Veo·파일용(구형 경로) 클라이언트. 자동 재시도가 없는(1회 시도) 설정인지 확인한다."""
    from google import genai
    from google.genai import types
    no_debug_env()
    http_kw.pop('retry_options', None)  # 재시도 설정은 받지 않음(None = 1회 시도)
    c = genai.Client(api_key=key or api_key(), http_options=types.HttpOptions(**http_kw) if http_kw else None)
    stop = getattr(getattr(getattr(c, '_api_client', None), '_retry', None), 'stop', None)
    if getattr(stop, 'max_attempt_number', None) != 1:
        raise RuntimeError('SDK 자동 재시도가 꺼져 있는지 확인하지 못함: 유료 요청을 보내지 않음')
    return c


_CLIENT = None


def client():
    # 클라이언트 객체가 먼저 해제되면 연결이 닫히므로 모듈 수준에 보관
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = make_client()
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


def _fail_unknown(token, est, kind_ko, e):
    """요청 중 오류: 즉시 거절이면 0, 아니면 청구 여부를 모르는 것으로(unresolved, 예상액 그대로) 남긴다."""
    code = status_code_of(e)
    msg = scrub(f'{type(e).__name__}: {e}')[:300]
    if code in REJECT_CODES:
        finalize(token, 0, 'error', f'즉시 거절({code}) {msg}')
        print(f'{kind_ko} 요청이 즉시 거절됨({code}): {msg}', file=sys.stderr)
        sys.exit(EXIT_REJECTED)
    finalize(token, est, 'unresolved', f'{msg} | 결과 없음. 청구됐는지 모름 → 예상 ${est:.3f}을 상한에 그대로 둠. '
                                       f'결제 화면 확인 뒤에만 mark-not-billed {token}')
    print(f'경고: {kind_ko} 요청 중 오류({msg}).\n'
          f'  서버에서는 생성·청구됐을 수 있습니다(추정 ${est:.2f}). 자동으로 다시 보내지 않았습니다.\n'
          f'  장부에는 unresolved(예상액 그대로, 상한·80% 계산에 들어감)로 남겼습니다. 표식: {token}\n'
          f'  Google 결제 화면에서 청구가 없었음을 확인한 뒤에만 0달러로 바꿉니다:\n'
          f'    python3 work/scripts/gen_api.py mark-not-billed {token} --reason "확인 내용"', file=sys.stderr)
    sys.exit(EXIT_UNKNOWN)


def mark_not_billed(token, reason):
    """사람이 Google 결제 화면에서 청구가 없음을 확인한 뒤에만: 미확정 행을 0달러(not_billed)로 바꾼다.

    pending 행(죽은 프로세스가 남긴 것)도 바꿀 수 있지만, 유료 실행 잠금을 잡은 상태에서만 한다
    (지금 돌고 있는 요청의 행을 잘못 지우지 않게). 같은 표식의 되찾기 기록 json은 <이름>.not_billed.json으로 옮겨 둔다.
    """
    if not token or not re.fullmatch(r'[0-9a-f]{6,32}', token):
        print(f'표식 형식이 아닙니다: {token!r} (장부 메모의 [call:…] 안 값)', file=sys.stderr)
        sys.exit(2)
    if not reason or len(reason.strip()) < 4:
        print('--reason에 결제 화면에서 확인한 내용을 적어야 합니다(예: "10/18 결제 화면에 그 시각 청구 없음")',
              file=sys.stderr)
        sys.exit(2)
    with paid_run_lock(f'mark-not-billed {token}'):
        rows = [r for r in unsettled_rows() if r['token'] == token]
        if not rows:
            print(f'표식 {token}의 미확정(pending·unresolved) 행이 장부에 없습니다. 바꾼 것 없음', file=sys.stderr)
            sys.exit(2)
        r = rows[-1]
        prev = re.sub(r'\[call:[0-9a-f]+\]\s*', '', r['note'])
        finalize(token, 0, 'not_billed', f'사람이 결제 화면 확인 후 청구 없음으로 표시(이전 {r["status"]} '
                                         f'예상 ${float(r["est_usd"]):.3f}). 확인 내용: {reason}. 이전 메모: {prev}')
        moved, side = None, None
        if r['output']:
            out_abs = r['output'] if os.path.isabs(r['output']) else os.path.normpath(os.path.join(REPO, r['output']))
            side = os.path.splitext(out_abs)[0] + '.json'
        if side and os.path.exists(side):
            try:
                with open(side, encoding='utf-8') as f:
                    meta = json.load(f)
            except (OSError, ValueError):
                meta = {}
            if meta.get('call_token') == token and meta.get('downloaded') is False:
                moved = free_path(os.path.splitext(side)[0] + '.not_billed.json')
                os.replace(side, moved)
        print(f'바꿈: 표식 {token} {r["status"]} ${float(r["est_usd"]):.3f} → not_billed $0.000 ({r["output"]})'
              + (f'\n  되찾기 기록을 옮김: {moved}' if moved else ''))
        return 0


# ---------------------------------------------------------------- 명령

def cmd_image(args):
    from google.genai import types
    from PIL import Image
    if args.model not in IMAGE_PRICE or args.size not in IMAGE_PRICE[args.model]:
        sys.exit(f'단가표에 없는 조합: {args.model} {args.size} (실행하지 않음)')
    est = IMAGE_PRICE[args.model][args.size]
    refuse_existing(args.out, args.overwrite)
    refuse_unsettled(args.out, args.new_attempt_after_billing_check)
    guard(est, args.cap, args.budget_file, args.allow_over_warn)
    prompt = read_prompt(args)
    parts = [prompt] + [Image.open(p) for p in args.images]
    settings = {'inputs': args.images, 'size': args.size, 'aspect': '16:9'}
    c = client()
    once('image')
    token = log_pending('image', args.model, settings, est, args.out,
                        limits=dict(cap=args.cap, budget_file=args.budget_file, allow_over_warn=args.allow_over_warn))
    t0 = time.time()
    try:
        resp = c.models.generate_content(
            model=args.model, contents=parts,
            config=types.GenerateContentConfig(
                response_modalities=['IMAGE'],
                image_config=types.ImageConfig(aspect_ratio='16:9', image_size=args.size)))
    except Exception as e:
        # 이미지는 서버 파일 목록에서 되찾을 수 없음
        _fail_unknown(token, est, '이미지', e)
    data, mime = None, None
    for part in resp.candidates[0].content.parts if resp.candidates else []:
        # Pro 이미지 모델은 생각 단계의 중간 이미지(thought=True)를 함께 보낼 수 있으므로 최종 이미지만 쓴다
        if part.inline_data is not None and not getattr(part, 'thought', False):
            data, mime = part.inline_data.data, part.inline_data.mime_type
    um = getattr(resp, 'usage_metadata', None)
    usage = {k: getattr(um, k, None) for k in ('prompt_token_count', 'candidates_token_count',
                                              'thoughts_token_count', 'total_token_count')} if um else {}
    if data is None:
        finalize(token, 0, 'no_image', _one_line(str(resp))[:300])
        print('이미지가 반환되지 않음', file=sys.stderr)
        sys.exit(EXIT_FAILED)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    # API는 확장자와 상관없이 JPEG를 돌려줄 수 있음(2K 결과물이 .png 이름의 JPEG였음).
    # 받은 그대로를 맞는 확장자로 보관하고, 요청한 이름이 다른 형식이면 무손실 PNG로 풀어서 저장한다.
    ext = {'image/jpeg': '.jpg', 'image/png': '.png', 'image/webp': '.webp'}.get(
        mime or '', mimetypes.guess_extension(mime or '') or '.bin')
    orig = os.path.splitext(args.out)[0] + ext
    if os.path.abspath(orig) != os.path.abspath(args.out):
        orig = free_path(orig, args.overwrite)
    with open(orig, 'wb') as f:
        f.write(data)
    if os.path.abspath(orig) != os.path.abspath(args.out):
        Image.open(io.BytesIO(data)).save(args.out)
    with Image.open(args.out) as im:
        w, h = im.size
    finalize(token, est, 'ok', f'{mime} {w}x{h} 원본 {os.path.relpath(orig)} 토큰 {json.dumps(usage)} '
                               f'{time.time() - t0:.0f}초')
    print(f'저장: {args.out} ({w}x{h}, 받은 형식 {mime}, 원본 {orig}) 토큰 {usage}')


def cmd_video(args):
    from google.genai import types
    # 연장은 7초가 새로 생성됨(출력 영상은 입력 영상 + 연장분)
    gen_sec = 7 if args.extend else args.duration
    est = VIDEO_PRICE[args.model][args.resolution] * gen_sec
    refuse_existing(args.out, args.overwrite)
    refuse_unsettled(args.out, args.new_attempt_after_billing_check)
    guard(est, args.cap, args.budget_file, args.allow_over_warn)
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
    once('veo')
    token = log_pending('video', args.model, settings, est, args.out,
                        limits=dict(cap=args.cap, budget_file=args.budget_file, allow_over_warn=args.allow_over_warn))
    try:
        op = c.models.generate_videos(model=args.model, source=src,
                                      config=types.GenerateVideosConfig(**cfg))
    except Exception as e:
        _fail_unknown(token, est, 'Veo', e)
    # 상태 확인은 무료이므로 오류가 나도 몇 번 더 묻는다(생성 요청은 다시 보내지 않음)
    t0, errs = time.time(), 0
    while not op.done:
        time.sleep(10)
        try:
            op = c.operations.get(op)
            errs = 0
        except Exception as e:
            errs += 1
            if errs >= 6:
                finalize(token, est, 'unresolved', f'상태 확인 실패, 작업 {getattr(op, "name", "?")} 청구됐을 수 있음: '
                                                   f'{scrub(e)[:200]}')
                print('경고: 생성은 시작됐지만 상태 확인에 계속 실패했습니다. 청구됐을 수 있어 장부에 예상액으로 남겼습니다.',
                      file=sys.stderr)
                sys.exit(EXIT_FETCH)
        print(f'  생성 중… {time.time() - t0:.0f}s', flush=True)
    resp = op.response
    vids = getattr(resp, 'generated_videos', None) if resp else None
    if op.error or not vids:
        note = json.dumps(op.error) if op.error else str(resp)[:300]
        finalize(token, 0, 'failed', note[:300])
        print(f'생성 실패: {scrub(note)}', file=sys.stderr)
        sys.exit(EXIT_FAILED)
    v = vids[0].video
    c.files.download(file=v)
    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    v.save(args.out)
    with open(os.path.splitext(args.out)[0] + '.json', 'w', encoding='utf-8') as f:
        json.dump({'model': args.model, 'prompt': prompt, 'video_uri': v.uri, **settings}, f,
                  ensure_ascii=False, indent=1)
    finalize(token, est, 'ok', '')
    print('저장:', args.out)


def add_safety_args(p, top):
    # 맨 앞(top)과 하위 명령 양쪽에서 받되, 하위 명령 쪽 기본값이 앞의 값을 덮지 않게 SUPPRESS
    d = (lambda v: v) if top else (lambda v: argparse.SUPPRESS)
    p.add_argument('--cap', type=float, default=d(float(os.environ['COST_CAP_USD'])
                                                  if os.environ.get('COST_CAP_USD') else None),
                   help='장부 누적 상한(달러). 예산 파일과 함께 쓰면 둘 다 확인')
    p.add_argument('--budget-file', default=d(None),
                   help='예산 파일(기본 COST_BUDGET_PATH 또는 work/final/budget.json, none=쓰지 않음)')
    p.add_argument('--allow-over-warn', action='store_true', default=d(False),
                   help='80%% 보고선을 넘는 요청 허용(사용자 허락 뒤에만)')  # argparse 도움말은 %를 %%로 써야 함


def main(argv=None):
    ap = argparse.ArgumentParser()
    add_safety_args(ap, True)
    sub = ap.add_subparsers(dest='cmd', required=True)

    p = sub.add_parser('image')
    add_safety_args(p, False)
    p.add_argument('images', nargs='+')
    p.add_argument('--out', required=True)
    p.add_argument('--prompt')
    p.add_argument('--prompt-file')
    p.add_argument('--model', default='gemini-3.1-flash-image')
    p.add_argument('--size', default='2K', choices=['1K', '2K', '4K'])
    p.add_argument('--overwrite', action='store_true', help='출력 파일이 있으면 덮어씀')
    p.add_argument('--new-attempt-after-billing-check', action='store_true',
                   help='이 출력에 미확정(청구 여부 모름) 장부 행이 있어도 새 요청을 보냄(결제 화면 확인 뒤에만)')
    p.set_defaults(fn=lambda a: _locked_run('image', cmd_image, a))

    p = sub.add_parser('video')
    add_safety_args(p, False)
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
    p.add_argument('--overwrite', action='store_true', help='출력 파일이 있으면 덮어씀')
    p.add_argument('--new-attempt-after-billing-check', action='store_true',
                   help='이 출력에 미확정(청구 여부 모름) 장부 행이 있어도 새 요청을 보냄(결제 화면 확인 뒤에만)')
    p.set_defaults(fn=lambda a: _locked_run('veo', cmd_video, a))

    p = sub.add_parser('mark-not-billed',
                       help='(사람이 결제 화면을 확인한 뒤에만) 청구 여부를 몰라 예상액으로 잡아 둔 행을 0달러로')
    p.add_argument('token', help='장부 메모의 [call:…] 안 표식')
    p.add_argument('--reason', required=True, help='결제 화면에서 확인한 내용')
    p.set_defaults(fn=lambda a: mark_not_billed(a.token, a.reason))

    args = ap.parse_args(argv)
    no_debug_env()
    return args.fn(args)


def _locked_run(what, fn, args):
    with paid_run_lock(f'{what} {args.out}'):
        return fn(args)


if __name__ == '__main__':
    sys.exit(main() or 0)
