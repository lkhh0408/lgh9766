"""유료 생성 스크립트(omni_gen.py, gen_api.py) 안전 시험. 네트워크·API 호출 없음.

- google.genai.Client를 가짜 객체로 바꿔 끼워 성공·끊김·되찾기·거절·예산 상황을 흉내 낸다.
- 실제 SDK(google-genai) 시험은 가짜 키 + httpx.MockTransport로만 하고, 요청이 몇 번 나가는지 센다.
- 장부는 임시 복사본(COST_LEDGER_PATH), 예산 파일도 임시 파일(COST_BUDGET_PATH)만 쓴다.
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


def ok_interaction(name='files/gen1'):
    return SimpleNamespace(id='v1_fake_interaction', status='completed', usage=dict(USAGE),
                           output_video=SimpleNamespace(
                               uri=f'https://generativelanguage.googleapis.com/v1beta/{name}:download?alt=media',
                               mime_type='video/mp4'))


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

    def omni(self, *args, out='A.mp4'):
        self.out = os.path.join(self.out_dir, out)
        base = ['--out', self.out, '--prompt-file', self.prompt, '--resolution', '360p', '--duration', '8']
        return self.run_main(O.main, *(base + list(args)))

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
        meta = json.load(open(os.path.join(self.out_dir, 'A.json'), encoding='utf-8'))
        self.assertEqual(meta['interaction_id'], 'v1_fake_interaction')
        self.assertTrue(meta['extendable'])
        self.assertEqual(meta['output_file'], 'files/gen1')
        self.assertAlmostEqual(meta['cost']['actual_usd'], actual, places=4)
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
        meta = json.load(open(os.path.join(self.out_dir, 'A.json'), encoding='utf-8'))
        self.assertIsNone(meta['interaction_id'])
        self.assertEqual(meta['recovered_file'], 'files/gen2')
        self.assertIs(meta['extendable'], False)
        self.assertIn('다시 보내지 않습니다', out)
        # 되찾은 결과로 연장하려 하면 유료 요청 없이 거절
        code, out2, err2 = self.omni('--extend-from', os.path.join(self.out_dir, 'A.json'), out='B.mp4')
        self.assertEqual(code, 2)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertIn('연장 재료로 쓸 수 없습니다', err2)

    def test_disconnect_no_file_logs_error_and_warns(self):
        def boom(kw):
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.create_behavior = boom
        before = self.rows()
        code, out, err = self.omni('--first', self.first, '--recover-wait', '0.15', '--recover-interval', '0.03')
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertGreaterEqual(SERVER.list_calls, 3)
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual((rows[-1]['status'], rows[-1]['est_usd']), ('error', '0.000'))
        self.assertIn('청구됐을 수 있음', rows[-1]['note'])
        self.assertIn('청구됐을 수 있습니다', err)
        self.assertIn('--recover-only', err)
        self.assertFalse(os.path.exists(self.out))
        self.assertAlmostEqual(G.spent(), self.base, places=3)

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
        # 죽은 프로세스가 남긴 pending 행도 상한 계산에 들어간다
        G.log_pending('video', O.MODEL, {}, 9.5, os.path.join(self.out_dir, 'dead.mp4'))
        SERVER.create_behavior = lambda kw: ok_interaction()
        code, out, err = self.omni('--first', self.first)
        self.assertEqual(code, G.EXIT_CAP)
        self.assertEqual(SERVER.create_calls, [])

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
        meta = json.load(open(os.path.join(self.out_dir, 'A.json'), encoding='utf-8'))
        self.assertIs(meta['downloaded'], False)
        n_rows = len(self.rows())
        code, out, err = self.run_main(O.main, '--out', self.out, '--recover-only')
        self.assertEqual(code, 0, err)
        self.assertEqual(len(SERVER.create_calls), 1)
        self.assertEqual(len(self.rows()), n_rows)  # 장부 행 추가 없음
        with open(self.out, 'rb') as f:
            self.assertEqual(f.read(), b'FAKEVIDEO:files/gen9')
        self.assertIs(json.load(open(os.path.join(self.out_dir, 'A.json'), encoding='utf-8'))['downloaded'], True)

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
        im = Image.open(self.out)
        self.assertEqual((im.format, im.size), ('PNG', (64, 36)))
        rows = self.rows()
        self.assertEqual(len(rows), len(before) + 1)
        self.assertEqual((rows[-1]['status'], rows[-1]['est_usd']), ('ok', '0.240'))
        self.assertIn('image/jpeg', rows[-1]['note'])

    def test_image_error_is_single_attempt_and_warns(self):
        def boom():
            raise FakeDisconnect('Server disconnected without sending a response.')
        SERVER.image_behavior = boom
        code, out, err = self.image()
        self.assertEqual(code, G.EXIT_UNKNOWN)
        self.assertEqual(len(SERVER.gen_calls), 1)
        self.assertEqual((self.rows()[-1]['status'], self.rows()[-1]['est_usd']), ('error', '0.000'))
        self.assertIn('청구됐을 수 있습니다', err)

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
