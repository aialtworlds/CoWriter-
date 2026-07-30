import statistics
from .helpers import split_sentences, excerpt
from .lexicons import normalize_lang, RELIABILITY

MIN_STDEV_RATIO = 0.35


def analyze(text: str, idioma: str) -> dict:
    lang = normalize_lang(idioma)
    sentences = split_sentences(text)
    lengths = [len(s.split()) for s, _, _ in sentences]
    detalhes = []
    if len(lengths) >= 4:
        mean = statistics.mean(lengths)
        stdev = statistics.pstdev(lengths)
        ratio = (stdev / mean) if mean else 0
        if ratio < MIN_STDEV_RATIO:
            # flag runs of 3+ consecutive sentences with very similar length
            run = [sentences[0]]
            for i in range(1, len(sentences)):
                if abs(lengths[i] - lengths[i - 1]) <= 2:
                    run.append(sentences[i])
                else:
                    if len(run) >= 3:
                        s_start = run[0][1]
                        s_end = run[-1][2]
                        detalhes.append({
                            'trecho': excerpt(text, s_start, s_end, pad=0),
                            'sugestao': "Sequência de frases com tamanho muito parecido. Alterne frases curtas e longas para dar ritmo à prosa.",
                            'inicio': s_start,
                            'fim': s_end,
                        })
                    run = [sentences[i]]
            if len(run) >= 3:
                s_start = run[0][1]
                s_end = run[-1][2]
                detalhes.append({
                    'trecho': excerpt(text, s_start, s_end, pad=0),
                    'sugestao': "Sequência de frases com tamanho muito parecido. Alterne frases curtas e longas para dar ritmo à prosa.",
                    'inicio': s_start,
                    'fim': s_end,
                })
    return {
        'check_type': 'prose_rhythm',
        'numero': 4,
        'tipo': 'deterministico',
        'confiabilidade': RELIABILITY.get(lang, 'generico'),
        'score': round(statistics.pstdev(lengths), 2) if len(lengths) > 1 else 0,
        'contagem': len(detalhes),
        'detalhes': detalhes,
    }
