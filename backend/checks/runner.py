from . import (
    ai_fingerprint,
    gesture_cooldown,
    descriptor_cooldown,
    prose_rhythm,
    sensory_rotation,
    filter_words,
    dialogue_tag_variety,
    paragraph_opening_monotony,
)

CHECK_MODULES = [
    ai_fingerprint,
    gesture_cooldown,
    descriptor_cooldown,
    prose_rhythm,
    sensory_rotation,
    filter_words,
    dialogue_tag_variety,
    paragraph_opening_monotony,
]


def run_deterministic_checks(text: str, idioma: str, custom_patterns_by_tipo: dict = None) -> list:
    custom_patterns_by_tipo = custom_patterns_by_tipo or {}
    frases_e_estruturas = custom_patterns_by_tipo.get('frase', []) + custom_patterns_by_tipo.get('estrutura', [])

    results = []
    results.append(ai_fingerprint.analyze(text, idioma, frases_e_estruturas))
    results.append(gesture_cooldown.analyze(text, idioma, custom_patterns_by_tipo.get('gesto', [])))
    results.append(descriptor_cooldown.analyze(text, idioma, custom_patterns_by_tipo.get('descritor', [])))
    results.append(prose_rhythm.analyze(text, idioma))
    results.append(sensory_rotation.analyze(text, idioma))
    results.append(filter_words.analyze(text, idioma))
    results.append(dialogue_tag_variety.analyze(text, idioma))
    results.append(paragraph_opening_monotony.analyze(text, idioma))
    return results
