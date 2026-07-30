import re
from .helpers import split_sentences, excerpt
from .lexicons import SPEECH_VERBS, ADVERB_SUFFIX, normalize_lang, RELIABILITY

MIN_OCCURRENCES = 3


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    verbs = SPEECH_VERBS.get(lang, SPEECH_VERBS['en'])
    suffix = ADVERB_SUFFIX.get(lang, '')
    verb_pattern = r'\b(' + '|'.join(re.escape(v) for v in verbs) + r')\b'
    detalhes = []
    if suffix:
        adverb_pattern = r'\b\w+' + re.escape(suffix) + r'\b'
        for sentence, start, end in split_sentences(text):
            if re.search(verb_pattern, sentence, re.IGNORECASE) and re.search(adverb_pattern, sentence, re.IGNORECASE):
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
    }
