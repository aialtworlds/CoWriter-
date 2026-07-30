import re
from .helpers import excerpt
from .lexicons import SENSORY, normalize_lang, RELIABILITY

DOMINANCE_THRESHOLD = 0.7


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    channels = SENSORY.get(lang, SENSORY['en'])
    counts = {}
    examples = {}
    total = 0
    for channel, words in channels.items():
        c = 0
        exs = []
        for w in words:
            for m in re.finditer(re.escape(w), text, re.IGNORECASE):
                c += 1
                if len(exs) < 2:
                    exs.append(excerpt(text, m.start(), m.end()))
        counts[channel] = c
        examples[channel] = exs
        total += c

    detalhes = []
    if total > 0:
        dominant = max(counts, key=counts.get)
        ratio = counts[dominant] / total
        if ratio >= DOMINANCE_THRESHOLD and counts[dominant] >= 3:
            detalhes.append({
                'trecho': ' / '.join(examples[dominant]) or dominant,
                'sugestao': f"Canal sensorial '{dominant}' domina {round(ratio * 100)}% das menções. Varie com som, textura, olfato ou paladar.",
                'inicio': 0,
                'fim': 0,
            })

    return {
        'check_type': 'sensory_rotation',
        'numero': 5,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': total,
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'distribuicao': counts,
    }
