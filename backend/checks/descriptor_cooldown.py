import re
from .helpers import excerpt
from .lexicons import DESCRITORES, normalize_lang, RELIABILITY

COOLDOWN_MAX = 1


def analyze(text: str, idioma: str, custom_patterns: list = None) -> dict:
    lang = normalize_lang(idioma)
    descritores = DESCRITORES.get(lang, DESCRITORES['en'])
    detalhes = []
    custom_hits = {}
    for descritor in descritores:
        matches = list(re.finditer(re.escape(descritor), text, re.IGNORECASE))
        if len(matches) > COOLDOWN_MAX:
            for m in matches[COOLDOWN_MAX:]:
                detalhes.append({
                    'trecho': excerpt(text, m.start(), m.end()),
                    'sugestao': f"Descritor \"{descritor}\" repetido dentro do mesmo capítulo. Varie a caracterização física.",
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
                    'sugestao': f"Descritor personalizado \"{texto_padrao}\" excedeu o limite de {max_ocorrencias}x definido em Minhas Regras.",
                    'inicio': m.start(),
                    'fim': m.end(),
                })
    return {
        'check_type': 'descriptor_cooldown',
        'numero': 3,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'custom_hits': custom_hits,
    }
