import re
from .helpers import excerpt
from .lexicons import CLICHES, normalize_lang, RELIABILITY


def analyze(text: str, idioma: str, custom_patterns: list = None) -> dict:
    lang = normalize_lang(idioma)
    phrases = CLICHES.get(lang, CLICHES['en'])
    detalhes = []
    custom_hits = {}
    for phrase in phrases:
        for m in re.finditer(re.escape(phrase), text, re.IGNORECASE):
            detalhes.append({
                'trecho': excerpt(text, m.start(), m.end()),
                'sugestao': f"Frase-clichê de IA detectada: \"{phrase}\". Reescreva com uma imagem específica da cena ou do personagem.",
                'inicio': m.start(),
                'fim': m.end(),
            })
    for rule in (custom_patterns or []):
        texto_padrao = rule['texto_padrao']
        matches = list(re.finditer(re.escape(texto_padrao), text, re.IGNORECASE))
        if matches:
            custom_hits[rule['id']] = len(matches)
            for m in matches:
                detalhes.append({
                    'trecho': excerpt(text, m.start(), m.end()),
                    'sugestao': f"Regra personalizada disparada: \"{texto_padrao}\". Reescreva esse trecho.",
                    'inicio': m.start(),
                    'fim': m.end(),
                })
    return {
        'check_type': 'ai_fingerprint',
        'numero': 1,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': len(detalhes),
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'custom_hits': custom_hits,
    }
