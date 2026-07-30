"""
Fase 4 pre-check: Anthropic wrapper client smoke test.

Verifies:
- GET /api/ai/ping requires auth (401 without Bearer token)
- GET /api/ai/ping with valid demo Bearer token returns 200 with:
    * model == 'claude-sonnet-5' (from ANTHROPIC_MODEL env)
    * resposta is a non-empty string containing 'OK' (real Anthropic call)
- Regression: /api/ (root) still 200, /api/wallet still 200 for demo user

This costs a tiny amount of real Anthropic API credit (~16 max_tokens).
"""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://cowriter-ai.preview.emergentagent.com').rstrip('/')
SUPABASE_URL = 'https://cexplgtcimdezzxuimkv.supabase.co'
SUPABASE_ANON = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNleHBsZ3RjaW1kZXp6eHVpbWt2Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODUzNjY1NDYsImV4cCI6MjEwMDk0MjU0Nn0.pxENcn8FEms5TXkwz-SYYOOCXLeKyAr8wtrG6358zXY'

USER = ('demo.escritor@cowriter.test', 'CoWriter#2026')


def _supa_login(email: str, password: str) -> str:
    r = requests.post(
        f'{SUPABASE_URL}/auth/v1/token?grant_type=password',
        headers={'apikey': SUPABASE_ANON, 'Content-Type': 'application/json'},
        json={'email': email, 'password': password},
        timeout=15,
    )
    r.raise_for_status()
    return r.json()['access_token']


@pytest.fixture(scope='module')
def token():
    try:
        return _supa_login(*USER)
    except Exception as e:
        pytest.skip(f'Demo user login failed: {e}')


@pytest.fixture()
def client(token):
    s = requests.Session()
    s.headers.update({'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'})
    return s


# ------------------- Regression sanity -------------------

def test_root_still_online():
    r = requests.get(f'{BASE_URL}/api/', timeout=10)
    assert r.status_code == 200
    assert r.json().get('message')


def test_wallet_still_works(client):
    r = client.get(f'{BASE_URL}/api/wallet', timeout=10)
    assert r.status_code == 200
    data = r.json()
    assert 'saldo_creditos' in data


# ------------------- /api/ai/ping tests -------------------

def test_ai_ping_requires_auth():
    r = requests.get(f'{BASE_URL}/api/ai/ping', timeout=10)
    assert r.status_code == 401, f'Expected 401 without token, got {r.status_code}: {r.text}'


def test_ai_ping_returns_real_claude_response(client):
    r = client.get(f'{BASE_URL}/api/ai/ping', timeout=60)
    assert r.status_code == 200, f'Expected 200, got {r.status_code}: {r.text}'
    data = r.json()

    # model must reflect env var, not hardcoded
    assert data.get('model') == 'claude-sonnet-5', f"model mismatch: got {data.get('model')}"

    # resposta must be a real, non-empty string containing 'OK'
    resposta = data.get('resposta')
    assert isinstance(resposta, str), f'resposta not a string: {type(resposta)}'
    assert len(resposta) > 0, 'resposta is empty'
    assert len(resposta) < 200, f'resposta suspiciously long ({len(resposta)} chars), expected trivial "OK": {resposta!r}'
    # Real Claude call for the prompt "Responda exatamente: OK" should contain OK
    assert re.search(r'\bOK\b', resposta, re.IGNORECASE), f"resposta does not contain 'OK': {resposta!r}"


# ------------------- Wrapper file sanity (no hardcoded key/model) -------------------

def test_claude_client_reads_from_env():
    """Static inspection: /app/backend/ai/claude_client.py must not hardcode key or model."""
    path = '/app/backend/ai/claude_client.py'
    with open(path, 'r', encoding='utf-8') as f:
        src = f.read()
    # must reference env vars
    assert "os.environ['ANTHROPIC_API_KEY']" in src or 'os.environ.get(\'ANTHROPIC_API_KEY\'' in src, \
        'ANTHROPIC_API_KEY env read not found in claude_client.py'
    assert 'ANTHROPIC_MODEL' in src, 'ANTHROPIC_MODEL env read not found in claude_client.py'
    # must not hardcode any sk-ant- key
    assert 'sk-ant-' not in src, 'Hardcoded Anthropic API key found in claude_client.py'
