"""Vedic transits -- the temporal mode of the graha denotation.

A transit is the same graha evaluated at a *time*, not a new meaning: the
transiting graha's karakatva (already admitted from BPHS, 1E-V-SOURCE-B) placed
at ``temporal_scope="transit-<when>"``. Given a birth Moon sign and the grahas'
sidereal transit signs at a moment, this emits one transit claim per graha,
recording each graha's house counted from the Moon.

The transit's *quality* -- whether a graha transiting a given house from the
Moon is benefic or malefic -- is the gochara polarity, sourced from Phaladipika
(1E-V-SOURCE-C, ``vedic_gochara``). So a transit claim's axis and coordinate
come from the graha karakatva (BPHS) and its polarity from the gochara table
(Phaladipika): the same Saturn transit is contraction/positive in the 3rd from
the Moon and contraction/negative in the 1st.

Transits do not pollute the natal concordance: relations.COMPARABLE_SCOPES
admits transit<->transit and event<->event but not natal<->transit, so a transit
claim is simply not comparable to a natal one. A transit claim therefore has no
comparison partner until another system gains a transit mode, or event-scope
claims are introduced for 1E-B event-linking -- the substrate is laid, its
consumer is not built.
"""

from __future__ import annotations

from typing import Mapping

from atlas.validation.denotation.expressions import DenotationClaim
from atlas.validation.denotation.vedic_denotation import GrahaDictionary
from atlas.validation.denotation.vedic_gochara import (
    gochara_polarity,
    has_gochara,
)
from atlas.validation.denotation.vedic_grahas import GRAHAS


TRANSIT_SCOPE_PREFIX = "transit"


class VedicTransitError(ValueError):
    """A transit could not be computed as specified."""


def house_from_moon(transit_sign: int, natal_moon_sign: int) -> int:
    """Return the 1..12 house a transit sign occupies counted from the Moon.

    The Moon's own sign is the 1st house; counting proceeds zodiacally. This is
    the reference gochara is reckoned from.
    """
    if not (1 <= transit_sign <= 12 and 1 <= natal_moon_sign <= 12):
        raise VedicTransitError("signs must lie in 1..12.")

    return (transit_sign - natal_moon_sign) % 12 + 1


def transit_claims(
    graha_transit_signs: Mapping[str, int],
    natal_moon_sign: int,
    dictionary: GrahaDictionary,
    subject_id: str,
    *,
    when: str,
) -> list[DenotationClaim]:
    """Return one transit claim per denoted graha, at transit temporal scope.

    ``graha_transit_signs`` maps a graha to its sidereal sign (1..12) at the
    moment, computed upstream via swisseph under the admitted Lahiri ayanamsa.
    Each claim takes its axis and coordinate from the graha's sourced karakatva
    (BPHS) and its polarity from the gochara table (Phaladipika), by the graha's
    house from the Moon. A graha with a karakatva but no sourced gochara rule is
    skipped rather than given an invented quality.
    """
    if not when:
        raise VedicTransitError("a transit needs a 'when' label for its scope.")

    scope = f"{TRANSIT_SCOPE_PREFIX}-{when}"
    claims: list[DenotationClaim] = []

    for graha in GRAHAS:
        sign = graha_transit_signs.get(graha)
        if sign is None:
            continue

        entry = dictionary.lookup(graha)
        if entry is None or not has_gochara(graha):
            continue

        house = house_from_moon(sign, natal_moon_sign)

        claims.append(
            DenotationClaim(
                system="vedic",
                subject_id=subject_id,
                axis=entry.axis,
                value=entry.coordinate,
                # Sourced gochara polarity (Phaladipika), by house from Moon.
                polarity=gochara_polarity(graha, house),
                temporal_scope=scope,
                mapping_kind=entry.mapping_kind,
                confidence=entry.confidence,
                source_basis=(
                    f"{entry.tradition}:{entry.source_passage_id}:"
                    f"gochara_house_from_moon={house}"
                ),
            )
        )

    return claims
