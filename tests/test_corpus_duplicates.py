from atlas.corpus.duplicates import (
    canonicalize_name,
    detect_duplicate_names,
    detect_possible_aliases,
)


def test_canonicalize_name():
    assert canonicalize_name("Alan_Mathison-Turing") == "alan mathison turing"


def test_detect_duplicate_names():
    duplicates = detect_duplicate_names(
        [
            "Alan Turing",
            "alan_turing",
            "Nikola Tesla",
        ]
    )

    assert duplicates
    assert duplicates[0]["count"] == 2


def test_detect_possible_aliases():
    aliases = detect_possible_aliases(
        [
            "Alan Turing",
            "Alan Mathison Turing",
            "Nikola Tesla",
        ]
    )

    assert aliases
    assert aliases[0]["name_a"] == "Alan Turing"
    assert aliases[0]["name_b"] == "Alan Mathison Turing"