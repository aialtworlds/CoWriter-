import json
import math
from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from database import get_pool
from checks.helpers import count_words
from checks.runner import run_deterministic_checks
from routers.chapters import _assert_chapter_owner, _assert_project_owner

router = APIRouter()

WORDS_PER_CREDIT = 1000


@router.get('/chapters/{chapter_id}/estimate')
async def estimate_analysis(chapter_id: str, user=Depends(current_user)):
    pool = get_pool()
    chapter = await _assert_chapter_owner(pool, chapter_id, user['sub'])
    palavras = count_words(chapter['texto_bruto'])
    creditos_estimados = math.ceil(palavras / WORDS_PER_CREDIT) if palavras else 0
    wallet = await pool.fetchrow("SELECT saldo_creditos FROM credit_wallet WHERE user_id=$1", user['sub'])
    saldo = float(wallet['saldo_creditos']) if wallet else 0
    return {
        'palavras': palavras,
        'creditos_estimados_ia': creditos_estimados,
        'saldo_atual': saldo,
        'saldo_suficiente': saldo >= creditos_estimados,
    }


@router.post('/chapters/{chapter_id}/analyze', status_code=201)
async def analyze_chapter(chapter_id: str, user=Depends(current_user)):
    pool = get_pool()
    chapter = await _assert_chapter_owner(pool, chapter_id, user['sub'])
    texto = chapter['texto_bruto']
    idioma = chapter['idioma_detectado'] or chapter['project_idioma']
    palavras = count_words(texto)

    resultados = run_deterministic_checks(texto, idioma)

    async with pool.acquire() as conn:
        async with conn.transaction():
            run_row = await conn.fetchrow(
                "INSERT INTO analysis_runs (chapter_id, palavras_analisadas, creditos_consumidos, resultados_json) "
                "VALUES ($1, $2, 0, $3) RETURNING id, \"timestamp\", palavras_analisadas, creditos_consumidos",
                chapter_id, palavras, json.dumps({'checks_fatos': resultados}),
            )
            for r in resultados:
                await conn.execute(
                    "INSERT INTO check_results (analysis_run_id, check_type, numero, tipo, confiabilidade, score, contagem, detalhes_json) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                    run_row['id'], r['check_type'], r['numero'], r['tipo'], r['confiabilidade'],
                    r['score'], r['contagem'], json.dumps(r['detalhes']),
                )

    return {
        'analysis_run_id': str(run_row['id']),
        'timestamp': run_row['timestamp'],
        'palavras_analisadas': palavras,
        'creditos_consumidos': 0,
        'fatos': resultados,
        'leitura_critica': {'status': 'em_breve', 'mensagem': 'Checks de julgamento de IA chegam na próxima fase.'},
    }


@router.get('/analysis_runs/{analysis_run_id}')
async def get_analysis_run(analysis_run_id: str, user=Depends(current_user)):
    pool = get_pool()
    run_row = await pool.fetchrow(
        "SELECT a.id, a.chapter_id, a.\"timestamp\", a.palavras_analisadas, a.creditos_consumidos "
        "FROM analysis_runs a JOIN chapters c ON c.id = a.chapter_id JOIN projects p ON p.id = c.project_id "
        "WHERE a.id=$1 AND p.user_id=$2",
        analysis_run_id, user['sub'],
    )
    if not run_row:
        raise HTTPException(404, 'Análise não encontrada')
    checks = await pool.fetch(
        "SELECT check_type, numero, tipo, confiabilidade, score, contagem, detalhes_json FROM check_results "
        "WHERE analysis_run_id=$1 ORDER BY numero",
        analysis_run_id,
    )
    fatos = []
    for c in checks:
        item = dict(c)
        item['detalhes'] = json.loads(item.pop('detalhes_json'))
        fatos.append(item)
    result = dict(run_row)
    result['fatos'] = fatos
    return result


@router.get('/projects/{project_id}/history')
async def project_history(project_id: str, user=Depends(current_user)):
    pool = get_pool()
    await _assert_project_owner(pool, project_id, user['sub'])
    rows = await pool.fetch(
        "SELECT c.id as chapter_id, c.titulo, a.id as analysis_run_id, a.\"timestamp\", "
        "a.palavras_analisadas, a.creditos_consumidos "
        "FROM chapters c LEFT JOIN LATERAL ("
        "  SELECT * FROM analysis_runs ar WHERE ar.chapter_id = c.id ORDER BY ar.\"timestamp\" DESC LIMIT 1"
        ") a ON true "
        "WHERE c.project_id=$1 ORDER BY c.criado_em DESC",
        project_id,
    )
    return [dict(r) for r in rows]
