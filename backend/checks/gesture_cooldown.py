import re
from .helpers import excerpt
from .lexicons import GESTOS, normalize_lang, RELIABILITY

COOLDOWN_MAX = 1


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    gestos = GESTOS.get(lang, GESTOS['en'])
    detalhes = []
    for gesto in gestos:
        matches = list(re.finditer(re.escape(gesto), text, re.IGNORECASE))
        if len(matches) > COOLDOWN_MAX:
            for m in matches[COOLDOWN_MAX:]:
                detalhes.append({
                    'trecho': excerpt(text, m.start(), m.end()),
                    'sugestao': f"Gesto \"{gesto}\" já apareceu neste capítulo (limite: {COOLDOWN_MAX}x). Varie a reação física do personagem.",
                    'inicio': m.start(),
                    'fim': m.end(),
                })
    return {
        'check_type': 'gesture_cooldown',
        'numero': 2,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
    }
