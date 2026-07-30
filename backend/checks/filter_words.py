import re
from .helpers import excerpt
from .lexicons import FILTER_WORDS, normalize_lang, RELIABILITY


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    phrases = FILTER_WORDS.get(lang, FILTER_WORDS['en'])
    detalhes = []
    for phrase in phrases:
        for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
            detalhes.append({
                'trecho': excerpt(text, m.start(), m.end()),
                'sugestao': f"Palavra-filtro \"{phrase}\" afasta o leitor da experiência direta. Mostre a ação/sensação sem o filtro do narrador.",
                'inicio': m.start(),
                'fim': m.end(),
            })
    return {
        'check_type': 'filter_words',
        'numero': 6,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
    }
