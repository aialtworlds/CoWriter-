import re
from .helpers import excerpt
from .lexicons import GESTOS, normalize_lang, RELIABILITY

COOLDOWN_MAX = 1


def analyze(text: str, idioma: str, custom_patterns: list = None) -> dict:
    lang = normalize_lang(idioma)
    gestos = GESTOS.get(lang, GESTOS['en'])
    detalhes = []
    custom_hits = {}
    full_counts = {}
    for gesto in gestos:
        matches = list(re.finditer(re.escape(gesto), text, re.IGNORECASE))
        if matches:
            full_counts[gesto] = len(matches)
        if len(matches) > COOLDOWN_MAX:
            for m in matches[COOLDOWN_MAX:]:
                detalhes.append({
                    'trecho': excerpt(text, m.start(), m.end()),
                    'sugestao': f"Gesto \"{gesto}\" já apareceu neste capítulo (limite: {COOLDOWN_MAX}x). Varie a reação física do personagem.",
                    'inicio': m.start(),
                    'fim': m.end(),
                })
    for rule in (custom_patterns or []):
        texto_padrao = rule['texto_padrao']
        max_ocorrencias = rule.get('cooldown_max', COOLDOWN_MAX)
        matches = list(re.finditer(re.escape(texto_padrao), text, re.IGNORECASE))
        if len(matches) > max_ocorrencias:
            excedentes = matches[max_ocorrencias:]
            custom_hits[rule['id']] = len(excedentes)
            for m in excedentes:
                detalhes.append({
                    'trecho': excerpt(text, m.start(), m.end()),
                    'sugestao': f"Gesto personalizado \"{texto_padrao}\" excedeu o limite de {max_ocorrencias}x definido em Minhas Regras.",
                    'inicio': m.start(),
                    'fim': m.end(),
                })
    ocorrencias_por_gesto = dict(sorted(full_counts.items(), key=lambda kv: -kv[1])[:10])
    return {
        'check_type': 'gesture_cooldown',
        'numero': 2,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'custom_hits': custom_hits,
        'metricas': {'ocorrencias_por_gesto': ocorrencias_por_gesto},
    }
