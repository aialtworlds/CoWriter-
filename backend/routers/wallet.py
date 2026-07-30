from fastapi import APIRouter, Depends
from auth import current_user
from database import get_pool

router = APIRouter()


@router.get('/wallet')
async def get_wallet(user=Depends(current_user)):
    pool = get_pool()
    row = await pool.fetchrow("SELECT saldo_creditos, atualizado_em FROM credit_wallet WHERE user_id=$1", user['sub'])
    if not row:
        return {'saldo_creditos': 0, 'atualizado_em': None}
    return dict(row)


@router.get('/wallet/transactions')
async def list_transactions(user=Depends(current_user)):
    pool = get_pool()
    rows = await pool.fetch(
        "SELECT id, tipo, quantidade, referencia_id, criado_em FROM credit_transactions "
        "WHERE user_id=$1 ORDER BY criado_em DESC",
        user['sub'],
    )
    return [dict(r) for r in rows]
