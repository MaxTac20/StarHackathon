"""Persian text normalization, shared by ingestion and query time.

The corpus mixes Persian and Arabic orthography for the same letters, both digit
sets, and inconsistent ZWNJ. Matching folded forms is what makes the lexical leg
of retrieval work at all; see ``docs/CONTRACTS.md``.
"""

from __future__ import annotations

import re
import unicodedata

ZWNJ = "‌"

# Arabic orthography and presentation forms that must read as their Persian letter.
_FOLD = {
    "ي": "ی",  # ARABIC YEH        -> FARSI YEH
    "ى": "ی",  # ALEF MAKSURA      -> FARSI YEH
    "ك": "ک",  # ARABIC KAF        -> KEHEH
    "ة": "ه",  # TEH MARBUTA       -> HEH
    "ە": "ه",  # AE                -> HEH
    "ۀ": "ه",  # HEH WITH YEH ABOVE      -> HEH  (U+06C0; NFKC leaves it alone)
    "ۂ": "ه",  # HEH GOAL WITH HAMZA     -> HEH
    "ہ": "ه",  # HEH GOAL                -> HEH
    "أ": "ا",  # ALEF WITH HAMZA ABOVE
    "إ": "ا",  # ALEF WITH HAMZA BELOW
    "آ": "ا",  # ALEF WITH MADDA
    "ؤ": "و",  # WAW WITH HAMZA
    "ئ": "ی",  # YEH WITH HAMZA
}

# Tashkeel, tatweel, and bidirectional controls carry no lexical meaning here.
_DELETE = {
    ord(c): None
    for c in (
        *(chr(c) for c in range(0x064B, 0x0653)),  # tashkeel
        "ـ",  # tatweel
        "‎",  # LRM
        "‏",  # RLM
        "ً",
    )
}

_DIGITS = {
    **{0x06F0 + i: ord("0") + i for i in range(10)},  # Persian
    **{0x0660 + i: ord("0") + i for i in range(10)},  # Arabic-Indic
}

_FOLD_TABLE = {ord(k): v for k, v in _FOLD.items()}
_WHITESPACE = re.compile(r"\s+")


def normalize(text: str, *, strip_zwnj: bool = True) -> str:
    """Fold ``text`` to its canonical Persian form.

    NFKC only. Never NFD: ``ۀ`` decomposes to U+06D5 + U+0654, and U+06D5 is a
    letter, so stripping combining marks afterwards silently rewrites the word.

    ``strip_zwnj`` removes zero-width non-joiners, which is right for building a
    lexical index and wrong for text shown to a person.
    """
    out = unicodedata.normalize("NFKC", text)
    out = out.translate(_DELETE)
    out = out.translate(_FOLD_TABLE)
    out = out.translate(_DIGITS)
    if strip_zwnj:
        out = out.replace(ZWNJ, "")
    return _WHITESPACE.sub(" ", out).strip()


def query_variants(text: str) -> list[str]:
    """Both ZWNJ readings of ``text``, most-normalized first, without duplicates.

    Roughly a third of Persian word types in the corpus contain a ZWNJ and the
    authors are not consistent about it, so a query has to be tried both ways.
    """
    variants = [normalize(text, strip_zwnj=True), normalize(text, strip_zwnj=False)]
    return list(dict.fromkeys(v for v in variants if v))
