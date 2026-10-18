"""유료 생성 스크립트(omni_gen.py, gen_api.py) 안전 시험. 네트워크·API 호출 없음.

- google.genai.Client를 가짜 객체로 바꿔 끼워 성공·끊김·되찾기·거절·예산 상황을 흉내 낸다.
- 실제 SDK(google-genai) 시험은 가짜 키 + httpx.MockTransport로만 하고, 요청이 몇 번 나가는지 센다.
- 장부는 임시 복사본(COST_LEDGER_PATH), 예산 파일도 임시 파일(COST_BUDGET_PATH)만 쓴다.
  유료 실행 잠금 파일(.paid_run.lock)도 장부와 같은 임시 폴더에 생긴다.
  실제 work/cost_ledger.csv와 work/final/budget.json은 시작·끝 해시가 같아야 한다.
- 이 프로세스 안에서는 GEMINI_API_KEY를 가짜 값으로 덮어써서 진짜 키를 읽지도 쓰지도 않는다.

실행(저장소 루트): python3 work/scripts/tests/test_paid_safety.py   (pytest가 있으면 python3 -m pytest 도 됨)
"""
import contextlib
import csv
import datetime as dt
import hashlib
import io
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from types import SimpleNamespace

HERE = os.path.dirname(os.path.abspath(__file__))
SCRIPTS = os.path.dirname(HERE)
WORK = os.path.dirname(SCRIPTS)
REAL_LEDGER = os.path.join(WORK, 'cost_ledger.csv')
REAL_BUDGET = os.path.join(WORK, 'final', 'budget.json')
FAKE_KEY = 'FAKE-TEST-KEY-not-a-real-key-0123456789'

# 진짜 키를 쓰지 않도록 이 프로세스의 환경만 바꾼다(값은 읽지도 출력하지도 않음)
os.environ['GEMINI_API_KEY'] = FAKE_KEY
for _k in ('GOOGLE_API_KEY', 'COST_CAP_USD', 'GOOGLE_GENAI_DEBUG', 'COST_LEDGER_PATH', 'COST_BUDGET_PATH'):
    os.environ.pop(_k, None)
sys.path.insert(0, SCRIPTS)

import google.genai as genai_mod  # noqa: E402
import gen_api as G  # noqa: E402
import omni_gen as O  # noqa: E402

REAL_CLIENT = genai_mod.Client


def sha(path):
    if not os.path.exists(path):
        return None
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()


_HASHES = {}


def setUpModule():
    _HASHES['ledger'] = sha(REAL_LEDGER)
    _HASHES['budget'] = sha(REAL_BUDGET)


def tearDownModule():
    assert sha(REAL_LEDGER) == _HASHES['ledger'], '실제 장부가 바뀌었음!'
    assert sha(REAL_BUDGET) == _HASHES['budget'], '실제 예산 파일이 바뀌었음!'


# ---------------------------------------------------------------- 가짜 SDK

def now():
    return dt.datetime.now(dt.timezone.utc)


def load_json(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)


class FakeDisconnect(Exception):
    """httpx.RemoteProtocolError('Server disconnected…')를 흉내."""


class FakeStatusError(Exception):
    def __init__(self, code, msg):
        super().__init__(f'Error code: {code} - {msg}')
        self.status_code = code


def gen_file(name, created, source='GENERATED', mime='video/mp4', state='ACTIVE'):
    return SimpleNamespace(name=name, create_time=created, source=source, mime_type=mime,
                           state=SimpleNamespace(name=state, value=state),
                           uri=f'https://generativelanguage.googleapis.com/v1beta/{name}',
                           download_uri=f'https://generativelanguage.googleapis.com/v1beta/{name}:download?alt=media')


class FakeServer:
    def __init__(self):
        self.files, self.scheduled = [], []   # scheduled: (list 호출 몇 번째부터 보이는지, 파일)
        self.create_calls, self.create_retry_cfgs, self.gen_calls = [], [], []
        self.list_calls = self.get_calls = 0
        self.downloads, self.uploads, self.uploaded = [], [], {}
        self.download_fail = 0
        self.create_behavior = None
        self.image_behavior = None
        self.interaction = None
        self.clients = []
        self.during_create = None
        self.get_sequence = []   # interactions.get가 차례로 돌려줄 값(비면 interaction). 예외 객체면 그것을 던짐
        self.during_get = None


SERVER = FakeServer()


class FakeFiles:
    def list(self, config=None):
        SERVER.list_calls += 1
        for item in list(SERVER.scheduled):
            if SERVER.list_calls >= item[0]:
                SERVER.files.append(item[1])
                SERVER.scheduled.remove(item)
        return list(SERVER.files)

    def download(self, file=None, config=None):
        name = O.file_name(file)
        SERVER.downloads.append(name)
        if SERVER.download_fail > 0:
            SERVER.download_fail -= 1
            raise RuntimeError('download failed (mock)')
        return b'FAKEVIDEO:' + name.encode()

    def upload(self, file=None, config=None):
        f = gen_file(f'files/up{len(SERVER.uploads)}', now(), source='UPLOADED', mime='image/png')
        SERVER.uploads.append(file)
        SERVER.uploaded[f.name] = f
        return f

    def get(self, name=None, config=None):
        return SERVER.uploaded[name]


class FakeInteractions:
    def __init__(self):
        self.sdk_configuration = SimpleNamespace(retry_config='DEFAULT-RETRY')

    def create(self, **kw):
        SERVER.create_calls.append(kw)
        SERVER.create_retry_cfgs.append(self.sdk_configuration.retry_config)
        if SERVER.during_create:
            SERVER.during_create()
        return SERVER.create_behavior(kw)

    def get(self, iid, **kw):
        SERVER.get_calls += 1
        if SERVER.during_get:
            SERVER.during_get()
        if SERVER.get_sequence:
            v = SERVER.get_sequence.pop(0)
            if isinstance(v, Exception):
                raise v
            return v
        return SERVER.interaction


class FakeModels:
    def generate_content(self, model=None, contents=None, config=None):
        SERVER.gen_calls.append({'model': model, 'config': config})
        if SERVER.during_create:
            SERVER.during_create()
        return SERVER.image_behavior()


class FakeClient:
    def __init__(self, api_key=None, http_options=None, **kw):
        self.api_key_is_fake = api_key == FAKE_KEY
        self.http_options = http_options
        self.files, self.interactions, self.models = FakeFiles(), FakeInteractions(), FakeModels()
        # 구형 경로 재시도 확인용(SDK 2.30.1 구조와 같게: 재시도 없음 = 1회 시도)
        self._api_client = SimpleNamespace(_retry=SimpleNamespace(stop=SimpleNamespace(max_attempt_number=1)))
        SERVER.clients.append(self)


USAGE = {'input_tokens_by_modality': [{'modality': 'image', 'tokens': 1100}, {'modality': 'text', 'tokens': 300}],
         'output_tokens_by_modality': [{'modality': 'video', 'tokens': 15448}],
         'total_input_tokens': 1400, 'total_output_tokens': 15600, 'total_thought_tokens': 300}


def ok_interaction(name='files/gen1', iid='v1_fake_interaction'):
    return SimpleNamespace(id=iid, status='completed', usage=dict(USAGE),
                           output_video=SimpleNamespace(
                               uri=f'https://generativelanguage.googleapis.com/v1beta/{name}:download?alt=media',
                               mime_type='video/mp4'))


USAGE_4K = {'output_tokens_by_modality': [{'modality': 'video', 'tokens': 139008}], 'total_output_tokens': 139860,
            'total_thought_tokens': 374, 'total_input_tokens': 1414}


def waiting_interaction(status='in_progress', iid='v1_fake_interaction'):
    return SimpleNamespace(id=iid, status=status, usage=None, output_video=None)


def disconnect(kw):
    raise FakeDisconnect('Server disconnected without sending a response.')


# ---------------------------------------------------------------- 공통 준비

class Base(unittest.TestCase):
    def setUp(self):
        global SERVER
        SERVER = FakeServer()
        self.tmp = tempfile.mkdtemp(prefix='paid_safety_')
        self.ledger = os.path.join(self.tmp, 'cost_ledger.csv')
        shutil.copy(REAL_LEDGER, self.ledger)
        self.budget = os.path.join(self.tmp, 'budget.json')
        os.environ['COST_LEDGER_PATH'] = self.ledger
        os.environ['COST_BUDGET_PATH'] = self.budget
        os.environ['GEMINI_API_KEY'] = FAKE_KEY
        self.base = G.spent()
        self.set_budget(self.base + 10, self.base + 8)
        self.out_dir = os.path.join(self.tmp, 'out')
        os.makedirs(self.out_dir)
        self.prompt = os.path.join(self.tmp, 'p.txt')
        with open(self.prompt, 'w', encoding='utf-8') as f:
            f.write('Continuous single shot. test prompt')
        self.first = os.path.join(self.tmp, 'first.png')
        from PIL import Image
        Image.new('RGB', (64, 36), (40, 80, 120)).save(self.first)
        G._PAID_ATTEMPTS.clear()
        G._CLIENT = None
        genai_mod.Client = FakeClient

    def tearDown(self):
        genai_mod.Client = REAL_CLIENT
        G._PAID_ATTEMPTS.clear()
        G._CLIENT = None
        for k in ('COST_LEDGER_PATH', 'COST_BUDGET_PATH'):
            os.environ.pop(k, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def set_budget(self, cap, warn):
        with open(self.budget, 'w', encoding='utf-8') as f:
            json.dump({'ledger_cap_usd': round(cap, 3), 'warn_at_usd': round(warn, 3), 'note': '시험'}, f)

    def rows(self):
        with open(self.ledger, newline='', encoding='utf-8') as f:
            return list(csv.DictReader(f))

    def ledger_text(self):
        with open(self.ledger, encoding='utf-8') as f:
            return f.read()

    def run_main(self, fn, *args):
        out, err = io.StringIO(), io.StringIO()
        G._PAID_ATTEMPTS.clear()  # 한 번 실행 = 새 프로세스와 같게
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            try:
                code = fn(list(args)) or 0
            except SystemExit as e:
                code = e.code if isinstance(e.code, int) else 1
        return code, out.getvalue(), err.getvalue()

    def omni(self, *args, out='A.mp4', res='360p'):
        self.out = os.path.join(self.out_dir, out)
        base = ['--out', self.out, '--prompt-file', self.prompt, '--resolution', res, '--duration', '8']
        return self.run_main(O.main, *(base + list(args)))

    def row_of(self, token):
        return [r for r in self.rows() if f'[call:{token}]' in r['note']]

    def token_of(self, out):
        meta = load_json(os.path.splitext(out)[0] + '.json')
        return meta['call_token']

    def assert_no_key(self, *texts):
        for t in texts + (self.ledger_text(),):
            self.assertNotIn(FAKE_KEY, t)


# ---------------------------------------------------------------- Omni 시험

class OmniPaidSafety(Base):
    def test_success_uses_usage_tokens_and_single_attempt(self):
        SERVER.create_behavior = lambda kw: ok_interaction('files/gen1')
        SERVER.interaction = ok_interaction('files/gen1')
        before = self.rows()
        est = O.estimate_usd('360p', 8, False)
        seen = {}

        def during():
            r = G.ledger_rows()[-1]
            seen['status'], seen['spent'] = r['status'], G.spent()
        SERVER.during_create = during
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        # 요청 중에는 pending 행이 상한 계산에 들어가 있었다
        self.assertEqual(seen['status'], 'pending')
        self.assertAlmostEqual(seen['spent'], self.base + est, places=3)
        # 생성 요청은 재시도를 끈 클라이언트로, 확인·내려받기는 기본 클라이언트로
        cfg = SERVER.create_retry_cfgs[0]
        self.assertEqual(getattr(cfg, 'strategy', None), 'none')
        self.assertIs(cfg.retry_connection_errors, False)
        self.assertEqual(len(SERVER.clients), 2)
        self.assertTrue(all(c.api_key_is_fake for c in SERVER.clients))
        self.assertEqual(SERVER.clients[0].interactions.sdk_configuration.retry_config, 'DEFAULT-RETRY')
        self.assertEqual(SERVER.create_calls[0]['response_format']['resolution'], '360p')
        self.assertTrue(SERVER.create_calls[0]['input'][-1]['text'].startswith('<FIRST_FRAME>'))
        # 장부: 행 1개 추가, 실제 토큰 기준 비용
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual(rows[:-1], before)
        r = rows[-1]
        actual = 15448 * 17.5e-6 + (152 + 300) * 17.5e-6 + 1400 * 2e-6
        self.assertEqual(r['status'], 'ok')
        self.assertEqual(r['est_usd'], f'{actual:.3f}')
        self.assertIn('응답 토큰 기준', r['note'])
        self.assertIn(f'{est:.3f}', r['note'])
        self.assertEqual(G.pending_rows(), [])
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual(meta['interaction_id'], 'v1_fake_interaction')
        self.assertTrue(meta['extendable'])
        self.assertEqual(meta['output_file'], 'files/gen1')
        self.assertAlmostEqual(meta['cost']['actual_usd'], actual, delta=1e-4)
        self.assertEqual(meta['cost']['estimate_usd'], est)
        with open(self.out, 'rb') as f:
            self.assertEqual(f.read(), b'FAKEVIDEO:files/gen1')
        self.assert_no_key(out, err)

    def test_disconnect_then_recovered_server_file(self):
        t = now()
        SERVER.files = [gen_file('files/old1', t - dt.timedelta(hours=2)),        # 오래된 생성물
                        gen_file('files/snap1', t - dt.timedelta(seconds=5)),     # 요청 전부터 있던 것(시계 여유 안)
                        gen_file('files/upX', t, source='UPLOADED')]              # 업로드 파일
        SERVER.scheduled = [(2, gen_file('files/ref1', t + dt.timedelta(seconds=1))),   # 이미 다른 json이 쓰는 것
                            (3, gen_file('files/gen2', t + dt.timedelta(seconds=2)))]   # 이번 요청의 결과
        with open(os.path.join(self.out_dir, 'older_result.json'), 'w', encoding='utf-8') as f:
            json.dump({'recovered_file': 'files/ref1'}, f)

        def boom(kw):
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.create_behavior = boom
        before = self.rows()
        est = O.estimate_usd('360p', 8, False)
        code, out, err = self.omni('--first', self.first, '--recover-wait', '5', '--recover-interval', '0.01')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(SERVER.downloads, ['files/gen2'])
        self.assertEqual(SERVER.list_calls, 3)  # 요청 전 1번 + 오류 뒤 2번
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        r = rows[-1]
        self.assertEqual((r['status'], r['est_usd']), ('ok', f'{est:.3f}'))
        self.assertIn('files/gen2', r['note'])
        self.assertIn('되찾음', r['note'])
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertIsNone(meta['interaction_id'])
        self.assertEqual(meta['recovered_file'], 'files/gen2')
        self.assertIs(meta['extendable'], False)
        self.assertIn('다시 보내지 않습니다', out)
        # 되찾은 결과로 연장하려 하면 유료 요청 없이 거절
        code, out2, err2 = self.omni('--extend-from', os.path.join(self.out_dir, 'A.json'), out='B.mp4')
        self.assertEqual(code, 2)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertIn('연장 재료로 쓸 수 없습니다', err2)

    def test_disconnect_no_file_stays_unresolved_and_counts(self):
        # 결과를 못 찾아도 0달러로 바꾸지 않는다: unresolved(예상액)로 상한·80% 계산에 남는다
        SERVER.create_behavior = disconnect
        before = self.rows()
        est = O.estimate_usd('360p', 8, False)
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.15', '--recover-interval', '0.03')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertGreaterEqual(SERVER.list_calls, 3)
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual((rows[-1]['status'], rows[-1]['est_usd']), ('unresolved', f'{est:.3f}'))
        self.assertIn('청구됐는지 모름', rows[-1]['note'])
        self.assertIn('청구됐을 수 있습니다', err)
        # 되찾기 안내에 해상도·길이가 들어 있어야 한다(기본값으로 잘못 적지 않게)
        self.assertIn('--recover-only --resolution 360p --duration 8', err)
        self.assertIn('--mark-not-billed', err)
        self.assertFalse(os.path.exists(self.out))
        self.assertAlmostEqual(G.spent(), self.base + est, places=3)
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual((meta['downloaded'], meta['ledger'], meta['resolution']), (False, 'unresolved', '360p'))
        self.assertEqual(len(self.row_of(meta['call_token'])), 1)

    def test_unresolved_counts_toward_cap_for_next_request(self):
        # 리뷰 E1: 결과를 못 찾은 4K 요청 뒤, 4K 하나 값만 남은 예산에서는 다음 4K를 보내지 않는다
        self.set_budget(self.base + 3.0, self.base + 2.9)
        SERVER.create_behavior = disconnect
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01',
                                   res='4k')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertAlmostEqual(G.spent() - self.base, O.estimate_usd('4k', 8), places=3)
        SERVER.create_behavior = lambda kw: ok_interaction('files/gen2')
        SERVER.interaction = ok_interaction('files/gen2')
        code2, out2, err2 = self.omni('--first', self.first, out='B.mp4', res='4k')
        self.assertEqual(code2, G.EXIT_CAP)
        self.assertEqual(len(SERVER.create_calls), 1)

    def test_late_file_recovered_by_printed_hint_keeps_4k_estimate(self):
        # 리뷰 E2: 안내된 명령 그대로 되찾으면, 원래 행(4K 예상액)을 ok로 바꾸고 새 행은 만들지 않는다
        SERVER.create_behavior = disconnect
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01',
                                   res='4k')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        token = self.token_of(self.out)
        n_rows = len(self.rows())
        hint = [ln.strip() for ln in err.splitlines() if '--recover-only' in ln and ln.strip().startswith('python3')][0]
        SERVER.files.append(gen_file('files/late4k', now()))
        argv = hint.split()[2:] + ['--recover-wait', '0.05', '--recover-interval', '0.01']
        code3, out3, err3 = self.run_main(O.main, *argv)
        self.assertEqual(code3, 0, err3)
        self.assertEqual(len(self.rows()), n_rows)
        r = self.row_of(token)[0]
        self.assertEqual((r['status'], r['est_usd']), ('ok', f'{O.estimate_usd("4k", 8):.3f}'))
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual((meta['resolution'], meta['recovered_file'], meta['ledger']), ('4k', 'files/late4k', 'ok'))
        self.assertEqual(len(SERVER.create_calls), 1)

    def test_recover_only_without_row_needs_explicit_settings(self):
        out = os.path.join(self.out_dir, 'N.mp4')
        SERVER.files = [gen_file('files/n1', now())]
        since = (now() - dt.timedelta(minutes=1)).replace(tzinfo=None).isoformat(timespec='seconds')
        n_rows = len(self.rows())
        code, o, e = self.run_main(O.main, '--out', out, '--recover-only', '--recover-since', since)
        self.assertEqual(code, 2)
        self.assertIn('--resolution', e)
        self.assertEqual(len(self.rows()), n_rows)
        code, o, e = self.run_main(O.main, '--out', out, '--recover-only', '--recover-since', since,
                                   '--resolution', '4k', '--duration', '8', '--recover-wait', '0.05')
        self.assertEqual(code, 0, e)
        r = self.rows()[-1]
        self.assertEqual((r['status'], r['est_usd']), ('ok', f'{O.estimate_usd("4k", 8):.3f}'))
        self.assertEqual(load_json(os.path.join(self.out_dir, 'N.json'))['resolution'], '4k')

    def test_rerun_after_download_failure_is_refused(self):
        # 리뷰 E3: 내려받기만 실패(이미 청구) 뒤 같은 명령을 다시 실행해도 두 번째 유료 요청을 보내지 않는다
        SERVER.create_behavior = lambda kw: ok_interaction('files/gen9')
        SERVER.interaction = ok_interaction('files/gen9')
        SERVER.download_fail = 3
        real_sleep = time.sleep
        time.sleep = lambda s: None
        try:
            code, out, err = self.omni('--first', self.first)
            self.assertEqual(code, G.EXIT_FETCH)
            SERVER.download_fail = 0
            code2, out2, err2 = self.omni('--first', self.first)
        finally:
            time.sleep = real_sleep
        self.assertEqual(code2, G.EXIT_EXISTS)
        self.assertIn('--recover-only', err2)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(load_json(os.path.join(self.out_dir, 'A.json'))['interaction_id'], 'v1_fake_interaction')
        # 사람이 확인하고 일부러 새로 만들 때만: 앞 기록은 옮겨 두고 보낸다
        second = ok_interaction('files/genB', iid='v1_second')
        SERVER.create_behavior = lambda kw: second
        SERVER.interaction = second
        code3, out3, err3 = self.omni('--first', self.first, '--new-attempt-after-billing-check')
        self.assertEqual(code3, 0, err3)
        self.assertEqual(len(SERVER.create_calls), 2)
        prev = [f for f in os.listdir(self.out_dir) if f.startswith('A.prev_') and f.endswith('.json')]
        self.assertEqual(len(prev), 1)
        self.assertEqual(load_json(os.path.join(self.out_dir, prev[0]))['interaction_id'], 'v1_fake_interaction')

    def test_unresolved_row_blocks_rerun_until_marked_not_billed(self):
        SERVER.create_behavior = disconnect
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        token = self.token_of(self.out)
        os.remove(os.path.join(self.out_dir, 'A.json'))       # json이 없어도 장부 행으로 막는다
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_EXISTS)
        self.assertIn('mark-not-billed', err)
        self.assertEqual(len(SERVER.create_calls), 1)
        # 이유 없이 0달러로 바꿀 수 없음
        code, o, e = self.run_main(O.main, '--mark-not-billed', token)
        self.assertEqual(code, 2)
        code, o, e = self.run_main(O.main, '--mark-not-billed', token, '--reason', '결제 화면에 그 시각 청구 없음(시험)')
        self.assertEqual(code, 0, e)
        r = self.row_of(token)[0]
        self.assertEqual((r['status'], r['est_usd']), ('not_billed', '0.000'))
        self.assertIn('결제 화면', r['note'])
        self.assertAlmostEqual(G.spent(), self.base, places=3)
        SERVER.create_behavior = lambda kw: ok_interaction('files/gen3')
        SERVER.interaction = ok_interaction('files/gen3')
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 2)

    def test_mark_not_billed_moves_unresolved_json(self):
        SERVER.create_behavior = disconnect
        self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01')
        token = self.token_of(self.out)
        code, o, e = self.run_main(G.main, 'mark-not-billed', token, '--reason', '결제 화면 확인(시험)')
        self.assertEqual(code, 0, e)
        self.assertFalse(os.path.exists(os.path.join(self.out_dir, 'A.json')))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, 'A.not_billed.json')))
        code, o, e = self.run_main(G.main, 'mark-not-billed', token, '--reason', '두 번째')
        self.assertEqual(code, 2)   # 이미 확정된 행은 다시 바꾸지 않음

    def test_in_progress_is_polled_until_completed(self):
        # 리뷰 E4: in_progress로 돌아오면 0달러 failed로 끝내지 않고 get으로 끝날 때까지 기다린다
        SERVER.create_behavior = lambda kw: waiting_interaction('in_progress')
        SERVER.get_sequence = [waiting_interaction('queued'), waiting_interaction('in_progress'),
                               ok_interaction('files/slow1')]
        code, out, err = self.omni('--first', self.first, '--recover-interval', '0.01', '--poll-wait', '5')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(SERVER.downloads, ['files/slow1'])
        r = self.rows()[-1]
        self.assertEqual(r['status'], 'ok')
        self.assertGreater(float(r['est_usd']), 0.2)

    def test_in_progress_timeout_stays_unresolved_then_recovers(self):
        SERVER.create_behavior = lambda kw: waiting_interaction('in_progress')
        SERVER.interaction = waiting_interaction('in_progress')
        est = O.estimate_usd('360p', 8)
        code, out, err = self.omni('--first', self.first, '--recover-interval', '0.01', '--poll-wait', '0.05')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        r = self.rows()[-1]
        self.assertEqual((r['status'], r['est_usd']), ('unresolved', f'{est:.3f}'))
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual((meta['interaction_id'], meta['downloaded']), ('v1_fake_interaction', False))
        # 나중에 끝나면 무료 되찾기가 같은 행을 응답 토큰 비용으로 확정한다
        SERVER.interaction = ok_interaction('files/late_ip')
        n_rows = len(self.rows())
        code, o, e = self.run_main(O.main, '--out', self.out, '--recover-only', '--poll-wait', '1')
        self.assertEqual(code, 0, e)
        self.assertEqual(len(self.rows()), n_rows)
        r = self.row_of(meta['call_token'])[0]
        self.assertEqual(r['status'], 'ok')
        self.assertNotEqual(r['est_usd'], f'{est:.3f}')    # 응답 토큰 기준 금액
        self.assertEqual(SERVER.downloads, ['files/late_ip'])
        self.assertTrue(load_json(os.path.join(self.out_dir, 'A.json'))['extendable'])
        self.assertEqual(len(SERVER.create_calls), 1)

    def test_failed_is_zero_only_when_usage_shows_no_video(self):
        failed = SimpleNamespace(id='v1_f', status='failed', output_video=None,
                                 usage={'output_tokens_by_modality': [], 'total_output_tokens': 0})
        SERVER.create_behavior = lambda kw: failed
        SERVER.interaction = failed
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_FAILED)
        self.assertEqual((self.rows()[-1]['status'], self.rows()[-1]['est_usd']), ('failed', '0.000'))
        # 토큰 정보가 없는 실패는 청구 여부를 모르는 것으로 둔다
        failed2 = SimpleNamespace(id='v1_f2', status='incomplete', output_video=None, usage=None)
        SERVER.create_behavior = lambda kw: failed2
        SERVER.interaction = failed2
        code, out, err = self.omni('--first', self.first, out='B.mp4')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(self.rows()[-1]['status'], 'unresolved')

    def test_stream_cut_after_created_uses_interaction_id(self):
        # 리뷰 E5(스트림): 첫 이벤트로 id를 받았으면 파일 목록으로 짐작하지 않고 그 id의 결과를 받는다
        def stream(kw):
            yield SimpleNamespace(event_type='interaction.created', interaction=SimpleNamespace(id='v1_stream'))
            SERVER.files.append(gen_file('files/decoy', now()))
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.create_behavior = stream
        SERVER.interaction = ok_interaction('files/streamed', iid='v1_stream')
        code, out, err = self.omni('--first', self.first, '--stream', '--recover-interval', '0.01')
        self.assertEqual(code, 0, err)
        self.assertEqual(SERVER.downloads, ['files/streamed'])
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual((meta['interaction_id'], meta['extendable']), ('v1_stream', False))
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_multiple_candidates_are_not_auto_adopted(self):
        def boom(kw):
            SERVER.files += [gen_file('files/c1', now()), gen_file('files/c2', now() + dt.timedelta(seconds=1))]
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.create_behavior = boom
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(SERVER.downloads, [])
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual(meta['candidates'], ['files/c1', 'files/c2'])
        self.assertEqual(self.row_of(meta['call_token'])[0]['status'], 'unresolved')
        self.assertIn('--recover-file', err)
        # 사람이 고른 파일로 정리
        code, o, e = self.run_main(O.main, '--out', self.out, '--recover-only', '--recover-file', 'files/c2')
        self.assertEqual(code, 0, e)
        self.assertEqual(SERVER.downloads, ['files/c2'])
        r = self.row_of(meta['call_token'])[0]
        self.assertEqual((r['status'], r['est_usd']), ('ok', f'{O.estimate_usd("360p", 8):.3f}'))
        self.assertEqual(load_json(os.path.join(self.out_dir, 'A.json'))['recovered_file'], 'files/c2')

    def test_other_unresolved_request_blocks_auto_adopt(self):
        # 앞서 결과를 못 찾은 다른 요청이 있으면, 새로 생긴 파일 하나도 그쪽의 늦은 결과일 수 있어 고르지 않는다
        tok = G.log_pending('video', O.MODEL, {'resolution': '4k', 'duration': 8}, 2.453,
                            os.path.join(self.out_dir, 'old.mp4'))
        G.finalize(tok, 2.453, 'unresolved', '시험: 앞 요청 결과 못 찾음')

        def boom(kw):
            SERVER.files.append(gen_file('files/late_or_mine', now()))
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.create_behavior = boom
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.05', '--recover-interval', '0.01')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(SERVER.downloads, [])
        self.assertIn(tok, err)

    def test_concurrent_paid_run_is_refused(self):
        # 리뷰 E6: 다른 유료 실행이 잠금을 잡고 있으면 상한 확인 전에 바로 끝낸다(업로드·요청·장부 변화 없음)
        SERVER.create_behavior = lambda kw: ok_interaction()
        text = self.ledger_text()
        with G.paid_run_lock('다른 프로세스 흉내'):
            code, out, err = self.omni('--first', self.first)
            code2, o2, e2 = self.run_main(G.main, 'image', '--model', 'gemini-3-pro-image', '--size', '4K',
                                          '--out', os.path.join(self.out_dir, 'K.png'), '--prompt-file', self.prompt,
                                          self.first)
        self.assertEqual((code, code2), (G.EXIT_BUSY, G.EXIT_BUSY))
        self.assertIn('다른 유료 실행', err)
        self.assertEqual((SERVER.create_calls, SERVER.uploads, SERVER.gen_calls), ([], [], []))
        self.assertEqual(self.ledger_text(), text)

    def test_nested_run_during_upload_cannot_pass_cap(self):
        # 리뷰 E6 그대로: 상한 확인 뒤 업로드·목록 확인 중에 다른 실행이 끼어들어도 둘 다 통과하지 못한다
        self.set_budget(self.base + 3.0, self.base + 2.9)
        it = ok_interaction('files/g')
        it.usage = dict(USAGE_4K)
        SERVER.create_behavior = lambda kw: it
        SERVER.interaction = it
        real_ref = O.referenced_names
        state = {}

        def hook(extra=()):
            if 'b' not in state:
                saved = dict(G._PAID_ATTEMPTS)
                G._PAID_ATTEMPTS.clear()
                try:
                    state['b'] = O.main(['--out', os.path.join(self.out_dir, 'B.mp4'), '--prompt-file', self.prompt,
                                         '--resolution', '4k', '--duration', '8', '--first', self.first])
                except SystemExit as e:
                    state['b'] = e.code
                G._PAID_ATTEMPTS.clear()
                G._PAID_ATTEMPTS.update(saved)
            return real_ref(extra)
        O.referenced_names = hook
        try:
            code, out, err = self.omni('--first', self.first, res='4k')
        finally:
            O.referenced_names = real_ref
        self.assertEqual(state['b'], G.EXIT_BUSY)
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertLessEqual(G.spent() - self.base, 3.0)

    def test_limit_is_rechecked_when_pending_row_is_written(self):
        # 상한 확인과 pending 기록 사이에 장부가 바뀌면(잠금 밖 기록 등) 요청 직전에 다시 막는다
        SERVER.create_behavior = lambda kw: ok_interaction()
        real_ref = O.referenced_names

        def hook(extra=()):
            G.log('video', O.MODEL, {}, 9.9, 'ok', os.path.join(self.out_dir, 'other.mp4'), '시험: 잠금 밖 기록')
            return real_ref(extra)
        O.referenced_names = hook
        try:
            code, out, err = self.omni('--first', self.first)
        finally:
            O.referenced_names = real_ref
        self.assertEqual(code, G.EXIT_CAP)
        self.assertIn('요청 직전 다시 확인', err)
        self.assertEqual(SERVER.create_calls, [])
        self.assertEqual(G.unsettled_rows(), [])

    def test_background_writes_id_first_then_polls(self):
        SERVER.create_behavior = lambda kw: waiting_interaction('in_progress', iid='v1_bg')
        seen = {}

        def during_get():
            if 'meta' not in seen:
                seen['meta'] = load_json(os.path.join(self.out_dir, 'A.json'))
                seen['row'] = G.unsettled_rows()[-1]
        SERVER.during_get = during_get
        SERVER.get_sequence = [waiting_interaction('in_progress', iid='v1_bg')]
        SERVER.interaction = ok_interaction('files/bg1', iid='v1_bg')
        code, out, err = self.omni('--first', self.first, '--background', '--recover-interval', '0.01')
        self.assertEqual(code, 0, err)
        self.assertIs(SERVER.create_calls[0].get('background'), True)
        self.assertEqual((seen['meta']['interaction_id'], seen['meta']['downloaded']), ('v1_bg', False))
        self.assertEqual(seen['row']['status'], 'pending')
        self.assertIn('v1_bg', seen['row']['note'])
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertEqual((meta['interaction_id'], meta['extendable'], meta['mode']), ('v1_bg', True, 'background'))
        self.assertEqual(self.rows()[-1]['status'], 'ok')
        self.assertEqual(SERVER.downloads, ['files/bg1'])

    def test_background_into_new_folder_writes_id_before_video(self):
        # 계획의 연결 시험(T1)처럼 아직 없는 폴더로 내보내도, 영상 전에 id를 json에 먼저 남겨야 한다
        SERVER.create_behavior = lambda kw: waiting_interaction('in_progress', iid='v1_bgnew')
        seen = {}

        def during_get():
            p = os.path.join(self.out_dir, 'newdir', 'T1.json')
            if 'meta' not in seen and os.path.exists(p):
                seen['meta'] = load_json(p)
        SERVER.during_get = during_get
        SERVER.get_sequence = [waiting_interaction('in_progress', iid='v1_bgnew')]
        SERVER.interaction = ok_interaction('files/bgnew', iid='v1_bgnew')
        code, out, err = self.omni('--first', self.first, '--background', '--recover-interval', '0.01',
                                   out=os.path.join('newdir', 'T1.mp4'))
        self.assertEqual(code, 0, err)
        self.assertEqual((seen['meta']['interaction_id'], seen['meta']['downloaded']), ('v1_bgnew', False))
        self.assertNotIn('요청 오류', out)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_background_and_stream_together_is_refused(self):
        code, out, err = self.omni('--first', self.first, '--background', '--stream')
        self.assertEqual(code, 2)
        self.assertEqual(SERVER.create_calls, [])

    def test_resolution_is_required_and_must_match_chain(self):
        SERVER.create_behavior = lambda kw: ok_interaction()
        out = os.path.join(self.out_dir, 'R.mp4')
        code, o, e = self.run_main(O.main, '--out', out, '--prompt-file', self.prompt, '--first', self.first)
        self.assertEqual(code, 2)
        prev = os.path.join(self.out_dir, 'P4k.json')
        with open(prev, 'w', encoding='utf-8') as f:
            json.dump({'interaction_id': 'v1_prev', 'resolution': '4k', 'chain_seconds': 8.0}, f)
        code, o, e = self.omni('--extend-from', prev, out='R2.mp4', res='360p')
        self.assertEqual(code, 2)
        self.assertIn('해상도', e)
        self.assertEqual(SERVER.create_calls, [])

    def test_recover_only_from_other_cwd_finds_row(self):
        # 리뷰 E7: 다른 폴더에서 실행해도 같은 출력의 미확정 행을 찾는다
        out = os.path.join(self.out_dir, 'K.mp4')
        G.log_pending('video', O.MODEL, {'resolution': '4k', 'duration': 8}, 2.553, out)
        SERVER.scheduled = [(1, gen_file('files/killed1', now() + dt.timedelta(seconds=3)))]
        cwd = os.getcwd()
        os.chdir(self.out_dir)
        try:
            code, o, e = self.run_main(O.main, '--out', out, '--recover-only', '--recover-wait', '0.05',
                                       '--recover-interval', '0.01')
        finally:
            os.chdir(cwd)
        self.assertEqual(code, 0, e)
        self.assertEqual(G.unsettled_rows(), [])
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_503_is_not_retried_and_goes_to_recovery(self):
        t = now()
        SERVER.scheduled = [(2, gen_file('files/gen503', t + dt.timedelta(seconds=1)))]

        def boom(kw):
            raise FakeStatusError(503, "{'error': {'code': 503, 'message': 'UNAVAILABLE'}}")
        SERVER.create_behavior = boom
        code, out, err = self.omni('--first', self.first, '--recover-wait', '5', '--recover-interval', '0.01')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(SERVER.downloads, ['files/gen503'])
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_400_rejection_is_not_polled(self):
        def boom(kw):
            raise FakeStatusError(400, "{'error': {'message': 'bad', 'code': 'invalid_request'}}")
        SERVER.create_behavior = boom
        before = self.rows()
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_REJECTED)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(SERVER.list_calls, 1)  # 요청 전 목록만
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual((rows[-1]['status'], rows[-1]['est_usd']), ('error', '0.000'))

    def test_budget_cap_refusal(self):
        self.set_budget(self.base + 0.1, self.base + 0.05)
        SERVER.create_behavior = lambda kw: ok_interaction()
        text = self.ledger_text()
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_CAP)
        self.assertEqual(SERVER.create_calls, [])
        self.assertEqual(SERVER.uploads, [])
        self.assertEqual(self.ledger_text(), text)
        self.assertIn('예산 상한 초과', err)

    def test_warn_line_refusal_then_allow_over_warn(self):
        self.set_budget(self.base + 10, self.base + 0.1)
        SERVER.create_behavior = lambda kw: ok_interaction()
        SERVER.interaction = ok_interaction()
        text = self.ledger_text()
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_WARN)
        self.assertEqual(SERVER.create_calls, [])
        self.assertEqual(self.ledger_text(), text)
        self.assertIn('80% 보고선', err)
        code, out, err = self.omni('--first', self.first, '--allow-over-warn')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_pending_rows_count_toward_cap(self):
        # 죽은 프로세스가 남긴 pending 행도 80% 보고선·상한 계산에 들어간다(예산: 상한 +10, 보고선 +8)
        SERVER.create_behavior = lambda kw: ok_interaction()
        G.log_pending('video', O.MODEL, {}, 7.9, os.path.join(self.out_dir, 'dead1.mp4'))
        code, out, err = self.omni('--first', self.first)      # 7.9 + 0.29 > 8
        self.assertEqual(code, G.EXIT_WARN)
        G.log_pending('video', O.MODEL, {}, 2.0, os.path.join(self.out_dir, 'dead2.mp4'))
        code, out, err = self.omni('--first', self.first, '--allow-over-warn')   # 9.9 + 0.29 > 10
        self.assertEqual(code, G.EXIT_CAP)
        self.assertEqual(SERVER.create_calls, [])
        self.assertEqual(len(G.pending_rows()), 2)

    def test_cap_option_still_works_without_budget(self):
        os.environ['COST_BUDGET_PATH'] = 'none'
        SERVER.create_behavior = lambda kw: ok_interaction()
        code, out, err = self.omni('--first', self.first, '--cap', f'{self.base + 0.1:.3f}')
        self.assertEqual(code, G.EXIT_CAP)
        self.assertEqual(SERVER.create_calls, [])

    def test_existing_output_is_not_overwritten(self):
        SERVER.create_behavior = lambda kw: ok_interaction()
        with open(os.path.join(self.out_dir, 'A.mp4'), 'wb') as f:
            f.write(b'approved')
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_EXISTS)
        self.assertEqual(SERVER.create_calls, [])
        with open(os.path.join(self.out_dir, 'A.mp4'), 'rb') as f:
            self.assertEqual(f.read(), b'approved')

    def test_extend_from_uses_previous_interaction(self):
        prev = os.path.join(self.out_dir, 'P.json')
        with open(prev, 'w', encoding='utf-8') as f:
            json.dump({'interaction_id': 'v1_prev', 'chain_seconds': 8.0}, f)
        SERVER.create_behavior = lambda kw: ok_interaction('files/ext1')
        SERVER.interaction = ok_interaction('files/ext1')
        code, out, err = self.omni('--extend-from', prev, '--duration', '4')
        self.assertEqual(code, 0, err)
        self.assertEqual(SERVER.create_calls[0]['previous_interaction_id'], 'v1_prev')
        self.assertEqual(SERVER.create_calls[0]['response_format']['duration'], '4s')
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_key_is_never_written(self):
        def boom(kw):
            raise FakeStatusError(400, f'bad request with header x-goog-api-key: {FAKE_KEY}')
        SERVER.create_behavior = boom
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_REJECTED)
        self.assertIn('***', self.rows()[-1]['note'])
        self.assert_no_key(out, err)

    def test_debug_env_is_removed(self):
        os.environ['GOOGLE_GENAI_DEBUG'] = '1'
        SERVER.create_behavior = lambda kw: ok_interaction()
        SERVER.interaction = ok_interaction()
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, 0, err)
        self.assertNotIn('GOOGLE_GENAI_DEBUG', os.environ)

    def test_download_failure_then_recover_only(self):
        SERVER.create_behavior = lambda kw: ok_interaction('files/gen9')
        SERVER.interaction = ok_interaction('files/gen9')
        SERVER.download_fail = 3
        sleeps = []
        real_sleep = time.sleep
        time.sleep = lambda s: sleeps.append(s)
        try:
            code, out, err = self.omni('--first', self.first)
        finally:
            time.sleep = real_sleep
        self.assertEqual(code, G.EXIT_FETCH)
        self.assertEqual(len(SERVER.create_calls), 1)
        r = self.rows()[-1]
        self.assertEqual(r['status'], 'ok')       # 생성은 됐으므로 비용은 잡는다
        meta = load_json(os.path.join(self.out_dir, 'A.json'))
        self.assertIs(meta['downloaded'], False)
        n_rows = len(self.rows())
        code, out, err = self.run_main(O.main, '--out', self.out, '--recover-only')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(len(self.rows()), n_rows)  # 장부 행 추가 없음
        with open(self.out, 'rb') as f:
            self.assertEqual(f.read(), b'FAKEVIDEO:files/gen9')
        self.assertIs(load_json(os.path.join(self.out_dir, 'A.json'))['downloaded'], True)

    def test_recover_only_finalizes_pending_row_of_killed_process(self):
        out = os.path.join(self.out_dir, 'K.mp4')
        token = G.log_pending('video', O.MODEL, {'resolution': '4k'}, 2.55, out)
        SERVER.files = [gen_file('files/old', now() - dt.timedelta(hours=1))]
        SERVER.scheduled = [(1, gen_file('files/killed1', now() + dt.timedelta(seconds=3)))]
        before = self.rows()
        code, out_s, err = self.run_main(O.main, '--out', out, '--recover-only', '--recover-wait', '1',
                                         '--recover-interval', '0.01')
        self.assertEqual(code, 0, err)
        self.assertEqual(SERVER.create_calls, [])
        rows = self.rows()
        self.assertEqual(len(rows), len(before))
        r = rows[-1]
        self.assertEqual((r['status'], r['est_usd']), ('ok', '2.550'))
        self.assertIn(f'[call:{token}]', r['note'])
        self.assertIn('files/killed1', r['note'])

    def test_finalize_keeps_other_rows_byte_identical(self):
        text = self.ledger_text()
        token = G.log_pending('video', O.MODEL, {'a': 1}, 1.0, os.path.join(self.out_dir, 'x.mp4'), 'line1\nline2')
        G.finalize(token, 0.5, 'ok', 'done\nok')
        new = self.ledger_text()
        self.assertTrue(new.startswith(text))
        self.assertEqual(new[len(text):].count('\n'), 1)
        self.assertEqual(self.rows()[-1]['status'], 'ok')

    def test_once_guard(self):
        G._PAID_ATTEMPTS.clear()
        G.once('omni')
        with self.assertRaises(RuntimeError):
            G.once('image')

    def test_estimates(self):
        self.assertAlmostEqual(O.estimate_usd('4k', 8), 2.453, places=3)
        self.assertAlmostEqual(O.estimate_usd('4k', 8, True), 2.553, places=3)
        self.assertAlmostEqual(O.estimate_usd('4k', 4, True), 1.336, places=3)
        self.assertAlmostEqual(O.estimate_usd('360p', 8), 0.29, places=2)
        # 실제 4K 첫 클립 토큰(E1_4k.json)으로 계산한 값은 기존 보정값 범위($2.44~2.51) 안
        u = {'output_tokens_by_modality': [{'modality': 'video', 'tokens': 139008}], 'total_output_tokens': 139860,
             'total_thought_tokens': 374, 'total_input_tokens': 1414}
        usd, _ = O.usage_cost(u)
        self.assertTrue(2.44 <= usd <= 2.51, usd)


# ---------------------------------------------------------------- 이미지 시험

class ImagePaidSafety(Base):
    def image_response(self):
        from PIL import Image
        b1, b2 = io.BytesIO(), io.BytesIO()
        Image.new('RGB', (32, 18), (255, 0, 0)).save(b1, 'PNG')
        Image.new('RGB', (64, 36), (0, 128, 0)).save(b2, 'JPEG', quality=100)
        self.final_jpeg = b2.getvalue()

        def part(data, mime, thought=False):
            return SimpleNamespace(inline_data=SimpleNamespace(data=data, mime_type=mime), thought=thought)
        return SimpleNamespace(
            candidates=[SimpleNamespace(content=SimpleNamespace(parts=[part(b1.getvalue(), 'image/png', True),
                                                                       part(self.final_jpeg, 'image/jpeg')]))],
            usage_metadata=SimpleNamespace(prompt_token_count=1300, candidates_token_count=2000,
                                           thoughts_token_count=200, total_token_count=3500))

    def image(self, *extra, model='gemini-3-pro-image', size='4K'):
        self.out = os.path.join(self.out_dir, 'K0.png')
        return self.run_main(G.main, 'image', '--model', model, '--size', size, '--out', self.out,
                             '--prompt-file', self.prompt, *extra, self.first)

    def test_pro_4k_image_saved_once_with_cost(self):
        SERVER.image_behavior = self.image_response
        before = self.rows()
        code, out, err = self.image()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.gen_calls), 1)
        cfg = SERVER.gen_calls[0]['config']
        self.assertEqual(cfg.image_config.image_size, '4K')
        self.assertEqual(cfg.image_config.aspect_ratio, '16:9')
        with open(os.path.join(self.out_dir, 'K0.jpg'), 'rb') as f:
            self.assertEqual(f.read(), self.final_jpeg)     # 생각 단계 이미지가 아니라 최종 이미지
        from PIL import Image
        with Image.open(self.out) as im:
            self.assertEqual((im.format, im.size), ('PNG', (64, 36)))
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual((rows[-1]['status'], rows[-1]['est_usd']), ('ok', '0.240'))
        self.assertIn('image/jpeg', rows[-1]['note'])

    def test_image_error_is_single_attempt_and_stays_unresolved(self):
        def boom():
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.image_behavior = boom
        code, out, err = self.image()
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(len(SERVER.gen_calls), 1)
        self.assertEqual((self.rows()[-1]['status'], self.rows()[-1]['est_usd']), ('unresolved', '0.240'))
        self.assertIn('청구됐을 수 있습니다', err)
        self.assertAlmostEqual(G.spent(), self.base + 0.24, places=3)
        # 같은 출력으로 다시 실행하면 막고, 사람이 결제 화면을 확인해 0달러로 바꾼 뒤에만 다시 보낸다
        code, out, err = self.image()
        self.assertEqual(code, G.EXIT_EXISTS)
        self.assertEqual(len(SERVER.gen_calls), 1)
        token = G.unsettled_rows()[-1]['token']
        code, o, e = self.run_main(G.main, 'mark-not-billed', token, '--reason', '결제 화면 확인(시험)')
        self.assertEqual(code, 0, e)
        self.assertAlmostEqual(G.spent(), self.base, places=3)
        SERVER.image_behavior = self.image_response
        code, out, err = self.image()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.gen_calls), 2)

    def test_image_budget_and_warn_guard(self):
        SERVER.image_behavior = self.image_response
        self.set_budget(self.base + 0.1, self.base + 0.05)
        code, out, err = self.image()
        self.assertEqual(code, G.EXIT_CAP)
        self.set_budget(self.base + 5, self.base + 0.1)
        code, out, err = self.image()
        self.assertEqual(code, G.EXIT_WARN)
        self.assertEqual(SERVER.gen_calls, [])
        code, out, err = self.image('--allow-over-warn')   # 하위 명령 뒤에 붙여도 됨
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.gen_calls), 1)

    def test_flash_4k_refused_before_call(self):
        SERVER.image_behavior = self.image_response
        code, out, err = self.image(model='gemini-3.1-flash-image', size='4K')
        self.assertNotEqual(code, 0)
        self.assertEqual(SERVER.gen_calls, [])


# ---------------------------------------------------------------- 명령줄 도움말(예전 호출 방식 호환)

class CliHelp(unittest.TestCase):
    def test_help_texts_render(self):
        # 도움말 문구의 '%'가 argparse에서 깨지지 않는지(예: '80%% 보고선'), 예전 --cap 위치도 그대로 되는지
        cases = [(G.main, ['--help']), (G.main, ['image', '--help']), (G.main, ['video', '--help']),
                 (G.main, ['--cap', '30', 'video', '--help']), (O.build_parser().parse_args, ['--help'])]
        for fn, argv in cases:
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf), self.assertRaises(SystemExit) as cm:
                fn(argv)
            self.assertEqual(cm.exception.code, 0, argv)
            self.assertIn('80% 보고선', buf.getvalue(), argv)


# ---------------------------------------------------------------- 실제 SDK(오프라인) 시험

class RealSdkOffline(unittest.TestCase):
    """설치된 google-genai로 실제 요청 객체를 만들되, MockTransport로 받아서 POST 수만 센다(네트워크 없음)."""

    def setUp(self):
        import httpx
        self.httpx = httpx
        genai_mod.Client = REAL_CLIENT
        self.calls, self.mode = [], '503'

        def handler(req):
            self.calls.append(req.method)
            assert req.url.host == '127.0.0.1'
            if self.mode == 'disconnect':
                raise httpx.RemoteProtocolError('Server disconnected without sending a response.', request=req)
            if self.mode == '400':
                return httpx.Response(400, json={'error': {'code': 400, 'message': 'mock bad request'}})
            return httpx.Response(503, json={'error': {'code': 503, 'message': 'mock', 'status': 'UNAVAILABLE'}})
        self.handler = handler

    def kw(self):
        return dict(base_url='http://127.0.0.1:9/', timeout=30_000,
                    httpx_client=self.httpx.Client(transport=self.httpx.MockTransport(self.handler)))

    def create(self, c):
        self.calls.clear()
        err = None
        try:
            c.interactions.create(model=O.MODEL, input=[{'type': 'text', 'text': 'x'}],
                                  response_format={'type': 'video', 'delivery': 'uri', 'aspect_ratio': '16:9',
                                                   'duration': '4s', 'resolution': '360p'}, store=True)
        except Exception as e:  # noqa: BLE001
            err = e
        return self.calls.count('POST'), err

    def test_paid_client_sends_exactly_one_post(self):
        c = O.make_paid_client(key=FAKE_KEY, **self.kw())
        for mode, code in (('503', 503), ('disconnect', None), ('400', 400)):
            self.mode = mode
            n, err = self.create(c)
            self.assertEqual(n, 1, mode)
            self.assertIsNotNone(err)
            self.assertEqual(G.status_code_of(err), code, mode)
            self.assertNotIn(FAKE_KEY, G.scrub(err))

    def test_default_client_would_retry(self):
        # 대조군: 기본 설정이면 503에 같은 생성 요청을 여러 번 보낸다(그래서 끄는 것이 필요)
        self.mode = '503'
        n, _ = self.create(O.make_poll_client(key=FAKE_KEY, **self.kw()))
        self.assertGreater(n, 1)

    def test_legacy_image_client_single_attempt(self):
        self.mode = '503'
        c = G.make_client(key=FAKE_KEY, **self.kw())
        self.calls.clear()
        with self.assertRaises(Exception):
            c.models.generate_content(model='gemini-3-pro-image', contents=['x'])
        self.assertEqual(self.calls.count('POST'), 1)


if __name__ == '__main__':
    unittest.main(verbosity=2)
