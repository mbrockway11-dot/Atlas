from atlas.ciphers import (
    english_ordinal_sequence,
    hebrew_literal_sequence,
    hebrew_phonetic_sequence,
    run_all_ciphers,
)


def test_english_ordinal_sequence():
    assert english_ordinal_sequence("ABC") == [1, 2, 3]


def test_hebrew_literal_sequence_is_letter_for_letter():
    assert hebrew_literal_sequence("MICHAEL") == [40, 10, 20, 8, 1, 5, 30]


def test_hebrew_phonetic_sequence_combines_sound_groups():
    assert hebrew_phonetic_sequence("PH") == [80]
    assert hebrew_phonetic_sequence("TH") == [400]
    assert hebrew_phonetic_sequence("SH") == [300]
    assert hebrew_phonetic_sequence("CH") == [20]
    assert hebrew_phonetic_sequence("CK") == [20]


def test_hebrew_literal_and_phonetic_differ_for_michael():
    literal = hebrew_literal_sequence("Michael")
    phonetic = hebrew_phonetic_sequence("Michael")

    assert literal == [40, 10, 20, 8, 1, 5, 30]
    assert phonetic == [40, 10, 20, 1, 5, 30]
    assert literal != phonetic


def test_run_all_ciphers():
    result = run_all_ciphers("Michael Elvis Brockway")

    assert set(result) == {
        "ordinal",
        "hebrew_literal",
        "hebrew_phonetic",
    }

    assert result["hebrew_literal"] != result["hebrew_phonetic"]