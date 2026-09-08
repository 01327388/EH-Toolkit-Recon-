from app.services.matching import _slugify, _word_overlap


def test_slugify_strips_common_suffixes_and_punctuation():
    assert _slugify("Acme, Inc.") == "acme"
    assert _slugify("Widget Corporation") == "widget"
    assert _slugify("Foo-Bar LLC") == "foobar"


def test_slugify_handles_empty_and_symbols():
    assert _slugify("!!!") == ""


def test_word_overlap_identical_strings_is_one():
    assert _word_overlap("Acme Corp", "Acme Corp") == 1.0


def test_word_overlap_disjoint_strings_is_zero():
    assert _word_overlap("Acme Corp", "Totally Different") == 0.0


def test_word_overlap_partial_match():
    score = _word_overlap("Acme Corp", "Acme Industries")
    assert 0 < score < 1
