"""
CoWriter V1 - Fase 3 backend tests: Minhas Regras (banned_patterns)

Covers:
- Auth requirement (401 without token)
- CRUD: POST/GET/PUT/DELETE /api/banned_patterns
- Scope filtering: no project_id -> only global; with project_id -> project+global
- Import (multi-line) + Export (text/plain)
- Invalid tipo -> 400
- RLS: user B cannot see/update/delete user A's rules (404)
- Integration into analyze_chapter:
    * tipo='frase' -> ai_fingerprint check flags custom hit + increments disparos_count
    * tipo='gesto' with custom cooldown_max -> gesture_cooldown flags only excess + increments disparos_count
    * tipo='descritor' with custom cooldown_max -> descriptor_cooldown flags only excess
- Regression: when project has zero custom rules, existing 8 deterministic checks still run.
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cowriter-ai.preview.emergentagent.com').rstrip('/')
SUPABASE_URL = 'https://cexplgtcimdezzxuimkv.supabase.co'
SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNleHBsZ3RjaW1kZXp6eHVpbWt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY1NDYsImV4cCI6MjEwMDk0MjU0Nn0.pxENcn8FEms5TXkwz-SYYOOCXLeKyAr8wtrG6358zXY'

USER_A = ('demo.escritor@cowriter.test', 'CoWriter#2026')
USER_B = ('demo.escritor2@cowriter.test', 'CoWriter#2026')


def _supa_login(email, password):
    r = requests.post(
        f'{SUPABASE_URL}/auth/v1/token?grant_type=password',
        headers={'apikey': SUPABASE_ANON, 'Content-Type': 'application/json'},
        json={'email': email, 'password': password},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()['access_token']


@pytest.fixture(scope='module')
def token_a():
    try:
        return _supa_login(*USER_A)
    except Exception as e:
        pytest.skip(f'User A login failed: {e}')


@pytest.fixture(scope='module')
def token_b():
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


@pytest.fixture()
def project_a(client_a):
    r = client_a.post(f'{BASE_URL}/api/projects', json={'nome': f'TEST_Rules_{uuid.uuid4().hex[:6]}', 'idioma': 'pt-BR'})
    assert r.status_code == 201, r.text
    return r.json()['id']


# --------------------------- Auth ---------------------------

class TestBannedPatternsAuth:
    @pytest.mark.parametrize('method,path', [
        ('GET', '/api/banned_patterns'),
        ('POST', '/api/banned_patterns'),
        ('GET', '/api/banned_patterns/export'),
        ('POST', '/api/banned_patterns/import'),
    ])
    def test_auth_required(self, method, path):
        r = requests.request(method, f'{BASE_URL}{path}', json={} if method == 'POST' else None)
        assert r.status_code == 401


# --------------------------- CRUD ---------------------------

class TestBannedPatternsCRUD:
    def test_create_global_frase_defaults(self, client_a):
        payload = {'tipo': 'frase', 'texto_padrao': f'TEST_frase_{uuid.uuid4().hex[:6]}'}
        r = client_a.post(f'{BASE_URL}/api/banned_patterns', json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data['tipo'] == 'frase'
        assert data['texto_padrao'] == payload['texto_padrao']
        assert data['project_id'] is None
        assert data['disparos_count'] == 0
        # cleanup
        client_a.delete(f"{BASE_URL}/api/banned_patterns/{data['id']}")

    def test_create_project_scoped_gesto(self, client_a, project_a):
        payload = {'tipo': 'gesto', 'texto_padrao': f'TEST_gesto_{uuid.uuid4().hex[:6]}',
                   'project_id': project_a, 'cooldown_max': 3}
        r = client_a.post(f'{BASE_URL}/api/banned_patterns', json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert data['project_id'] == project_a
        assert data['cooldown_max'] == 3
        client_a.delete(f"{BASE_URL}/api/banned_patterns/{data['id']}")

    def test_invalid_tipo_400(self, client_a):
        r = client_a.post(f'{BASE_URL}/api/banned_patterns', json={'tipo': 'invalid', 'texto_padrao': 'x'})
        assert r.status_code == 400

    def test_list_global_only_when_no_project_id(self, client_a):
        # Create one global + one project-scoped
        r_project = client_a.post(f'{BASE_URL}/api/projects', json={'nome': f'TEST_scope_{uuid.uuid4().hex[:6]}', 'idioma': 'pt-BR'})
        pid = r_project.json()['id']
        r_glob = client_a.post(f'{BASE_URL}/api/banned_patterns',
                               json={'tipo': 'frase', 'texto_padrao': f'TEST_G_{uuid.uuid4().hex[:6]}'})
        r_proj = client_a.post(f'{BASE_URL}/api/banned_patterns',
                               json={'tipo': 'frase', 'texto_padrao': f'TEST_P_{uuid.uuid4().hex[:6]}', 'project_id': pid})
        gid = r_glob.json()['id']
        pid_rule = r_proj.json()['id']

        # No project_id → only globals
        r = client_a.get(f'{BASE_URL}/api/banned_patterns')
        assert r.status_code == 200
        ids_no_scope = [x['id'] for x in r.json()]
        assert gid in ids_no_scope
        assert pid_rule not in ids_no_scope, 'project-scoped rule leaked into global list'

        # With project_id → both globals + project's rules
        r = client_a.get(f'{BASE_URL}/api/banned_patterns', params={'project_id': pid})
        assert r.status_code == 200
        ids_scoped = [x['id'] for x in r.json()]
        assert gid in ids_scoped
        assert pid_rule in ids_scoped

        # cleanup
        client_a.delete(f"{BASE_URL}/api/banned_patterns/{gid}")
        client_a.delete(f"{BASE_URL}/api/banned_patterns/{pid_rule}")
        client_a.delete(f'{BASE_URL}/api/projects/{pid}')

    def test_update_rule(self, client_a):
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'descritor', 'texto_padrao': 'TEST_D_orig', 'cooldown_max': 1})
        rid = r.json()['id']
        r = client_a.put(f'{BASE_URL}/api/banned_patterns/{rid}',
                         json={'texto_padrao': 'TEST_D_updated', 'cooldown_max': 5})
        assert r.status_code == 200
        assert r.json()['texto_padrao'] == 'TEST_D_updated'
        assert r.json()['cooldown_max'] == 5
        # GET verifies persistence
        r_list = client_a.get(f'{BASE_URL}/api/banned_patterns')
        got = next(x for x in r_list.json() if x['id'] == rid)
        assert got['texto_padrao'] == 'TEST_D_updated'
        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')

    def test_delete_rule_and_404_on_second_delete(self, client_a):
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'frase', 'texto_padrao': f'TEST_del_{uuid.uuid4().hex[:6]}'})
        rid = r.json()['id']
        d = client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        assert d.status_code == 204
        d2 = client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        assert d2.status_code == 404


# --------------------------- Import / Export ---------------------------

class TestImportExport:
    def test_import_multi_line(self, client_a):
        payload = {
            'tipo': 'frase',
            'texto': 'TEST_imp_um\nTEST_imp_dois\n\nTEST_imp_tres',
        }
        r = client_a.post(f'{BASE_URL}/api/banned_patterns/import', json=payload)
        assert r.status_code == 201, r.text
        data = r.json()
        assert len(data) == 3, f'expected 3 rules (blank line skipped), got {len(data)}'
        textos = [d['texto_padrao'] for d in data]
        assert 'TEST_imp_um' in textos
        assert 'TEST_imp_dois' in textos
        assert 'TEST_imp_tres' in textos
        # cleanup
        for d in data:
            client_a.delete(f"{BASE_URL}/api/banned_patterns/{d['id']}")

    def test_import_invalid_tipo(self, client_a):
        r = client_a.post(f'{BASE_URL}/api/banned_patterns/import',
                          json={'tipo': 'foo', 'texto': 'a\nb'})
        assert r.status_code == 400

    def test_export_returns_plain_text(self, client_a):
        # seed one rule
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'frase', 'texto_padrao': 'TEST_exp_unique_marker_xyz'})
        rid = r.json()['id']
        r = client_a.get(f'{BASE_URL}/api/banned_patterns/export')
        assert r.status_code == 200
        ct = r.headers.get('content-type', '')
        assert 'text/plain' in ct, f'expected text/plain, got {ct}'
        assert 'TEST_exp_unique_marker_xyz' in r.text
        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')


# --------------------------- RLS / Ownership ---------------------------

class TestRLS:
    def test_user_b_cannot_touch_user_a_rule(self, client_a, client_b):
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'frase', 'texto_padrao': f'TEST_rls_{uuid.uuid4().hex[:6]}'})
        rid = r.json()['id']
        # B lists → should not include A's rule
        list_b = client_b.get(f'{BASE_URL}/api/banned_patterns').json()
        assert not any(x['id'] == rid for x in list_b), 'RLS breach: user B sees user A rule'
        # B update → 404
        r_upd = client_b.put(f'{BASE_URL}/api/banned_patterns/{rid}',
                             json={'texto_padrao': 'hacked'})
        assert r_upd.status_code == 404
        # B delete → 404
        r_del = client_b.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        assert r_del.status_code == 404
        # Rule still exists for A
        assert any(x['id'] == rid for x in client_a.get(f'{BASE_URL}/api/banned_patterns').json())
        # cleanup
        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')


# --------------------------- Integration with analyze_chapter ---------------------------

class TestAnalyzeIntegration:
    def _create_project_and_chapter(self, client, texto, project_nome=None, chapter_titulo=None):
        r = client.post(f'{BASE_URL}/api/projects',
                        json={'nome': project_nome or f'TEST_int_{uuid.uuid4().hex[:6]}', 'idioma': 'pt-BR'})
        pid = r.json()['id']
        r = client.post(f'{BASE_URL}/api/projects/{pid}/chapters',
                        json={'titulo': chapter_titulo or 'TEST_cap', 'texto_bruto': texto})
        cid = r.json()['id']
        return pid, cid

    def test_frase_rule_flags_ai_fingerprint_and_increments(self, client_a):
        # global frase rule
        pattern = f'TESTMARKER_{uuid.uuid4().hex[:6]}_coracao'
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'frase', 'texto_padrao': pattern})
        rid = r.json()['id']
        assert r.json()['disparos_count'] == 0

        texto = f'Um começo neutro. {pattern}. Um meio neutro. {pattern}. Um fim.'
        pid, cid = self._create_project_and_chapter(client_a, texto)

        r_an = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r_an.status_code == 201, r_an.text
        fatos = r_an.json()['fatos']
        ai_fp = next(f for f in fatos if f['check_type'] == 'ai_fingerprint')
        # Expect at least the 2 occurrences of our pattern to be flagged
        detalhes = ai_fp['detalhes']
        matched = [d for d in detalhes if pattern.lower() in d['trecho'].lower()
                   or 'Regra personalizada' in d.get('sugestao', '')]
        assert len(matched) >= 2, f'expected >=2 custom hits in ai_fingerprint, got {len(matched)}: {detalhes}'
        # any suggestion should mention Regra personalizada
        assert any('Regra personalizada' in d.get('sugestao', '') for d in detalhes)

        # rule.disparos_count should have incremented by 2
        rules = client_a.get(f'{BASE_URL}/api/banned_patterns').json()
        r_now = next(x for x in rules if x['id'] == rid)
        assert r_now['disparos_count'] == 2, f'expected 2, got {r_now["disparos_count"]}'

        # cleanup
        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        client_a.delete(f'{BASE_URL}/api/projects/{pid}')

    def test_gesto_rule_flags_only_excess_over_cooldown(self, client_a):
        pattern = f'TESTMARKER_{uuid.uuid4().hex[:6]}_punhos'
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'gesto', 'texto_padrao': pattern, 'cooldown_max': 2})
        rid = r.json()['id']

        # 3 occurrences → cooldown=2 → 1 excess should be flagged
        texto = f'Ele {pattern}. Depois ela {pattern}. Finalmente ele {pattern} de novo.'
        pid, cid = self._create_project_and_chapter(client_a, texto)

        r_an = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r_an.status_code == 201, r_an.text
        fatos = r_an.json()['fatos']
        gc = next(f for f in fatos if f['check_type'] == 'gesture_cooldown')
        custom_related = [d for d in gc['detalhes']
                          if pattern.lower() in d.get('trecho', '').lower()
                          or 'personalizado' in d.get('sugestao', '').lower()]
        assert len(custom_related) == 1, f'expected exactly 1 excess for gesto (3 - cooldown 2), got {len(custom_related)}: {gc["detalhes"]}'

        rules = client_a.get(f'{BASE_URL}/api/banned_patterns').json()
        r_now = next(x for x in rules if x['id'] == rid)
        assert r_now['disparos_count'] == 1

        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        client_a.delete(f'{BASE_URL}/api/projects/{pid}')

    def test_descritor_rule_flags_only_excess(self, client_a):
        pattern = f'TESTMARKER_{uuid.uuid4().hex[:6]}_azulados'
        r = client_a.post(f'{BASE_URL}/api/banned_patterns',
                          json={'tipo': 'descritor', 'texto_padrao': pattern, 'cooldown_max': 1})
        rid = r.json()['id']

        # 3 occurrences, cooldown=1 → 2 excess flagged
        texto = f'Olhos {pattern}. Depois {pattern}. E de novo {pattern}.'
        pid, cid = self._create_project_and_chapter(client_a, texto)

        r_an = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r_an.status_code == 201, r_an.text
        fatos = r_an.json()['fatos']
        dc = next(f for f in fatos if f['check_type'] == 'descriptor_cooldown')
        custom_related = [d for d in dc['detalhes']
                          if pattern.lower() in d.get('trecho', '').lower()
                          or 'personalizado' in d.get('sugestao', '').lower()]
        assert len(custom_related) == 2, f'expected 2 excess, got {len(custom_related)}'

        rules = client_a.get(f'{BASE_URL}/api/banned_patterns').json()
        r_now = next(x for x in rules if x['id'] == rid)
        assert r_now['disparos_count'] == 2

        client_a.delete(f'{BASE_URL}/api/banned_patterns/{rid}')
        client_a.delete(f'{BASE_URL}/api/projects/{pid}')

    def test_regression_no_custom_rules_still_returns_8_checks(self, client_a):
        # Create ISOLATED project with no custom rules for it, and no relevant globals
        texto = ('Ela sorriu. Ele sorriu. Ela sorriu de novo, sorriu mais uma vez, e sorriu outra vez. '
                 'Ela viu que ele estava triste. Ela sentiu que algo mudara.')
        pid, cid = self._create_project_and_chapter(client_a, texto)
        r_an = client_a.post(f'{BASE_URL}/api/chapters/{cid}/analyze')
        assert r_an.status_code == 201, r_an.text
        fatos = r_an.json()['fatos']
        types = {f['check_type'] for f in fatos}
        expected = {
            'ai_fingerprint', 'gesture_cooldown', 'descriptor_cooldown', 'prose_rhythm',
            'sensory_rotation', 'filter_words', 'dialogue_tag_variety', 'paragraph_opening_monotony',
        }
        assert expected.issubset(types)
        # credits still 0
        assert r_an.json()['creditos_consumidos'] == 0

        client_a.delete(f'{BASE_URL}/api/projects/{pid}')
