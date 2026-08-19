import re
from .helpers import split_sentences, excerpt
from .lexicons import SPEECH_VERBS, ADVERB_SUFFIX, normalize_lang, RELIABILITY

MIN_OCCURRENCES = 3


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    verbs = SPEECH_VERBS.get(lang, SPEECH_VERBS['en'])
    suffix = ADVERB_SUFFIX.get(lang, '')
    verb_pattern = r'\b(' + '|'.join(re.escape(v) for v in verbs) + r')\b'
    adverb_pattern = r'\b\w+' + re.escape(suffix) + r'\b' if suffix else None
    detalhes = []
    falas_com_tag_detectadas = 0
    falas_com_adverbio = 0
    for sentence, start, end in split_sentences(text):
        if not re.search(verb_pattern, sentence, re.IGNORECASE):
            continue
        falas_com_tag_detectadas += 1
        if adverb_pattern and re.search(adverb_pattern, sentence, re.IGNORECASE):
            falas_com_adverbio += 1
            detalhes.append({
                'trecho': excerpt(text, start, end, pad=0),
                'sugestao': "Combinação de verbo de fala + advérbio. Prefira mostrar o tom através da ação ou do próprio diálogo.",
                'inicio': start,
                'fim': end,
            })
    contagem = len(detalhes)
    if contagem < MIN_OCCURRENCES:
        detalhes = []
    return {
        'check_type': 'dialogue_tag_variety',
        'numero': 7,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': contagem,
        'contagem': len(detalhes),
        'detalhes': detalhes,
        'metricas': {
            'falas_com_tag_detectadas': falas_com_tag_detectadas,
            'falas_com_adverbio': falas_com_adverbio,
        },
    }
