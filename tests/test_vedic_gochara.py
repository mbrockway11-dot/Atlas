"""The sourced gochara transit-polarity table (Phaladipika, 1E-V-SOURCE-C).

Freezes the seven star-planets' auspicious-houses-from-Moon table as verified
against the page images, and the total polarity rule (Sloka 10: benefic in the
listed houses, malefic in the rest).
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.vedic_gochara import (
    GOCHARA_RULES,
    GOCHARA_SOURCE,
    VedicGocharaError,
    auspicious_houses,
    gochara_manifest,
    gochara_polarity,
    has_gochara,
)


# The verified table, kept here independently so a silent edit to the source
# module is caught.
EXPECTED = {
    "sun": {3, 6, 10, 11},
    "moon": {1, 3, 6, 7, 10, 11},
    "mars": {3, 6, 11},
    "mercury": {2, 4, 6, 8, 10, 11},
    "jupiter": {2, 5, 7, 9, 11},
    "venus": {1, 2, 3, 4, 5, 8, 9, 11, 12},
    "saturn": {3, 6, 11},
}


def test_the_seven_grahas_carry_the_verified_houses() -> None:
    """Each rule matches the page-image-verified Phaladipika table."""
    assert {rule.graha for rule in GOCHARA_RULES} == set(EXPECTED)

    for graha, houses in EXPECTED.items():
        assert auspicious_houses(graha) == frozenset(houses)


def test_polarity_is_total_benefic_in_list_malefic_otherwise() -> None:
    """Sloka 10: listed houses positive, every other house negative."""
    for graha, houses in EXPECTED.items():
        for house in range(1, 13):
            expected = "positive" if house in houses else "negative"
            assert gochara_polarity(graha, house) == expected


def test_saturn_sade_sati_houses_are_malefic() -> None:
    """A sanity check on a well-known case: Saturn in 12,1,2 from Moon is bad."""
    for house in (12, 1, 2):
        assert gochara_polarity("saturn", house) == "negative"
    # ...and its classic relief houses are benefic.
    for house in (3, 6, 11):
        assert gochara_polarity("saturn", house) == "positive"


def test_nodes_have_no_gochara_rule() -> None:
    """Rahu and Ketu are out of scope; no rule may be invented for them."""
    assert not has_gochara("rahu")
    assert not has_gochara("ketu")

    with pytest.raises(VedicGocharaError):
        auspicious_houses("rahu")


def test_house_out_of_range_is_rejected() -> None:
    """Houses are 1..12."""
    with pytest.raises(VedicGocharaError):
        gochara_polarity("sun", 13)


def test_provenance_is_recorded() -> None:
    """The table names its verified source copy."""
    assert "Phaladipika" in GOCHARA_SOURCE["work"]
    assert GOCHARA_SOURCE["file_hash"]
    assert "459723994" in GOCHARA_SOURCE["worldcat_oclc"]

    manifest = gochara_manifest()

    assert len(manifest["rules"]) == 7
    assert all("scan_leaf" in rule for rule in manifest["rules"])
