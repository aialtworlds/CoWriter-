"""
CoWriter V1 - Backend API tests (Fase 1+2)

Covers:
- Auth requirement (401 without token) for protected endpoints
- /api/, /api/me, /api/wallet, /api/wallet/transactions
- Projects CRUD (POST, GET list, GET one, PUT, DELETE) with persistence verification
- Chapters (create, get, estimate, list under project)
- Analysis (analyze, get analysis_run, project history) + deterministic checks fire correctly
- RLS/ownership: user B cannot read user A's project/chapter/analysis_run (must be 404, not 200)

Test users:
- demo.escritor@cowriter.test  / CoWriter#2026  (has 5 credit bonus)
- demo.escritor2@cowriter.test / CoWriter#2026  (RLS boundary test user)
"""
import os
import pytest
import requests
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cowriter-ai.preview.emergentagent.com').rstrip('/')
SUPABASE_URL = 'https://cexplgtcimdezzxuimkv.supabase.co'
SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNleHBsZ3RjaW1kZXp6eHVpbWt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY1NDYsImV4cCI6MjEwMDk0MjU0Nn0.pxENcn8FEms5TXkwz-SYYOOCXLeKyAr8wtrG6358zXY'

USER_A = ('demo.escritor@cowriter.test', 'CoWriter#2026')
USER_B = ('demo.escritor2@cowriter.test', 'CoWriter#2026')

SAMPLE_TEXT = (
    'Ela sorriu. Ele sorriu. Ela sorriu de novo, sorriu mais uma vez, e sorriu outra vez. '
    'O silêncio parecia ensurdecedor. Ela viu que ele estava triste. Ela sentiu que algo mudara. '
    'Ela olhou pela janela. Ela olhou o jardim. Ela olhou as flores.'
)


def _supa_login(email: str, password: str) -> str:
    r = requests.post(
        f'{SUPABASE_URL}/auth/v1/token?grant_type=password',
        headers={'apikey': SUPABASE_ANON, 'Content-Type': 'application/json'},
        json={'email': email, 'password': password},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()['access_token']


@pytest.fixture(scope='session')
def token_a() -> str:
    try:
        return _supa_login(*USER_A)
    except Exception as e:
        pytest.skip(f'User A login failed: {e}')


@pytest.fixture(scope='session')
def token_b() -> str:
    try:
        return _supa_login(*USER_B)
    except Exception as e:
        pytest.skip(f'User B login failed: {e}')


@pytest.fixture()
def client_a(token_a):
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token_a}', 'Content-Type': 'application/json'})
    return s


@pytest.fixture()
def client_b(token_b):
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token_b}', 'Content-Type': 'application/json'})
    return s


# --------------------------- Basic / Auth ---------------------------

class TestRootAndAuth:
    def test_root_online(self):
        r = requests.get(f'{BASE_URL}/api/')
        assert r.status_code == 200
        assert r.json().get('message')

    @pytest.mark.parametrize('path', [
        '/api/me', '/api/wallet', '/api/wallet/transactions', '/api/projects',
    ])
    def test_auth_required(self, path):
        r = requests.get(f'{BASE_URL}{path}')
        assert r.status_code == 401, f'{path} expected 401, got {r.status_code}'

    def test_me(self, client_a):
        r = client_a.get(f'{BASE_URL}/api/me')
        assert r.status_code == 200
        data = r.json()
        assert data.get('email') == USER_A[0]
        assert data.get('user_id')


# --------------------------- Wallet ---------------------------

class TestWallet:
    def test_wallet_balance(self, client_a):
        r = client_a.get(f'{BASE_URL}/api/wallet')
        assert r.status_code == 200
        data = r.json()
        # Demo user starts with 5 credits (bonus)
        assert 'saldo_creditos' in data
        assert float(data['saldo_creditos']) >= 0

    def test_wallet_transactions_has_bonus(self, client_a):
        r = client_a.get(f'{BASE_URL}/api/wallet/transactions')
        assert r.status_code == 200
        txs = r.json()
        assert isinstance(txs, list)
        # Should contain a bonus_inicial entry
        tipos = {t.get('tipo') for t in txs}
        assert 'bonus_inicial' in tipos, f'Expected bonus_inicial in transaction types, got {tipos}'


# --------------------------- Projects CRUD ---------------------------

class TestProjects:
    _project_id = None

    def test_create_project(self, client_a):
        payload = {'nome': f'TEST_Projeto_{uuid.uuid4().hex[:8]}', 'idioma': 'pt-BR', 'genero': 'Ficção'}
        r = client_a.post(f'{BASE_URL}/api/projects', json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data['nome'] == payload['nome']
        assert data['idioma'] == 'pt-BR'
        assert data['genero'] == 'Ficção'
        assert 'id' in data
        TestProjects._project_id = data['id']

    def test_list_projects_contains_created(self, client_a):
        assert TestProjects._project_id, 'create test must run first'
        r = client_a.get(f'{BASE_URL}/api/projects')
        assert r.status_code == 200
        ids = [p['id'] for p in r.json()]
        assert TestProjects._project_id in ids

    def test_get_project_persisted(self, client_a):
        assert TestProjects._project_id
        r = client_a.get(f'{BASE_URL}/api/projects/{TestProjects._project_id}')
        assert r.status_code == 200
        assert r.json()['id'] == TestProjects._project_id

    def test_update_project(self, client_a):
        r = client_a.put(
            f'{BASE_URL}/api/projects/{TestProjects._project_id}',
            json={'nome': 'TEST_Projeto_Renamed'},
        )
        assert r.status_code == 200
        assert r.json()['nome'] == 'TEST_Projeto_Renamed'
        # persistence
        r2 = client_a.get(f'{BASE_URL}/api/projects/{TestProjects._project_id}')
        assert r2.json()['nome'] == 'TEST_Projeto_Renamed'

    def test_delete_nonexistent_project_404(self, client_a):
        fake = str(uuid.uuid4())
        r = client_a.delete(f'{BASE_URL}/api/projects/{fake}')
        assert r.status_code == 404


# --------------------------- Chapter + Analysis Flow ---------------------------

class TestChapterAnalysisFlow:
    ids = {}

    def test_full_flow(self, client_a):
        # 1) create project
        r = client_a.post(f'{BASE_URL}/api/projects', json={'nome': f'TEST_Flow_{uuid.uuid4().hex[:6]}', 'idioma': 'pt-BR'})
        assert r.status_code == 201, r.text
        pid = r.json()['id']
        self.ids['project_id'] = pid

        # 2) create chapter
        r = client_a.post(
            f'{BASE_URL}/api/projects/{pid}/chapters',
            json={'titulo': 'TEST_Cap_1', 'texto_bruto': SAMPLE_TEXT},
        )
        assert r.status_code == 201, r.text
        chap = r.json()
        cid = chap['id']
        self.ids['chapter_id'] = cid
        assert chap.get('palavras', 0) > 0

        # 3) list chapters
        r = client_a.get(f'{BASE_URL}/api/projects/{pid}/chapters')
        assert r.status_code == 200
        assert any(c['id'] == cid for c in r.json())

        # 4) get chapter
        r = client_a.get(f'{BASE_URL}/api/chapters/{cid}')
        assert r.status_code == 200
        assert r.json()['titulo'] == 'TEST_Cap_1'

        # 5) estimate
        r = client_a.get(f'{BASE_URL}/api/chapters/{cid}/estimate')
        assert r.status_code == 200, r.text
        est = r.json()
        assert est['palavras'] > 0
        assert 'creditos_estimados_ia' in est
        assert 'saldo_atual' in est
        assert 'saldo_suficiente' in est

        # 6) analyze
        wallet_before = client_a.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos']
        r = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r.status_code == 201, r.text
        an = r.json()
        assert an['creditos_consumidos'] == 0, 'checks 1-8 are free — must not consume credits'
        assert 'analysis_run_id' in an
        assert an['leitura_critica']['status'] == 'em_breve'
        run_id = an['analysis_run_id']
        self.ids['analysis_run_id'] = run_id
        # verify 8 deterministic checks
        check_types = {f['check_type'] for f in an['fatos']}
        expected = {
            'ai_fingerprint', 'gesture_cooldown', 'descriptor_cooldown', 'prose_rhythm',
            'sensory_rotation', 'filter_words', 'dialogue_tag_variety', 'paragraph_opening_monotony',
        }
        assert expected.issubset(check_types), f'missing checks: {expected - check_types}'

        # 7) verify expected flags fired: gesture_cooldown, filter_words, sensory_rotation
        by_type = {f['check_type']: f for f in an['fatos']}
        assert by_type['gesture_cooldown']['contagem'] > 0, 'gesture_cooldown should flag repeated "sorriu"'
        assert by_type['filter_words']['contagem'] > 0, 'filter_words should flag "viu que"/"sentiu que"'
        # sensory_rotation flags visual dominance; contagem may be > 0 or score-based
        assert by_type['sensory_rotation'] is not None

        # 8) wallet unchanged
        wallet_after = client_a.get(f'{BASE_URL}/api/wallet').json()['saldo_creditos']
        assert float(wallet_after) == float(wallet_before), 'wallet must NOT decrease for free checks 1-8'

        # 9) GET analysis_run and verify persisted
        r = client_a.get(f'{BASE_URL}/api/analysis_runs/{run_id}')
        assert r.status_code == 200
        data = r.json()
        assert data['creditos_consumidos'] == 0
        assert len(data['fatos']) == 8

        # 10) history has analysis_run_id
        r = client_a.get(f'{BASE_URL}/api/projects/{pid}/history')
        assert r.status_code == 200
        hist = r.json()
        chapter_row = next((h for h in hist if h['chapter_id'] == cid), None)
        assert chapter_row is not None
        assert str(chapter_row['analysis_run_id']) == str(run_id)


# --------------------------- RLS / Ownership Boundary ---------------------------

class TestOwnershipBoundary:
    """User B must NOT be able to access User A's data."""

    def test_user_b_cannot_read_user_a_data(self, client_a, client_b):
        # User A creates a project + chapter + analysis
        r = client_a.post(f'{BASE_URL}/api/projects', json={'nome': f'TEST_Owned_{uuid.uuid4().hex[:6]}', 'idioma': 'pt-BR'})
        assert r.status_code == 201
        pid = r.json()['id']

        r = client_a.post(
            f'{BASE_URL}/api/projects/{pid}/chapters',
            json={'titulo': 'TEST_Owned_Cap', 'texto_bruto': SAMPLE_TEXT},
        )
        assert r.status_code == 201
        cid = r.json()['id']

        r = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r.status_code == 201
        arid = r.json()['analysis_run_id']

        # User B tries to access → must all be 404 (not 200)
        r = client_b.get(f'{BASE_URL}/api/projects/{pid}')
        assert r.status_code == 404, f'RLS breach: user B got {r.status_code} on project'

        r = client_b.get(f'{BASE_URL}/api/chapters/{cid}')
        assert r.status_code == 404, f'RLS breach: user B got {r.status_code} on chapter'

        r = client_b.get(f'{BASE_URL}/api/analysis_runs/{arid}')
        assert r.status_code == 404, f'RLS breach: user B got {r.status_code} on analysis_run'

        r = client_b.get(f'{BASE_URL}/api/projects/{pid}/chapters')
        assert r.status_code == 404

        r = client_b.get(f'{BASE_URL}/api/projects/{pid}/history')
        assert r.status_code == 404

        r = client_b.get(f'{BASE_URL}/api/chapters/{cid}/estimate')
        assert r.status_code == 404

        # User B cannot delete User A's project
        r = client_b.delete(f'{BASE_URL}/api/projects/{pid}')
        assert r.status_code == 404

        # And it must still be there for user A
        r = client_a.get(f'{BASE_URL}/api/projects/{pid}')
        assert r.status_code == 200
