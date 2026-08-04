import io
import json

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from auth import current_user
from database import get_pool

router = APIRouter()

CHECK_NAMES = {
    'pt-BR': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Cooldown de Gestos',
        'descriptor_cooldown': 'Cooldown de Descritores', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Objetivo de Cena', 'scene_magnetism': 'Magnetismo de Cena',
        'linger_cortar': 'Linger/Cortar', 'subtext_frame': 'Subtexto em Diálogo',
        'voiceprint_pov_filter': 'Voiceprint / Filtro de POV',
    },
    'pt-PT': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Cooldown de Gestos',
        'descriptor_cooldown': 'Cooldown de Descritores', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Objetivo de Cena', 'scene_magnetism': 'Magnetismo de Cena',
        'linger_cortar': 'Linger/Cortar', 'subtext_frame': 'Subtexto no Diálogo',
        'voiceprint_pov_filter': 'Voiceprint / Filtro de POV',
    },
    'en': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Gesture Cooldown',
        'descriptor_cooldown': 'Descriptor Cooldown', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Scene Objective', 'scene_magnetism': 'Scene Magnetism',
        'linger_cortar': 'Linger/Cut Check', 'subtext_frame': 'Subtext Frame',
        'voiceprint_pov_filter': 'Voiceprint / POV Filter',
    },
    'es': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Cooldown de Gestos',
        'descriptor_cooldown': 'Cooldown de Descriptores', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Objetivo de Escena', 'scene_magnetism': 'Magnetismo de Escena',
        'linger_cortar': 'Demora/Corte', 'subtext_frame': 'Subtexto en Diálogo',
        'voiceprint_pov_filter': 'Huella de Voz / Filtro POV',
    },
    'it': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Cooldown dei Gesti',
        'descriptor_cooldown': 'Cooldown dei Descrittori', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Obiettivo di Scena', 'scene_magnetism': 'Magnetismo di Scena',
        'linger_cortar': 'Indugio/Taglio', 'subtext_frame': 'Sottotesto nel Dialogo',
        'voiceprint_pov_filter': 'Impronta Vocale / Filtro POV',
    },
    'fr': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Cooldown des Gestes',
        'descriptor_cooldown': 'Cooldown des Descripteurs', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Objectif de Scène', 'scene_magnetism': 'Magnétisme de Scène',
        'linger_cortar': 'Prolonger/Couper', 'subtext_frame': 'Sous-texte du Dialogue',
        'voiceprint_pov_filter': 'Empreinte Vocale / Filtre POV',
    },
    'de': {
        'ai_fingerprint': 'AI Fingerprint Scan', 'gesture_cooldown': 'Gesten-Cooldown',
        'descriptor_cooldown': 'Deskriptor-Cooldown', 'prose_rhythm': 'Prose Rhythm',
        'sensory_rotation': 'Sensory Rotation', 'filter_words': 'Filter Words',
        'dialogue_tag_variety': 'Dialogue Tag Variety', 'paragraph_opening_monotony': 'Paragraph-Opening Monotony',
        'scene_objective': 'Szenenziel', 'scene_magnetism': 'Szenenmagnetismus',
        'linger_cortar': 'Verweilen/Schnitt', 'subtext_frame': 'Subtext im Dialog',
        'voiceprint_pov_filter': 'Stimmabdruck / POV-Filter',
    },
}

LABELS = {
    'pt-BR': {
        'title': 'Relatório de Análise — CoWriter', 'chapter': 'Capítulo', 'project': 'Projeto',
        'date': 'Data', 'words': 'Palavras analisadas', 'credits': 'Créditos consumidos',
        'facts': 'Fatos (determinístico)', 'critical': 'Leitura Crítica (IA)',
        'no_issues': 'Nenhum problema encontrado.', 'occurrences': 'ocorrência(s)',
        'summary': 'Resumo', 'disclaimer': 'Isto é uma leitura possível, não um veredito.',
        'no_ai_results': 'Nenhum resultado de leitura crítica disponível nesta análise.',
    },
    'pt-PT': {
        'title': 'Relatório de Análise — CoWriter', 'chapter': 'Capítulo', 'project': 'Projeto',
        'date': 'Data', 'words': 'Palavras analisadas', 'credits': 'Créditos consumidos',
        'facts': 'Factos (determinístico)', 'critical': 'Leitura Crítica (IA)',
        'no_issues': 'Nenhum problema encontrado.', 'occurrences': 'ocorrência(s)',
        'summary': 'Resumo', 'disclaimer': 'Isto é uma leitura possível, não um veredito.',
        'no_ai_results': 'Nenhum resultado de leitura crítica disponível nesta análise.',
    },
    'en': {
        'title': 'Analysis Report — CoWriter', 'chapter': 'Chapter', 'project': 'Project',
        'date': 'Date', 'words': 'Words analyzed', 'credits': 'Credits used',
        'facts': 'Facts (deterministic)', 'critical': 'Critical Reading (AI)',
        'no_issues': 'No issues found.', 'occurrences': 'occurrence(s)',
        'summary': 'Summary', 'disclaimer': 'This is a possible reading, not a verdict.',
        'no_ai_results': 'No critical reading results available for this analysis.',
    },
    'es': {
        'title': 'Informe de Análisis — CoWriter', 'chapter': 'Capítulo', 'project': 'Proyecto',
        'date': 'Fecha', 'words': 'Palabras analizadas', 'credits': 'Créditos consumidos',
        'facts': 'Hechos (determinístico)', 'critical': 'Lectura Crítica (IA)',
        'no_issues': 'No se encontraron problemas.', 'occurrences': 'ocurrencia(s)',
        'summary': 'Resumen', 'disclaimer': 'Esto es una lectura posible, no un veredicto.',
        'no_ai_results': 'No hay resultados de lectura crítica disponibles para este análisis.',
    },
    'it': {
        'title': 'Report di Analisi — CoWriter', 'chapter': 'Capitolo', 'project': 'Progetto',
        'date': 'Data', 'words': 'Parole analizzate', 'credits': 'Crediti consumati',
        'facts': 'Fatti (deterministico)', 'critical': 'Lettura Critica (IA)',
        'no_issues': 'Nessun problema riscontrato.', 'occurrences': 'occorrenza(e)',
        'summary': 'Riepilogo', 'disclaimer': 'Questa è una lettura possibile, non un verdetto.',
        'no_ai_results': 'Nessun risultato di lettura critica disponibile per questa analisi.',
    },
    'fr': {
        'title': "Rapport d'Analyse — CoWriter", 'chapter': 'Chapitre', 'project': 'Projet',
        'date': 'Date', 'words': 'Mots analysés', 'credits': 'Crédits consommés',
        'facts': 'Faits (déterministe)', 'critical': 'Lecture Critique (IA)',
        'no_issues': 'Aucun problème détecté.', 'occurrences': 'occurrence(s)',
        'summary': 'Résumé', 'disclaimer': "Ceci est une lecture possible, pas un verdict.",
        'no_ai_results': 'Aucun résultat de lecture critique disponible pour cette analyse.',
    },
    'de': {
        'title': 'Analysebericht — CoWriter', 'chapter': 'Kapitel', 'project': 'Projekt',
        'date': 'Datum', 'words': 'Analysierte Wörter', 'credits': 'Verbrauchte Credits',
        'facts': 'Fakten (deterministisch)', 'critical': 'Kritische Lektüre (KI)',
        'no_issues': 'Keine Probleme gefunden.', 'occurrences': 'Vorkommen',
        'summary': 'Zusammenfassung', 'disclaimer': 'Dies ist eine mögliche Lesart, kein Urteil.',
        'no_ai_results': 'Für diese Analyse sind keine Ergebnisse der kritischen Lektüre verfügbar.',
    },
}


def _lang_key(lang: str) -> str:
    return lang if lang in CHECK_NAMES else 'pt-BR'


async def _load_report_data(pool, analysis_run_id: str, user_id: str):
    run_row = await pool.fetchrow(
        "SELECT a.id, a.\"timestamp\", a.palavras_analisadas, a.creditos_consumidos, "
        "c.titulo as capitulo_titulo, p.nome as projeto_nome "
        "FROM analysis_runs a JOIN chapters c ON c.id = a.chapter_id JOIN projects p ON p.id = c.project_id "
        "WHERE a.id=$1 AND p.user_id=$2",
        analysis_run_id, user_id,
    )
    if not run_row:
        raise HTTPException(404, 'Análise não encontrada')
    checks = await pool.fetch(
        "SELECT check_type, numero, tipo, confiabilidade, contagem, detalhes_json FROM check_results "
        "WHERE analysis_run_id=$1 ORDER BY numero",
        analysis_run_id,
    )
    fatos, julgamento = [], []
    for c in checks:
        item = dict(c)
        raw = json.loads(item.pop('detalhes_json'))
        if isinstance(raw, dict) and 'items' in raw:
            item['detalhes'] = raw.get('items') or []
            item['summary'] = raw.get('summary')
        else:
            item['detalhes'] = raw or []
            item['summary'] = None
        (julgamento if item['tipo'] == 'julgamento' else fatos).append(item)
    return dict(run_row), fatos, julgamento


def _build_markdown(run_row, fatos, julgamento, lang: str) -> str:
    L, N = LABELS[lang], CHECK_NAMES[lang]
    lines = [
        f"# {L['title']}", '',
        f"**{L['project']}:** {run_row['projeto_nome']}  ",
        f"**{L['chapter']}:** {run_row['capitulo_titulo']}  ",
        f"**{L['date']}:** {run_row['timestamp']}  ",
        f"**{L['words']}:** {run_row['palavras_analisadas']}  ",
        f"**{L['credits']}:** {run_row['creditos_consumidos']}", '', '---', '',
        f"## {L['facts']}", '',
    ]
    for check in fatos:
        nome = N.get(check['check_type'], check['check_type'])
        lines.append(f"### {nome} — {check['contagem']} {L['occurrences']}")
        if not check['detalhes']:
            lines.append(f"_{L['no_issues']}_")
        for d in check['detalhes']:
            lines.append(f"- **{d.get('trecho', '')}**")
            if d.get('sugestao'):
                lines.append(f"  - {d['sugestao']}")
        lines.append('')
    lines += [f"## {L['critical']}", '', f"_{L['disclaimer']}_", '']
    if not julgamento:
        lines.append(L['no_ai_results'])
    for check in julgamento:
        nome = N.get(check['check_type'], check['check_type'])
        lines.append(f"### {nome}")
        if check.get('summary'):
            lines.append(f"**{L['summary']}:** {check['summary']}")
        if not check['detalhes']:
            lines.append(f"_{L['no_issues']}_")
        for d in check['detalhes']:
            lines.append(f"- **{d.get('trecho', '')}**")
            if d.get('sugestao'):
                lines.append(f"  - {d['sugestao']}")
        lines.append('')
    return '\n'.join(lines)


def _build_pdf(run_row, fatos, julgamento, lang: str) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

    L, N = LABELS[lang], CHECK_NAMES[lang]
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2 * cm, bottomMargin=2 * cm,
                             leftMargin=2 * cm, rightMargin=2 * cm)
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle('h1', parent=styles['Heading1'], spaceAfter=10)
    h2 = ParagraphStyle('h2', parent=styles['Heading2'], spaceBefore=14, spaceAfter=6, textColor=colors.HexColor('#1f2937'))
    h3 = ParagraphStyle('h3', parent=styles['Heading3'], spaceBefore=8, spaceAfter=4, textColor=colors.HexColor('#374151'))
    meta = ParagraphStyle('meta', parent=styles['Normal'], fontSize=9, textColor=colors.HexColor('#6b7280'))
    body = ParagraphStyle('body', parent=styles['Normal'], fontSize=10, spaceAfter=4)
    finding = ParagraphStyle('finding', parent=styles['Normal'], fontSize=9.5, leftIndent=12, spaceAfter=6)

    def esc(s):
        return (s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

    story = [Paragraph(L['title'], h1)]
    story.append(Paragraph(
        f"{L['project']}: {esc(run_row['projeto_nome'])} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{L['chapter']}: {esc(run_row['capitulo_titulo'])}<br/>"
        f"{L['date']}: {run_row['timestamp']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{L['words']}: {run_row['palavras_analisadas']} &nbsp;&nbsp;|&nbsp;&nbsp; "
        f"{L['credits']}: {run_row['creditos_consumidos']}", meta))
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', color=colors.HexColor('#e5e7eb')))
    story.append(Paragraph(L['facts'], h2))
    for check in fatos:
        nome = N.get(check['check_type'], check['check_type'])
        story.append(Paragraph(f"{esc(nome)} — {check['contagem']} {L['occurrences']}", h3))
        if not check['detalhes']:
            story.append(Paragraph(f"<i>{L['no_issues']}</i>", body))
        for d in check['detalhes']:
            txt = f"<b>{esc(d.get('trecho', ''))}</b>"
            if d.get('sugestao'):
                txt += f"<br/>{esc(d['sugestao'])}"
            story.append(Paragraph(txt, finding))
    story.append(Spacer(1, 8))
    story.append(HRFlowable(width='100%', color=colors.HexColor('#e5e7eb')))
    story.append(Paragraph(L['critical'], h2))
    story.append(Paragraph(f"<i>{esc(L['disclaimer'])}</i>", meta))
    if not julgamento:
        story.append(Paragraph(L['no_ai_results'], body))
    for check in julgamento:
        nome = N.get(check['check_type'], check['check_type'])
        story.append(Paragraph(esc(nome), h3))
        if check.get('summary'):
            story.append(Paragraph(f"<b>{L['summary']}:</b> {esc(check['summary'])}", body))
        if not check['detalhes']:
            story.append(Paragraph(f"<i>{L['no_issues']}</i>", body))
        for d in check['detalhes']:
            txt = f"<b>{esc(d.get('trecho', ''))}</b>"
            if d.get('sugestao'):
                txt += f"<br/>{esc(d['sugestao'])}"
            story.append(Paragraph(txt, finding))

    doc.build(story)
    return buf.getvalue()


@router.get('/analysis_runs/{analysis_run_id}/export')
async def export_report(
    analysis_run_id: str,
    format: str = Query('pdf', pattern='^(pdf|md)$'),
    lang: str = Query('pt-BR'),
    user=Depends(current_user),
):
    pool = get_pool()
    run_row, fatos, julgamento = await _load_report_data(pool, analysis_run_id, user['sub'])
    lang = _lang_key(lang)
    filename_base = f"cowriter-relatorio-{analysis_run_id[:8]}"

    if format == 'md':
        content = _build_markdown(run_row, fatos, julgamento, lang)
        return Response(
            content=content, media_type='text/markdown; charset=utf-8',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.md"'},
        )

    pdf_bytes = _build_pdf(run_row, fatos, julgamento, lang)
    return Response(
        content=pdf_bytes, media_type='application/pdf',
        headers={'Content-Disposition': f'attachment; filename="{filename_base}.pdf"'},
    )
