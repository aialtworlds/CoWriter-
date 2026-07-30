"""Embedded lexicons for the 8 deterministic checks, per language.
Reliability: 'verificado' for pt/en (curated), 'generico' for es/it/fr/de (lightweight lists).
"""

RELIABILITY = {
    'pt': 'verificado',
    'en': 'verificado',
    'es': 'generico',
    'it': 'generico',
    'fr': 'generico',
    'de': 'generico',
}

SUPPORTED_LANGS = ['pt', 'en', 'es', 'it', 'fr', 'de']


def normalize_lang(idioma: str) -> str:
    if not idioma:
        return 'pt'
    idioma = idioma.lower()
    if idioma.startswith('pt'):
        return 'pt'
    if idioma.startswith('en'):
        return 'en'
    if idioma.startswith('es'):
        return 'es'
    if idioma.startswith('it'):
        return 'it'
    if idioma.startswith('fr'):
        return 'fr'
    if idioma.startswith('de'):
        return 'de'
    return idioma if idioma in SUPPORTED_LANGS else 'pt'


CLICHES = {
    'pt': [
        "um silêncio ensurdecedor", "seu coração parecia querer saltar pelo peito",
        "o tempo parecia ter parado", "um frio percorreu sua espinha",
        "ela não sabia se ria ou chorava", "seus olhos brilhavam como estrelas",
        "um nó se formou em sua garganta", "o mundo ao seu redor desapareceu",
        "ele sentiu um aperto no peito", "as palavras morreram em sua garganta",
        "um turbilhão de emoções", "seu sangue gelou", "respirou fundo antes de responder",
        "não pôde deixar de notar", "algo em seu olhar mudou",
    ],
    'en': [
        "a deafening silence", "her heart threatened to leap out of her chest",
        "time seemed to stop", "a chill ran down his spine",
        "she didn't know whether to laugh or cry", "his eyes sparkled like stars",
        "a lump formed in her throat", "the world around them disappeared",
        "a wave of emotions washed over", "her blood ran cold",
        "took a deep breath before answering", "couldn't help but notice",
        "something in his gaze shifted", "little did she know",
    ],
    'es': ["un silencio ensordecedor", "el tiempo pareció detenerse", "un escalofrío recorrió su espalda"],
    'it': ["un silenzio assordante", "il tempo sembrò fermarsi", "un brivido le percorse la schiena"],
    'fr': ["un silence assourdissant", "le temps sembla s'arrêter", "un frisson lui parcourut l'échine"],
    'de': ["eine ohrenbetäubende stille", "die zeit schien stehen zu bleiben", "ein schauer lief ihr über den rücken"],
}

GESTOS = {
    'pt': [
        "sorriu", "suspirou", "cruzou os braços", "mordeu o lábio", "deu de ombros",
        "arqueou a sobrancelha", "franziu a testa", "apertou os olhos", "passou a mão pelo cabelo",
        "respirou fundo", "engoliu em seco", "cerrou os punhos", "desviou o olhar",
    ],
    'en': [
        "smiled", "sighed", "crossed her arms", "bit her lip", "shrugged",
        "raised an eyebrow", "furrowed his brow", "narrowed her eyes", "ran a hand through his hair",
        "took a deep breath", "swallowed hard", "clenched his fists", "looked away",
    ],
    'es': ["sonrió", "suspiró", "se cruzó de brazos", "se mordió el labio", "se encogió de hombros"],
    'it': ["sorrise", "sospirò", "incrociò le braccia", "si morse il labbro", "scrollò le spalle"],
    'fr': ["sourit", "soupira", "croisa les bras", "se mordit la lèvre", "haussa les épaules"],
    'de': ["lächelte", "seufzte", "verschränkte die arme", "biss sich auf die lippe", "zuckte mit den schultern"],
}

DESCRITORES = {
    'pt': [
        "olhos azuis", "olhos verdes", "olhos castanhos", "cabelo escuro", "cabelo loiro",
        "sorriso torto", "voz grave", "mãos calejadas", "pele pálida", "corpo esguio",
    ],
    'en': [
        "blue eyes", "green eyes", "brown eyes", "dark hair", "blonde hair",
        "crooked smile", "deep voice", "calloused hands", "pale skin", "slender body",
    ],
    'es': ["ojos azules", "cabello oscuro", "sonrisa torcida", "voz grave", "piel pálida"],
    'it': ["occhi azzurri", "capelli scuri", "sorriso storto", "voce profonda", "pelle pallida"],
    'fr': ["yeux bleus", "cheveux sombres", "sourire en coin", "voix grave", "peau pâle"],
    'de': ["blaue augen", "dunkles haar", "schiefes lächeln", "tiefe stimme", "blasse haut"],
}

SENSORY = {
    'pt': {
        'visual': ["viu", "olhou", "observou", "notou", "avistou", "vislumbrou", "brilhante", "escuro", "cor", "luz"],
        'auditivo': ["ouviu", "escutou", "som", "ruído", "sussurro", "grito", "silêncio", "eco", "voz", "barulho"],
        'olfativo': ["cheiro", "aroma", "fedor", "perfume", "sentiu o odor", "cheirava a"],
        'tatil': ["tocou", "sentiu a textura", "áspero", "suave", "quente", "frio", "macio", "rugoso"],
        'gustativo': ["sabor", "gosto", "provou", "doce", "amargo", "salgado", "azedo"],
    },
    'en': {
        'visual': ["saw", "looked", "watched", "noticed", "glimpsed", "spotted", "bright", "dark", "color", "light"],
        'auditivo': ["heard", "listened", "sound", "noise", "whisper", "scream", "silence", "echo", "voice"],
        'olfativo': ["smell", "scent", "stench", "perfume", "odor", "smelled of"],
        'tatil': ["touched", "texture", "rough", "smooth", "warm", "cold", "soft", "coarse"],
        'gustativo': ["taste", "flavor", "tasted", "sweet", "bitter", "salty", "sour"],
    },
    'es': {'visual': ["vio", "miró", "brillante"], 'auditivo': ["oyó", "sonido"], 'olfativo': ["olor", "aroma"], 'tatil': ["tocó", "suave"], 'gustativo': ["sabor", "dulce"]},
    'it': {'visual': ["vide", "guardò", "luminoso"], 'auditivo': ["sentì", "suono"], 'olfativo': ["odore", "profumo"], 'tatil': ["toccò", "morbido"], 'gustativo': ["sapore", "dolce"]},
    'fr': {'visual': ["vit", "regarda", "lumineux"], 'auditivo': ["entendit", "son"], 'olfativo': ["odeur", "parfum"], 'tatil': ["toucha", "doux"], 'gustativo': ["goût", "sucré"]},
    'de': {'visual': ["sah", "blickte", "hell"], 'auditivo': ["hörte", "klang"], 'olfativo': ["geruch", "duft"], 'tatil': ["berührte", "weich"], 'gustativo': ["geschmack", "süß"]},
}

FILTER_WORDS = {
    'pt': ["viu que", "sentiu que", "percebeu que", "notou que", "ouviu que", "reparou que", "soube que", "constatou que"],
    'en': ["saw that", "felt that", "noticed that", "realized that", "heard that", "knew that", "wondered if"],
    'es': ["vio que", "sintió que", "notó que", "se dio cuenta de que"],
    'it': ["vide che", "sentì che", "si accorse che", "si rese conto che"],
    'fr': ["vit que", "sentit que", "remarqua que", "se rendit compte que"],
    'de': ["sah, dass", "fühlte, dass", "merkte, dass", "bemerkte, dass"],
}

SPEECH_VERBS = {
    'pt': ["disse", "falou", "perguntou", "respondeu", "murmurou", "gritou", "exclamou", "sussurrou"],
    'en': ["said", "spoke", "asked", "replied", "murmured", "shouted", "exclaimed", "whispered"],
    'es': ["dijo", "preguntó", "respondió", "murmuró", "gritó"],
    'it': ["disse", "chiese", "rispose", "borbottò", "gridò"],
    'fr': ["dit", "demanda", "répondit", "murmura", "cria"],
    'de': ["sagte", "fragte", "antwortete", "murmelte", "rief"],
}

ADVERB_SUFFIX = {
    'pt': 'mente',
    'en': 'ly',
    'es': 'mente',
    'it': 'mente',
    'fr': 'ment',
    'de': '',
}
