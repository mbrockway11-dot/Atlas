"""The Vedic transit substrate: graha karakatva at transit scope.

A transit reuses the sourced graha denotation at a time; it carries the house
from the Moon and the karakatva polarity (not a gochara-house polarity, which
awaits its own source). Transit claims are not comparable to natal claims, so
they cannot pollute the natal concordance.
"""

from __future__ import annotations

import pytest

from atlas.validation.denotation.expressions import (
    DenotationClaim,
    assemble_subject,
)
from atlas.validation.denotation.concordance import subject_verdicts
from atlas.validation.denotation.relations import scopes_comparable
from atlas.validation.denotation.vedic_denotation_bphs import (
    canonical_dictionary,
)
from atlas.validation.denotation.vedic_transits import (
    VedicTransitError,
    house_from_moon,
    transit_claims,
)


def test_house_from_moon_counts_from_the_moon_sign() -> None:
    """The Moon's own sign is the 1st house; counting is zodiacal."""
    assert house_from_moon(5, 5) == 1        # same sign -> 1st
    assert house_from_moon(6, 5) == 2        # next sign -> 2nd
    assert house_from_moon(4, 5) == 12       # previous sign -> 12th
    assert house_from_moon(5, 8) == 10       # wraps around the zodiac


def test_house_from_moon_rejects_out_of_range() -> None:
    """Signs are 1..12."""
    with pytest.raises(VedicTransitError):
        house_from_moon(13, 5)


def test_transit_claims_take_karakatva_placement_and_gochara_polarity() -> None:
    """Axis/coordinate come from BPHS karakatva; polarity from Phaladipika.

    Natal Moon in Aries (1). Saturn transiting Gemini (3) is in the 3rd from the
    Moon -- an auspicious gochara house for Saturn -- so its contraction is
    benefic; Mars transiting Taurus (2) is in the 2nd, not auspicious, so its
    conflict is malefic.
    """
    dictionary = canonical_dictionary()

    claims = transit_claims(
        {"saturn": 3, "mars": 2},
        natal_moon_sign=1,
        dictionary=dictionary,
        subject_id="s1",
        when="2026-07-27",
    )

    by_axis = {(c.axis, c.value): c for c in claims}

    saturn = by_axis[("dynamic", "contraction")]
    mars = by_axis[("domain", "conflict")]

    for claim in claims:
        assert claim.system == "vedic"
        assert claim.temporal_scope == "transit-2026-07-27"
        assert "gochara_house_from_moon=" in claim.source_basis

    # Saturn in its auspicious 3rd -> positive; Mars in the 2nd -> negative.
    assert saturn.polarity == "positive"
    assert saturn.source_basis.endswith("=3")
    assert mars.polarity == "negative"
    assert mars.source_basis.endswith("=2")


def test_same_graha_flips_polarity_by_gochara_house() -> None:
    """The gochara payoff: one graha, opposite quality by house from the Moon."""
    dictionary = canonical_dictionary()

    def saturn_polarity(transit_sign: int) -> str:
        (claim,) = transit_claims(
            {"saturn": transit_sign},
            natal_moon_sign=1,
            dictionary=dictionary,
            subject_id="s",
            when="t",
        )
        return claim.polarity

    assert saturn_polarity(3) == "positive"   # 3rd from Moon: auspicious
    assert saturn_polarity(1) == "negative"   # 1st from Moon: malefic


def test_transit_needs_a_when_label() -> None:
    """A transit is at a time; the scope must name it."""
    with pytest.raises(VedicTransitError):
        transit_claims(
            {"sun": 1},
            natal_moon_sign=1,
            dictionary=canonical_dictionary(),
            subject_id="s1",
            when="",
        )


def test_transit_and_natal_scopes_are_not_comparable() -> None:
    """A transit claim cannot be compared to a natal one -- no pollution.

    The framework reserves transit<->transit and event<->event but not
    natal<->transit, so assembling a subject with a Vedic transit claim and a
    Kamea natal claim yields a not-comparable verdict, never a false agreement.
    """
    assert scopes_comparable("transit", "transit")
    assert not scopes_comparable("natal", "transit")

    dictionary = canonical_dictionary()
    (vedic_transit,) = transit_claims(
        {"sun": 1},
        natal_moon_sign=1,
        dictionary=dictionary,
        subject_id="s1",
        when="2026-07-27",
    )
    kamea_natal = DenotationClaim(
        system="kamea",
        subject_id="s1",
        axis="domain",
        value="agency",
        polarity="neutral",
        temporal_scope="natal",
        mapping_kind="direct",
        confidence=0.9,
        source_basis="kamea:measured",
    )

    subject = assemble_subject(
        "s1", {"vedic": [vedic_transit], "kamea": [kamea_natal]}
    )

    for verdict in subject_verdicts(subject):
        assert not verdict.agrees
