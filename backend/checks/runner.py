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


def run_deterministic_checks(text: str, idioma: str) -> list:
    return [module.analyze(text, idioma) for module in CHECK_MODULES]
