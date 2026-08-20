"""Behavioural checks for the shared Persian normalizer."""

from app.utils.persian import ZWNJ, normalize, query_variants


def test_arabic_orthography_folds_to_persian() -> None:
    # The same word written with Arabic yeh/kaf must match the Persian spelling.
    assert normalize("كيان") == normalize("کیان")


def test_digits_from_both_scripts_become_ascii() -> None:
    assert normalize("پورت ۸۰۰۲") == "پورت 8002"
    assert normalize("٤٠٤") == "404"


def test_tashkeel_and_tatweel_are_dropped() -> None:
    assert normalize("مُحَمَّد") == "محمد"
    assert normalize("لــیارا") == "لیارا"


def test_heh_variants_unify() -> None:
    assert normalize("برنامة") == normalize("برنامه")


def test_nfd_trap_does_not_corrupt_the_word() -> None:
    # U+06D5 is a letter, not a mark. Folding must reach 'ه', not delete it.
    assert normalize("ۀ") == "ه"


def test_zwnj_is_stripped_for_indexing_but_kept_for_display() -> None:
    word = f"می{ZWNJ}شود"
    assert normalize(word) == "میشود"
    assert ZWNJ in normalize(word, strip_zwnj=False)


def test_query_variants_cover_both_zwnj_readings_without_duplicates() -> None:
    variants = query_variants(f"می{ZWNJ}شود")
    assert variants == ["میشود", f"می{ZWNJ}شود"]
    # A word with no ZWNJ collapses to a single variant rather than repeating.
    assert query_variants("لیارا") == ["لیارا"]
