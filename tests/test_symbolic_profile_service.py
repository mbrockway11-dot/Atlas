from datetime import date

from atlas.services.symbolic_profile_service import (
    build_gematria_profile,
    build_numerology_profile,
    reduce_number,
)


def test_full_numerology_profile_is_deterministic_and_explainable():
    report = build_numerology_profile(
        "Michael Elvis Brockway",
        "1993-08-16",
        as_of=date(2026, 7, 21),
    )

    assert report["available"] is True
    assert report["core_numbers"]["life_path"]["number"] == 1
    assert report["core_numbers"]["birthday"]["number"] == 7
    assert report["core_numbers"]["expression"]["method"] == "Pythagorean values of every name letter"
    assert set(report["core_numbers"]) >= {
        "life_path",
        "birthday",
        "attitude",
        "expression",
        "soul_urge",
        "personality",
        "balance",
        "maturity",
    }
    assert len(report["pinnacles"]) == 4
    assert len(report["challenges"]) == 4
    assert report["cycles"]["as_of"] == "2026-07-21"
    assert report["vowel_policy"].startswith("A, E, I, O, U")


def test_master_numbers_are_preserved_only_when_requested():
    assert reduce_number(29) == 11
    assert reduce_number(29, preserve_masters=False) == 2
    assert reduce_number(38) == 11


def test_gematria_uses_all_atlas_systems_and_reports_convergence():
    report = build_gematria_profile("Michael Elvis Brockway")

    assert report["available"] is True
    assert set(report["systems"]) == {
        "ordinal",
        "hebrew_literal",
        "hebrew_phonetic",
        "reverse_ordinal",
    }
    assert report["systems"]["ordinal"]["total"] == sum(report["systems"]["ordinal"]["sequence"])
    assert report["systems"]["hebrew_literal"]["length"] > 0
    assert report["cross_system"]["system_count"] == 4
    assert len(report["cross_system"]["digital_roots"]) == 4
