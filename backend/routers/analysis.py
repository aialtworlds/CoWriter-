import json
import math
from fastapi import APIRouter, Depends, HTTPException
from auth import current_user
from database import get_pool
from checks.helpers import count_words
from checks.runner import run_deterministic_checks
from checks.ai_checks import run_judgment_checks
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

    resultados_fatos = run_deterministic_checks(texto, idioma, custom_patterns_by_tipo)

    custom_hits_total = {}
    for r in resultados_fatos:
        for rule_id, count in r.get('custom_hits', {}).items():
            custom_hits_total[rule_id] = custom_hits_total.get(rule_id, 0) + count

    creditos_necessarios = math.ceil(palavras / WORDS_PER_CREDIT) if palavras else 0
    wallet = await pool.fetchrow("SELECT saldo_creditos FROM credit_wallet WHERE user_id=$1", user['sub'])
    saldo = float(wallet['saldo_creditos']) if wallet else 0
    saldo_suficiente = saldo >= creditos_necessarios and creditos_necessarios > 0

    resultados_julgamento = []
    creditos_consumidos = 0
    leitura_critica_status = 'sem_credito'
    if saldo_suficiente:
        resultados_julgamento = await run_judgment_checks(texto, idioma)
        creditos_consumidos = creditos_necessarios
        leitura_critica_status = 'ok'
    elif creditos_necessarios == 0:
        leitura_critica_status = 'sem_credito'

    resultados = resultados_fatos + resultados_julgamento

    async with pool.acquire() as conn:
        async with conn.transaction():
            run_row = await conn.fetchrow(
                "INSERT INTO analysis_runs (chapter_id, palavras_analisadas, creditos_consumidos, resultados_json) "
                "VALUES ($1, $2, $3, $4) RETURNING id, \"timestamp\", palavras_analisadas, creditos_consumidos",
                chapter_id, palavras, creditos_consumidos,
                json.dumps({'checks_fatos': resultados_fatos, 'checks_julgamento': resultados_julgamento}),
            )
            for r in resultados:
                extra_payload = {
                    'items': r['detalhes'],
                    'distribuicao': r.get('distribuicao'),
                    'summary': r.get('summary'),
                }
                await conn.execute(
                    "INSERT INTO check_results (analysis_run_id, check_type, numero, tipo, confiabilidade, score, contagem, detalhes_json) "
                    "VALUES ($1, $2, $3, $4, $5, $6, $7, $8)",
                    run_row['id'], r['check_type'], r['numero'], r['tipo'], r['confiabilidade'],
                    r['score'], r['contagem'], json.dumps(extra_payload),
                )
            for rule_id, count in custom_hits_total.items():
                await conn.execute(
                    "UPDATE banned_patterns SET disparos_count = disparos_count + $1 WHERE id=$2 AND user_id=$3",
                    count, rule_id, user['sub'],
                )
            if creditos_consumidos > 0:
                await conn.execute(
                    "UPDATE credit_wallet SET saldo_creditos = saldo_creditos - $1, atualizado_em = now() "
                    "WHERE user_id=$2",
                    creditos_consumidos, user['sub'],
                )
                await conn.execute(
                    "INSERT INTO credit_transactions (user_id, tipo, quantidade, referencia_id) "
                    "VALUES ($1, 'consumo', $2, $3)",
                    user['sub'], -creditos_consumidos, run_row['id'],
                )

    leitura_critica = {'status': leitura_critica_status, 'checks': resultados_julgamento}
    if leitura_critica_status == 'sem_credito':
        leitura_critica['mensagem'] = (
            'Saldo de créditos insuficiente para rodar a leitura crítica (IA). '
            'Os checks determinísticos (Fatos) rodaram normalmente e não consomem crédito.'
        )

    return {
        'analysis_run_id': str(run_row['id']),
        'timestamp': run_row['timestamp'],
        'palavras_analisadas': palavras,
        'creditos_consumidos': creditos_consumidos,
        'fatos': resultados_fatos,
        'leitura_critica': leitura_critica,
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
    julgamento = []
    for c in checks:
        item = dict(c)
        raw = json.loads(item.pop('detalhes_json'))
        if isinstance(raw, dict) and 'items' in raw:
            item['detalhes'] = raw.get('items') or []
            if raw.get('distribuicao') is not None:
                item['distribuicao'] = raw['distribuicao']
            if raw.get('summary'):
                item['summary'] = raw['summary']
        else:
            item['detalhes'] = raw or []
        if item['tipo'] == 'julgamento':
            julgamento.append(item)
        else:
            fatos.append(item)
    result = dict(run_row)
    result['fatos'] = fatos
    result['leitura_critica'] = {
        'status': 'ok' if julgamento else ('sem_credito' if run_row['creditos_consumidos'] == 0 else 'ok'),
        'checks': julgamento,
    }
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
