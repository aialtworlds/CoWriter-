import re
from collections import Counter
from .helpers import split_paragraphs, excerpt
from .lexicons import normalize_lang, RELIABILITY

MIN_REPEATS = 3


def opening_words(paragraph: str, n: int = 2) -> str:
    words = re.findall(r"[\wÀ-ÿ']+", paragraph.lower())
    return ' '.join(words[:n])


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    paragraphs = split_paragraphs(text)
    openings = [opening_words(p) for p, _, _ in paragraphs]
    counts = Counter(o for o in openings if o)
    detalhes = []
    for opening, count in counts.items():
        if count >= MIN_REPEATS:
            positions = [paragraphs[i] for i, o in enumerate(openings) if o == opening]
            for p, start, end in positions:
                detalhes.append({
                    'trecho': excerpt(text, start, min(start + 60, end)),
                    'sugestao': f"Abertura de parágrafo \"{opening}\" repetida {count}x no capítulo. Varie a estrutura inicial das frases.",
                    'inicio': start,
                    'fim': end,
                })
    return {
        'check_type': 'paragraph_opening_monotony',
        'numero': 8,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'metricas': {
            'total_paragrafos': len(paragraphs),
            'maior_repeticao': max(counts.values()) if counts else 0,
            'limite': MIN_REPEATS,
        },
    }
