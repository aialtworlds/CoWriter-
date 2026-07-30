"""
Fase 4 tests: /api/analysis_runs/{id}/critical_reading

Verifies the full credit-economy contract for the AI Critical Reading feature:
- Auth guard (401 without token)
- Successful run: exactly 5 judgment cards (checks 9-13), each with tipo='julgamento',
  confiabilidade='ia', numero in {9,10,11,12,13}, and check_type covering all 5.
- Findings are contextual to the sample scene (verify AI, not stub).
- Credit accounting: wallet decrements by ceil(words/1000), a 'consumo' credit_transactions
  row is added with quantidade == -needed, and analysis_runs.creditos_consumidos updates.
- Idempotency: second POST returns ja_executada=true and does NOT re-charge or duplicate rows.
- Persistence: GET /api/analysis_runs/{id} returns leitura_critica_executada=true with same
  5 rows after a fresh session.
- Insufficient balance: 402 with body {'erro':'saldo_insuficiente','necessario':N,'saldo':M}
  and NO wallet debit / NO credit_transactions row created.
- Regression: Facts tab (checks 1-8) remains free and works alongside.
"""
import os
import math
import time
import pytest
import requests

BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
SUPABASE_URL = 'https://cexplgtcimdezzxuimkv.supabase.co'
SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNleHBsZ3RjaW1kZXp6eHVpbWt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY1NDYsImV4cCI6MjEwMDk0MjU0Nn0.pxENcn8FEms5TXkwz-SYYOOCXLeKyAr8wtrG6358zXY'

DEMO = ('demo.escritor@cowriter.test', 'CoWriter#2026')

SAMPLE_TEXT = (
    'Marina entrou na cozinha e encontrou Tomas sentado à mesa, olhando para o copo vazio.\n\n'
    '"Você viu a Clara hoje?", perguntou Marina, tentando parecer calma.\n\n'
    '"Vi", disse Tomas. "Ela estava na estação."\n\n'
    '"E o que ela disse?"\n\n'
    '"Nada demais. Perguntou se eu tinha visto você."\n\n'
    'Marina sentiu o estômago apertar, mas manteve o rosto neutro. Ela sabia que Tomas estava '
    'escondendo algo — a forma como ele evitava olhar diretamente pra ela era familiar demais.\n\n'
    '"Tomas, olha pra mim."\n\n'
    'Ele finalmente ergueu os olhos. Naquele instante, a porta se abriu com um estrondo e Clara '
    'entrou, o rosto vermelho de raiva. Sem dizer uma palavra, ela atravessou a cozinha e deu um '
    'tapa no rosto de Tomas. O som ecoou pela casa vazia.\n\n'
    'Tomas não disse nada. Marina também não. Os três ficaram ali, imóveis, como se o tempo '
    'tivesse parado por um segundo inteiro antes que alguém respirasse de novo.'
)


def _supa_login(email, password):
    r = requests.post(
        f'{SUPABASE_URL}/auth/v1/token?grant_type=password',
        headers={'apikey': SUPABASE_ANON, 'Content-Type': 'application/json'},
        json={'email': email, 'password': password}, timeout=15,
    )
    r.raise_for_status()
    return r.json()['access_token']


@pytest.fixture(scope='module')
def token():
    try:
        return _supa_login(*DEMO)
    except Exception as e:
        pytest.skip(f'Login failed: {e}')


@pytest.fixture()
def client(token):
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    return s


@pytest.fixture(scope='module')
def project_id(token):
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    r = s.post(f'{BASE_URL}/api/projects',
               json={'nome': f'TEST_Fase4_{int(time.time())}', 'idioma': 'pt-BR', 'genero': 'Ficção'})
    r.raise_for_status()
    return r.json()['id']


def _create_and_analyze(client, project_id, text, title_suffix=''):
    r = client.post(f'{BASE_URL}/api/projects/{project_id}/chapters',
                    json={'titulo': f'TEST_Fase4_Cap{title_suffix}', 'texto_bruto': text})
    assert r.status_code == 201, r.text
    chapter_id = r.json()['id']
    words = r.json()['palavras']

    r = client.post(f'{BASE_URL}/api/chapters/{chapter_id}/analyze')
    assert r.status_code == 201, r.text
    an = r.json()
    return {
        'chapter_id': chapter_id,
        'analysis_run_id': an['analysis_run_id'],
        'palavras': words,
        'creditos_consumidos_pre': an['creditos_consumidos'],
    }


# ---------------- Auth guard ----------------

class TestAuthGuard:
    def test_401_without_token(self):
        r = requests.post(f'{BASE_URL}/api/analysis_runs/00000000-0000-0000-0000-000000000000/critical_reading')
        assert r.status_code == 401


# ---------------- Success flow + Idempotency ----------------

class TestCriticalReadingFlow:
    state = {}

    def test_01_setup_chapter_and_analyze(self, client, project_id):
        info = _create_and_analyze(client, project_id, SAMPLE_TEXT, title_suffix='_Main')
        assert info['creditos_consumidos_pre'] == 0
        assert info['palavras'] > 0
        # ~150 words → expected credits = 1
        expected = math.ceil(info['palavras'] / 1000)
        assert expected == 1, f"expected 1 credit for ~150 words, got {expected} (palavras={info['palavras']})"

        # Wallet snapshot BEFORE critical reading
        wallet_before = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        txs_before = client.get(f'{BASE_URL}/api/wallet/transactions').json()

        TestCriticalReadingFlow.state.update({
            'chapter_id': info['chapter_id'],
            'analysis_run_id': info['analysis_run_id'],
            'palavras': info['palavras'],
            'expected_credits': expected,
            'wallet_before': wallet_before,
            'tx_count_before': len(txs_before),
        })

    def test_02_run_critical_reading_success(self, client):
        s = TestCriticalReadingFlow.state
        r = client.post(f"{BASE_URL}/api/analysis_runs/{s['analysis_run_id']}/critical_reading", timeout=90)
        assert r.status_code == 201, f'unexpected: {r.status_code} {r.text}'
        data = r.json()

        assert data['analysis_run_id'] == s['analysis_run_id']
        assert data['creditos_consumidos'] == s['expected_credits']
        assert data['ja_executada'] is False

        # 5 checks
        lc = data['leitura_critica']
        assert isinstance(lc, list) and len(lc) == 5, f'expected 5 checks, got {len(lc)}'

        check_types = {c['check_type'] for c in lc}
        expected_types = {'scene_objective', 'scene_magnetism', 'linger_cortar', 'subtext_frame', 'voiceprint_pov_filter'}
        assert check_types == expected_types, f'missing: {expected_types - check_types}'

        numeros = sorted(c['numero'] for c in lc)
        assert numeros == [9, 10, 11, 12, 13], f'expected numeros 9-13, got {numeros}'

        for c in lc:
            assert c['tipo'] == 'julgamento', f"{c['check_type']} tipo wrong: {c['tipo']}"
            assert c['confiabilidade'] == 'ia', f"{c['check_type']} confiabilidade wrong: {c['confiabilidade']}"
            # Real AI response must have a summary (not a placeholder / stub)
            assert 'summary' in c
            assert not c.get('erro'), f"{c['check_type']} returned erro=True (Claude parse failed): {c.get('summary')}"

        TestCriticalReadingFlow.state['first_response'] = data

    def test_03_findings_contextual_to_scene(self, client):
        """Real AI check: at least ONE of the checks must reference identifiable scene elements
        (Marina, Tomas, Clara, tapa/estação/cozinha) in its summary or a finding.
        This distinguishes real AI output from a generic stub."""
        data = TestCriticalReadingFlow.state['first_response']
        contextual_terms = ('marina', 'tomas', 'tomás', 'clara', 'tapa', 'cozinha', 'estação', 'estacao')
        haystack_parts = []
        for c in data['leitura_critica']:
            haystack_parts.append((c.get('summary') or '').lower())
            for d in c.get('detalhes', []):
                haystack_parts.append((d.get('trecho') or '').lower())
                haystack_parts.append((d.get('issue') or '').lower())
                haystack_parts.append((d.get('sugestao') or '').lower())
        haystack = '\n'.join(haystack_parts)
        matches = [t for t in contextual_terms if t in haystack]
        assert matches, f'No contextual scene terms found in AI output — looks like a stub. Sample: {haystack[:400]!r}'

    def test_04_wallet_debited_exactly(self, client):
        s = TestCriticalReadingFlow.state
        wallet_after = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        expected_after = s['wallet_before'] - s['expected_credits']
        assert wallet_after == expected_after, (
            f'wallet mismatch: before={s["wallet_before"]}, expected_after={expected_after}, actual={wallet_after}'
        )

    def test_05_credit_transaction_row_added(self, client):
        s = TestCriticalReadingFlow.state
        txs = client.get(f'{BASE_URL}/api/wallet/transactions').json()
        assert len(txs) == s['tx_count_before'] + 1, (
            f'expected exactly +1 transaction row, before={s["tx_count_before"]}, after={len(txs)}'
        )
        # Most recent should be the consumo (transactions are ordered DESC typically)
        consumo_txs = [t for t in txs if t.get('tipo') == 'consumo']
        assert consumo_txs, 'no consumo transaction row found'
        latest = consumo_txs[0]
        assert float(latest['quantidade']) == -s['expected_credits'], (
            f"consumo quantidade wrong: {latest['quantidade']} vs -{s['expected_credits']}"
        )

    def test_06_analysis_run_persisted_state(self, client):
        s = TestCriticalReadingFlow.state
        r = client.get(f"{BASE_URL}/api/analysis_runs/{s['analysis_run_id']}")
        assert r.status_code == 200
        data = r.json()
        assert data['leitura_critica_executada'] is True
        assert float(data['creditos_consumidos']) == s['expected_credits']
        assert len(data['leitura_critica']) == 5
        # Facts still there (checks 1-8) — free regression
        assert len(data['fatos']) == 8, f"fatos should still be 8, got {len(data['fatos'])}"

    def test_07_idempotency_second_call_no_recharge(self, client):
        s = TestCriticalReadingFlow.state
        wallet_before_2nd = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        tx_count_before_2nd = len(client.get(f'{BASE_URL}/api/wallet/transactions').json())

        r = client.post(f"{BASE_URL}/api/analysis_runs/{s['analysis_run_id']}/critical_reading", timeout=30)
        assert r.status_code == 201, f'expected cached 201, got {r.status_code}: {r.text}'
        data = r.json()
        assert data.get('ja_executada') is True, 'second call must return ja_executada=true'
        assert float(data['creditos_consumidos']) == s['expected_credits']
        assert len(data['leitura_critica']) == 5

        wallet_after_2nd = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        tx_count_after_2nd = len(client.get(f'{BASE_URL}/api/wallet/transactions').json())

        assert wallet_after_2nd == wallet_before_2nd, 'wallet was re-charged on idempotent call'
        assert tx_count_after_2nd == tx_count_before_2nd, 'new tx row added on idempotent call'


# ---------------- Insufficient balance (402) ----------------

class TestInsufficientBalance:
    """Create a big chapter that requires more credits than currently in the wallet, then verify
    POST critical_reading returns 402 with the documented body and NO side effects (no debit,
    no tx row, no check_results rows)."""

    def test_402_response_and_no_side_effects(self, client, project_id):
        # Read current wallet
        current_balance = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        # We need words such that ceil(words/1000) > balance → words > balance*1000
        # SAMPLE_TEXT is ~150 words; multiplier = ceil((balance+2)*1000 / 150) gives us enough buffer.
        sample_words = len(SAMPLE_TEXT.split())
        big_text_multiplier = math.ceil(((current_balance + 2) * 1000) / max(sample_words, 1))
        big_text = (SAMPLE_TEXT + '\n\n') * big_text_multiplier

        info = _create_and_analyze(client, project_id, big_text, title_suffix='_402')
        expected_needed = math.ceil(info['palavras'] / 1000)
        assert expected_needed > current_balance, (
            f'test setup wrong: needed={expected_needed}, balance={current_balance}'
        )

        wallet_before = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        tx_before = len(client.get(f'{BASE_URL}/api/wallet/transactions').json())

        r = client.post(f"{BASE_URL}/api/analysis_runs/{info['analysis_run_id']}/critical_reading", timeout=30)
        assert r.status_code == 402, f'expected 402, got {r.status_code}: {r.text}'

        # FastAPI HTTPException wraps dict detail in {"detail": {...}}
        body = r.json()
        detail = body.get('detail', body)
        assert detail.get('erro') == 'saldo_insuficiente', f'body: {body}'
        assert detail.get('necessario') == expected_needed, f'necessario mismatch: {detail}'
        assert float(detail.get('saldo')) == wallet_before

        # No side effects
        wallet_after = float(client.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos'])
        tx_after = len(client.get(f'{BASE_URL}/api/wallet/transactions').json())
        assert wallet_after == wallet_before, 'wallet changed on 402 attempt'
        assert tx_after == tx_before, 'new tx row on 402 attempt'

        # analysis_run must show leitura_critica_executada=False and no judgment rows
        run = client.get(f"{BASE_URL}/api/analysis_runs/{info['analysis_run_id']}").json()
        assert run['leitura_critica_executada'] is False
        assert len(run['leitura_critica']) == 0


# ---------------- Ownership ----------------

class TestOwnershipCriticalReading:
    def test_other_user_cannot_run_critical_reading(self, token):
        # login as user B
        try:
            token_b = _supa_login('demo.escritor2@cowriter.test', 'CoWriter#2026')
        except Exception as e:
            pytest.skip(f'User B login failed: {e}')

        client_a = requests.Session()
        client_a.headers.update({'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
        client_b = requests.Session()
        client_b.headers.update({'Authorization': f'Bearer {token_b}', 'Content-Type': 'application/json'})

        # User A creates and analyzes
        r = client_a.post(f'{BASE_URL}/api/projects',
                          json={'nome': f'TEST_Owned_F4_{int(time.time())}', 'idioma': 'pt-BR'})
        pid = r.json()['id']
        r = client_a.post(f'{BASE_URL}/api/projects/{pid}/chapters',
                          json={'titulo': 'TEST_Owned', 'texto_bruto': 'texto curto de teste.'})
        cid = r.json()['id']
        r = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        arid = r.json()['analysis_run_id']

        # User B tries critical reading → must be 404 (no ownership)
        r = client_b.post(f'{BASE_URL}/api/analysis_runs/{arid}/critical_reading')
        assert r.status_code == 404, f'RLS breach: B got {r.status_code} on A\'s critical_reading'
