import os
import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from auth import current_user
from database import get_pool
from schemas import PaymentCheckoutCreate

router = APIRouter()

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_emergent'
STRIPE_WEBHOOK_SECRET = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

PACOTES = {
    'conto': {'nome': 'Conto/novela curta', 'creditos': 40, 'valor': 29.90},
    'romance_medio': {'nome': 'Romance médio', 'creditos': 80, 'valor': 49.90},
    'romance_longo': {'nome': 'Romance longo', 'creditos': 150, 'valor': 79.90},
}


@router.get('/payments/packages')
async def list_packages(user=Depends(current_user)):
    return [{'pacote': k, **v} for k, v in PACOTES.items()]


@router.post('/payments/checkout')
async def create_checkout(payload: PaymentCheckoutCreate, user=Depends(current_user)):
    pacote_info = PACOTES.get(payload.pacote)
    if not pacote_info:
        raise HTTPException(400, 'Pacote inválido')

    session = stripe.checkout.Session.create(
        mode='payment',
        line_items=[{
            'price_data': {
                'currency': 'brl',
                'product_data': {
                    'name': f"CoWriter — {pacote_info['nome']} ({pacote_info['creditos']} créditos)",
                },
                'unit_amount': int(round(pacote_info['valor'] * 100)),
            },
            'quantity': 1,
        }],
        success_url=f"{payload.origin_url}/pagamento/sucesso?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{payload.origin_url}/pagamento/cancelado",
        metadata={'user_id': user['sub'], 'pacote': payload.pacote},
    )

    pool = get_pool()
    await pool.execute(
        "INSERT INTO payments (user_id, provider, external_id, moeda, valor, pacote, creditos_concedidos, status) "
        "VALUES ($1, 'stripe', $2, 'BRL', $3, $4, $5, 'pending')",
        user['sub'], session.id, pacote_info['valor'], payload.pacote, pacote_info['creditos'],
    )

    return {'checkout_url': session.url, 'session_id': session.id}


@router.get('/payments/status/{session_id}')
async def get_payment_status(session_id: str, user=Depends(current_user)):
    pool = get_pool()
    row = await pool.fetchrow(
        "SELECT status, pacote, creditos_concedidos, valor, moeda FROM payments WHERE external_id=$1 AND user_id=$2",
        session_id, user['sub'],
    )
    if not row:
        raise HTTPException(404, 'Pagamento não encontrado')

    if row['status'] != 'paid':
        try:
            session = stripe.checkout.Session.retrieve(session_id)
            if session.payment_status == 'paid' or session.status == 'complete':
                await _credit_payment(pool, session_id)
                row = await pool.fetchrow(
                    "SELECT status, pacote, creditos_concedidos, valor, moeda FROM payments WHERE external_id=$1",
                    session_id,
                )
        except stripe.error.StripeError:
            pass

    return dict(row)


@router.post('/stripe/webhook')
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get('stripe-signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig, STRIPE_WEBHOOK_SECRET)
    except (stripe.error.SignatureVerificationError, ValueError):
        raise HTTPException(400, 'Assinatura inválida')

    obj = event['data']['object']
    event_type = event['type']
    if event_type == 'checkout.session.completed' or (
        event_type == 'checkout.session.async_payment_succeeded' and obj.get('payment_status') == 'paid'
    ):
        await _credit_payment(get_pool(), obj['id'])

    return {'status': 'ok'}


async def _credit_payment(pool, session_id: str):
    async with pool.acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "UPDATE payments SET status='paid' WHERE external_id=$1 AND provider='stripe' AND status != 'paid' "
                "RETURNING id, user_id, creditos_concedidos",
                session_id,
            )
            if row:
                await conn.execute(
                    "INSERT INTO credit_transactions (user_id, tipo, quantidade, referencia_id) "
                    "VALUES ($1, 'compra_pacote', $2, $3)",
                    row['user_id'], row['creditos_concedidos'], row['id'],
                )
                await conn.execute(
                    "UPDATE credit_wallet SET saldo_creditos = saldo_creditos + $1, atualizado_em = now() "
                    "WHERE user_id=$2",
                    row['creditos_concedidos'], row['user_id'],
                )
