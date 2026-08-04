"""
Fase 6 Stripe Payments tests:
- GET /api/payments/packages
- POST /api/payments/checkout (valid + invalid pacote)
- GET /api/payments/status/{session_id}
- POST /api/stripe/webhook (invalid signature)
- Cross-user security on payments/status
"""
import os
import time
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')

USER_A_EMAIL = "demo.escritor@cowriter.test"
USER_A_PASSWORD = "CoWriter#2026"

# second test user for cross-user security test
USER_B_EMAIL = "TEST_userb.cowriter@example.com"
USER_B_PASSWORD = "TestUserB#2026"


def get_supabase_token(email, password):
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
        headers={"apikey": SUPABASE_ANON_KEY, "Content-Type": "application/json"},
        json={"email": email, "password": password},
    )
    if resp.status_code != 200:
        return None
    return resp.json().get("access_token")


def create_supabase_user(email, password):
    """Create user via Supabase admin API using service_role key, with email_confirm=true."""
    service_key = os.environ.get('SUPABASE_SERVICE_ROLE_KEY')
    resp = requests.post(
        f"{SUPABASE_URL}/auth/v1/admin/users",
        headers={
            "apikey": service_key,
            "Authorization": f"Bearer {service_key}",
            "Content-Type": "application/json",
        },
        json={"email": email, "password": password, "email_confirm": True},
    )
    return resp


@pytest.fixture(scope="module")
def token_a():
    tok = get_supabase_token(USER_A_EMAIL, USER_A_PASSWORD)
    if not tok:
        pytest.skip("Could not authenticate user A")
    return tok


@pytest.fixture(scope="module")
def token_b():
    tok = get_supabase_token(USER_B_EMAIL, USER_B_PASSWORD)
    if not tok:
        create_resp = create_supabase_user(USER_B_EMAIL, USER_B_PASSWORD)
        if create_resp.status_code not in (200, 201):
            pytest.skip(f"Could not create user B: {create_resp.status_code} {create_resp.text}")
        time.sleep(1)
        tok = get_supabase_token(USER_B_EMAIL, USER_B_PASSWORD)
    if not tok:
        pytest.skip("Could not authenticate user B after creation")
    return tok


@pytest.fixture
def client_a(token_a):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token_a}", "Content-Type": "application/json"})
    return s


@pytest.fixture
def client_b(token_b):
    s = requests.Session()
    s.headers.update({"Authorization": f"Bearer {token_b}", "Content-Type": "application/json"})
    return s


class TestPackagesEndpoint:
    def test_packages_requires_auth(self):
        resp = requests.get(f"{BASE_URL}/api/payments/packages")
        assert resp.status_code in (401, 403)

    def test_packages_returns_3_fixed_packages(self, client_a):
        resp = client_a.get(f"{BASE_URL}/api/payments/packages")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) == 3
        by_pacote = {p['pacote']: p for p in data}
        assert set(by_pacote.keys()) == {'conto', 'romance_medio', 'romance_longo'}
        assert by_pacote['conto']['creditos'] == 40
        assert by_pacote['conto']['valor'] == 29.90
        assert by_pacote['romance_medio']['creditos'] == 80
        assert by_pacote['romance_medio']['valor'] == 49.90
        assert by_pacote['romance_longo']['creditos'] == 150
        assert by_pacote['romance_longo']['valor'] == 79.90


class TestCheckoutEndpoint:
    def test_checkout_valid_pacote_creates_session(self, client_a):
        resp = client_a.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"pacote": "conto", "origin_url": "https://example.com"},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert "checkout_url" in data
        assert "session_id" in data
        assert data["checkout_url"].startswith("https://checkout.stripe.com")
        assert data["session_id"].startswith("cs_")

        # verify payments row inserted with status=pending via status endpoint
        status_resp = client_a.get(f"{BASE_URL}/api/payments/status/{data['session_id']}")
        assert status_resp.status_code == 200
        status_data = status_resp.json()
        assert status_data["status"] == "pending"
        assert status_data["pacote"] == "conto"
        assert status_data["creditos_concedidos"] == 40
        assert float(status_data["valor"]) == 29.90
        assert status_data["moeda"] == "BRL"

    def test_checkout_invalid_pacote_returns_400(self, client_a):
        resp = client_a.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"pacote": "nonexistent", "origin_url": "https://example.com"},
        )
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert "detail" in data

    def test_checkout_invalid_pacote_no_side_effects(self, client_a):
        """After invalid pacote request, packages list should still be unaffected (no crash)."""
        resp = client_a.get(f"{BASE_URL}/api/payments/packages")
        assert resp.status_code == 200
        assert len(resp.json()) == 3

    def test_checkout_requires_auth(self):
        resp = requests.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"pacote": "conto", "origin_url": "https://example.com"},
        )
        assert resp.status_code in (401, 403)


class TestStatusEndpoint:
    def test_status_nonexistent_session_404(self, client_a):
        resp = client_a.get(f"{BASE_URL}/api/payments/status/cs_test_nonexistent_session_xyz")
        assert resp.status_code == 404

    def test_cross_user_security(self, client_a, client_b):
        """User B's JWT must NOT be able to see user A's payment session."""
        create_resp = client_a.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"pacote": "romance_medio", "origin_url": "https://example.com"},
        )
        assert create_resp.status_code == 200
        session_id = create_resp.json()["session_id"]

        # user A can see it
        a_status = client_a.get(f"{BASE_URL}/api/payments/status/{session_id}")
        assert a_status.status_code == 200

        # user B must get 404, not user A's data
        b_status = client_b.get(f"{BASE_URL}/api/payments/status/{session_id}")
        assert b_status.status_code == 404, (
            f"Cross-user leak! User B got status {b_status.status_code}: {b_status.text}"
        )


class TestWebhookSecurity:
    def test_webhook_missing_signature_returns_400(self):
        resp = requests.post(
            f"{BASE_URL}/api/stripe/webhook",
            json={"type": "checkout.session.completed", "data": {"object": {"id": "cs_fake"}}},
        )
        assert resp.status_code == 400
        data = resp.json()
        assert "detail" in data
        assert "inv" in data["detail"].lower() or "assinatura" in data["detail"].lower()

    def test_webhook_invalid_signature_returns_400(self):
        resp = requests.post(
            f"{BASE_URL}/api/stripe/webhook",
            headers={"stripe-signature": "t=1,v1=invalidsignature12345"},
            json={"type": "checkout.session.completed", "data": {"object": {"id": "cs_fake"}}},
        )
        assert resp.status_code == 400

    def test_webhook_does_not_credit_on_invalid_sig(self, client_a):
        """Ensure a fake webhook call referencing a real pending session does not credit it."""
        create_resp = client_a.post(
            f"{BASE_URL}/api/payments/checkout",
            json={"pacote": "conto", "origin_url": "https://example.com"},
        )
        session_id = create_resp.json()["session_id"]

        requests.post(
            f"{BASE_URL}/api/stripe/webhook",
            headers={"stripe-signature": "t=1,v1=badsig"},
            json={
                "type": "checkout.session.completed",
                "data": {"object": {"id": session_id, "payment_status": "paid"}},
            },
        )
        status_resp = client_a.get(f"{BASE_URL}/api/payments/status/{session_id}")
        assert status_resp.json()["status"] == "pending"
