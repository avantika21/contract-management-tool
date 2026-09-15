"""Clause/section-aware chunking.

Splits contract text on common heading conventions (ARTICLE N, SECTION
N.N, "12.1 Limitation of Liability", "4. GOVERNING LAW") so a chunk holds
one clause rather than an arbitrary slice of running text - a large
blended chunk dilutes its embedding and makes it match poorly against any
one targeted query. Sections with no detected heading (or one section
that's unusually long) fall back to a word-based sliding window.
"""
import re

MAX_SECTION_WORDS = 400
FALLBACK_CHUNK_WORDS = 350
FALLBACK_OVERLAP_WORDS = 60
MIN_MERGE_WORDS = 40

_HEADING_RE = re.compile(
    r"""
    ARTICLE\s+[IVXLCDM\d]+\b                          # ARTICLE 12 / ARTICLE XII
    | SECTION\s+\d+(?:\.\d+)*\b                        # SECTION 5.6
    | \b\d{1,2}\.\d{1,2}(?:\.\d{1,2})?\s+[A-Z][a-z]     # 12.1 Limitation of Liability
    | \b\d{1,2}\.\s+[A-Z]{2,}(?:[ A-Z]{0,40})?\b        # 4. GOVERNING LAW
    """,
    re.VERBOSE,
)


def _split_on_headings(text: str) -> list[str]:
    starts = [m.start() for m in _HEADING_RE.finditer(text)]
    if not starts:
        return [text]

    segments = []
    if starts[0] > 0:
        segments.append(text[: starts[0]])
    for start, end in zip(starts, starts[1:] + [len(text)]):
        segments.append(text[start:end])
    return [s for s in segments if s.strip()]


def _word_window(text: str, chunk_size: int, overlap: int) -> list[str]:
    words = text.split()
    if not words:
        return []

    chunks = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end == len(words):
            break
        start = end - overlap
    return chunks


def chunk_text(
    text: str,
    max_section_words: int = MAX_SECTION_WORDS,
    fallback_chunk_words: int = FALLBACK_CHUNK_WORDS,
    fallback_overlap_words: int = FALLBACK_OVERLAP_WORDS,
    min_merge_words: int = MIN_MERGE_WORDS,
) -> list[str]:
    if not text.split():
        return []

    chunks: list[str] = []
    for segment in _split_on_headings(text):
        words = segment.split()
        if len(words) > max_section_words:
            chunks.extend(_word_window(segment, fallback_chunk_words, fallback_overlap_words))
        elif words:
            chunks.append(segment.strip())

    # A bare heading with little else (or a short recital) makes a poor,
    # near-empty embedding target - fold it into the next chunk instead of
    # leaving it to stand alone.
    merged: list[str] = []
    carry = ""
    for chunk in chunks:
        candidate = (carry + " " + chunk).strip() if carry else chunk
        if len(candidate.split()) < min_merge_words:
            carry = candidate
            continue
        merged.append(candidate)
        carry = ""
    if carry:
        if merged:
            merged[-1] = (merged[-1] + " " + carry).strip()
        else:
            merged.append(carry)

    return merged
