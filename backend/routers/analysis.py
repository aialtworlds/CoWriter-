import json
import math
from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from database import get_pool
from checks.helpers import count_words
from checks.runner import run_deterministic_checks
from ai.judgment_checks import run_judgment_checks
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

    pattern_rows = await pool.fetch(
        "SELECT id, tipo, texto_padrao, cooldown_max FROM banned_patterns "
        "WHERE user_id=$1 AND (project_id=$2 OR project_id IS NULL)",
        user['sub'], chapter['project_id'],
    )
    custom_patterns_by_tipo = {}
    for p in pattern_rows:
        custom_patterns_by_tipo.setdefault(p['tipo'], []).append(
            {'id': str(p['id']), 'texto_padrao': p['texto_padrao'], 'cooldown_max': p['cooldown_max']}
        )

    resultados = run_deterministic_checks(texto, idioma, custom_patterns_by_tipo)

    custom_hits_total = {}
    for r in resultados:
        for rule_id, count in r.get('custom_hits', {}).items():
            custom_hits_total[rule_id] = custom_hits_total.get(rule_id, 0) + count

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
            for rule_id, count in custom_hits_total.items():
                await conn.execute(
                    "UPDATE banned_patterns SET disparos_count = disparos_count + $1 WHERE id=$2 AND user_id=$3",
                    count, rule_id, user['sub'],
                )

    return {
        'analysis_run_id': str(run_row['id']),
        'timestamp': run_row['timestamp'],
        'palavras_analisadas': palavras,
        'creditos_consumidos': 0,
        'fatos': resultados,
        'leitura_critica': [],
        'leitura_critica_executada': False,
    }


async def _assert_analysis_run_owner(pool, analysis_run_id: str, user_id: str):
    run_row = await pool.fetchrow(
        "SELECT a.id, a.chapter_id, a.\"timestamp\", a.palavras_analisadas, a.creditos_consumidos, "
        "c.texto_bruto, c.idioma_detectado, p.idioma as project_idioma "
        "FROM analysis_runs a JOIN chapters c ON c.id = a.chapter_id JOIN projects p ON p.id = c.project_id "
        "WHERE a.id=$1 AND p.user_id=$2",
        analysis_run_id, user_id,
    )
    if not run_row:
        raise HTTPException(404, 'Análise não encontrada')
    return run_row


@router.post('/analysis_runs/{analysis_run_id}/critical_reading', status_code=201)
async def run_critical_reading(analysis_run_id: str, user=Depends(current_user)):
    pool = get_pool()
    run_row = await _assert_analysis_run_owner(pool, analysis_run_id, user['sub'])

    existing = await pool.fetch(
        "SELECT check_type, numero, tipo, confiabilidade, score, contagem, detalhes_json FROM check_results "
        "WHERE analysis_run_id=$1 AND tipo='julgamento' ORDER BY numero",
        analysis_run_id,
    )
    if existing:
        leitura_critica = []
        for c in existing:
            item = dict(c)
            item['detalhes'] = json.loads(item.pop('detalhes_json'))
            leitura_critica.append(item)
        return {
            'analysis_run_id': analysis_run_id,
            'creditos_consumidos': float(run_row['creditos_consumidos']),
            'leitura_critica': leitura_critica,
            'ja_executada': True,
        }

    palavras = run_row['palavras_analisadas']
    creditos_necessarios = math.ceil(palavras / WORDS_PER_CREDIT) if palavras else 0
    idioma = run_row['idioma_detectado'] or run_row['project_idioma']

    wallet = await pool.fetchrow("SELECT saldo_creditos FROM credit_wallet WHERE user_id=$1", user['sub'])
    saldo = float(wallet['saldo_creditos']) if wallet else 0
    if saldo < creditos_necessarios:
        raise HTTPException(402, {
            'erro': 'saldo_insuficiente',
            'necessario': creditos_necessarios,
            'saldo': saldo,
        })

    resultados = await run_judgment_checks(run_row['texto_bruto'], idioma)

    async with pool.acquire() as conn:
        async with conn.transaction():
            for r in resultados:
                await conn.execute(
                    "INSERT INTO check_results (analysis_run_id, check_type, numero, tipo, confiabilidade, score, contagem, detalhes_json) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                    analysis_run_id, r['check_type'], r['numero'], r['tipo'], r['confiabilidade'],
                    r['score'], r['contagem'], json.dumps(r['detalhes']),
                )
            await conn.execute(
                "UPDATE analysis_runs SET creditos_consumidos = creditos_consumidos + $1 WHERE id=$2",
                creditos_necessarios, analysis_run_id,
            )
            await conn.execute(
                "INSERT INTO credit_transactions (user_id, tipo, quantidade, referencia_id) VALUES ($1, 'consumo', $2, $3)",
                user['sub'], -creditos_necessarios, analysis_run_id,
            )
            await conn.execute(
                "UPDATE credit_wallet SET saldo_creditos = saldo_creditos - $1, atualizado_em = now() WHERE user_id=$2",
                creditos_necessarios, user['sub'],
            )

    return {
        'analysis_run_id': analysis_run_id,
        'creditos_consumidos': creditos_necessarios,
        'leitura_critica': resultados,
        'ja_executada': False,
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
    leitura_critica = []
    for c in checks:
        item = dict(c)
        item['detalhes'] = json.loads(item.pop('detalhes_json'))
        if item['tipo'] == 'julgamento':
            leitura_critica.append(item)
        else:
            fatos.append(item)
    result = dict(run_row)
    result['fatos'] = fatos
    result['leitura_critica'] = leitura_critica
    result['leitura_critica_executada'] = len(leitura_critica) > 0
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
