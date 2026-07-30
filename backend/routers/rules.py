from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from typing import Optional
from auth import current_user
from database import get_pool
from schemas import BannedPatternCreate, BannedPatternUpdate, BannedPatternImport

router = APIRouter()

TIPOS_VALIDOS = ['frase', 'gesto', 'descritor', 'estrutura']


@router.get('/banned_patterns')
async def list_banned_patterns(project_id: Optional[str] = Query(None), user=Depends(current_user)):
    pool = get_pool()
    if project_id:
        rows = await pool.fetch(
            "SELECT * FROM banned_patterns WHERE user_id=$1 AND (project_id=$2 OR project_id IS NULL) "
            "ORDER BY criado_em DESC",
            user['sub'], project_id,
        )
    else:
        rows = await pool.fetch(
            "SELECT * FROM banned_patterns WHERE user_id=$1 AND project_id IS NULL ORDER BY criado_em DESC",
            user['sub'],
        )
    return [dict(r) for r in rows]


@router.post('/banned_patterns', status_code=201)
async def create_banned_pattern(payload: BannedPatternCreate, user=Depends(current_user)):
    if payload.tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f'tipo deve ser um de {TIPOS_VALIDOS}')
    pool = get_pool()
    if payload.project_id:
        owner = await pool.fetchrow("SELECT id FROM projects WHERE id=$1 AND user_id=$2", payload.project_id, user['sub'])
        if not owner:
            raise HTTPException(404, 'Projeto não encontrado')
    row = await pool.fetchrow(
        "INSERT INTO banned_patterns (user_id, project_id, tipo, idioma, texto_padrao, cooldown_max, janela_capitulos) "
        "VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING *",
        user['sub'], payload.project_id, payload.tipo, payload.idioma, payload.texto_padrao,
        payload.cooldown_max, payload.janela_capitulos,
    )
    return dict(row)


@router.put('/banned_patterns/{pattern_id}')
async def update_banned_pattern(pattern_id: str, payload: BannedPatternUpdate, user=Depends(current_user)):
    pool = get_pool()
    existing = await pool.fetchrow("SELECT id FROM banned_patterns WHERE id=$1 AND user_id=$2", pattern_id, user['sub'])
    if not existing:
        raise HTTPException(404, 'Regra não encontrada')
    row = await pool.fetchrow(
        "UPDATE banned_patterns SET texto_padrao=COALESCE($1, texto_padrao), idioma=COALESCE($2, idioma), "
        "cooldown_max=COALESCE($3, cooldown_max) WHERE id=$4 RETURNING *",
        payload.texto_padrao, payload.idioma, payload.cooldown_max, pattern_id,
    )
    return dict(row)


@router.delete('/banned_patterns/{pattern_id}', status_code=204)
async def delete_banned_pattern(pattern_id: str, user=Depends(current_user)):
    pool = get_pool()
    result = await pool.execute("DELETE FROM banned_patterns WHERE id=$1 AND user_id=$2", pattern_id, user['sub'])
    if result == 'DELETE 0':
        raise HTTPException(404, 'Regra não encontrada')


@router.post('/banned_patterns/import', status_code=201)
async def import_banned_patterns(payload: BannedPatternImport, user=Depends(current_user)):
    if payload.tipo not in TIPOS_VALIDOS:
        raise HTTPException(400, f'tipo deve ser um de {TIPOS_VALIDOS}')
    pool = get_pool()
    if payload.project_id:
        owner = await pool.fetchrow("SELECT id FROM projects WHERE id=$1 AND user_id=$2", payload.project_id, user['sub'])
        if not owner:
            raise HTTPException(404, 'Projeto não encontrado')
    linhas = [l.strip() for l in payload.texto.splitlines() if l.strip()]
    inserted = []
    async with pool.acquire() as conn:
        async with conn.transaction():
            for linha in linhas:
                row = await conn.fetchrow(
                    "INSERT INTO banned_patterns (user_id, project_id, tipo, idioma, texto_padrao, cooldown_max) "
                    "VALUES ($1, $2, $3, $4, $5, $6) RETURNING *",
                    user['sub'], payload.project_id, payload.tipo, payload.idioma, linha, payload.cooldown_max,
                )
                inserted.append(dict(row))
    return inserted


@router.get('/banned_patterns/export', response_class=PlainTextResponse)
async def export_banned_patterns(
    tipo: Optional[str] = Query(None), project_id: Optional[str] = Query(None), user=Depends(current_user)
):
    pool = get_pool()
    conditions = ["user_id=$1"]
    params = [user['sub']]
    if project_id:
        conditions.append(f"(project_id=${len(params) + 1} OR project_id IS NULL)")
        params.append(project_id)
    else:
        conditions.append("project_id IS NULL")
    if tipo:
        conditions.append(f"tipo=${len(params) + 1}")
        params.append(tipo)
    query = f"SELECT texto_padrao FROM banned_patterns WHERE {' AND '.join(conditions)} ORDER BY criado_em"
    rows = await pool.fetch(query, *params)
    return '\n'.join(r['texto_padrao'] for r in rows)
