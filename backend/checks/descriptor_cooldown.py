import re
from .helpers import excerpt
from .lexicons import DESCRITORES, normalize_lang, RELIABILITY

COOLDOWN_MAX = 1


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    descritores = DESCRITORES.get(lang, DESCRITORES['en'])
    detalhes = []
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
    return {
        'check_type': 'descriptor_cooldown',
        'numero': 3,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
    }
