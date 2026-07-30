import re


def excerpt(text: str, start: int, end: int, pad: int = 40) -> str:
    s = max(0, start - pad)
    e = min(len(text), end + pad)
    return text[s:e].strip().replace('\n', ' ')


def split_sentences(text: str):
    """Returns list of (sentence, start, end) with char offsets."""
    pattern = re.compile(r'[^.!?…]+[.!?…]*', re.UNICODE)
    out = []
    for m in pattern.finditer(text):
        s = m.group().strip()
        if s:
            out.append((s, m.start(), m.end()))
    return out


def split_paragraphs(text: str):
    """Returns list of (paragraph, start, end)."""
    out = []
    pos = 0
    for para in re.split(r'\n\s*\n', text):
        start = text.find(para, pos)
        if start == -1:
            start = pos
        end = start + len(para)
        pos = end
        if para.strip():
            out.append((para.strip(), start, end))
    return out


def count_words(text: str) -> int:
    return len(text.split())
