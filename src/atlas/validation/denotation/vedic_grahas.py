"""The nine grahas, and the one subject-varying quantity v1 computes.

This is the Vedic expression layer, the analogue of ``numerology_expression``:
it knows the frozen vocabulary of grahas and how to compute one quantity from a
subject, and it knows nothing about the shared ontology. What a graha *means* is
a sourced denotation compiled elsewhere; this module only says which grahas
exist and, for a birth moment, which graha rules the ascendant.

The ascendant's *sign* is sidereal, so it depends on the ayanamsa -- and only
the Lahiri ayanamsa is admitted (1E-V-SOURCE-A). Computing the lagna lord here
therefore consumes the one licensed sidereal choice, which is exactly why the
ayanamsa acquisition had to come first.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VEDIC_GRAHAS_VERSION = "1.0.0"


# The nine grahas of classical Jyotisa. Rahu and Ketu are the lunar nodes; they
# rule no sign, so a lagna lord is always one of the seven star-planets.
GRAHAS: tuple[str, ...] = (
    "sun",
    "moon",
    "mars",
    "mercury",
    "jupiter",
    "venus",
    "saturn",
    "rahu",
    "ketu",
)

GRAHA_SANSKRIT: dict[str, str] = {
    "sun": "Surya",
    "moon": "Chandra",
    "mars": "Mangala",
    "mercury": "Budha",
    "jupiter": "Guru",
    "venus": "Shukra",
    "saturn": "Shani",
    "rahu": "Rahu",
    "ketu": "Ketu",
}


# Classical sign rulerships (Meshadi order, signs 1-12). Fixed here as the
# frozen convention this expression uses; nodes are omitted because they rule no
# rasi. A denotation keyed to a graha applies wherever that graha is named,
# whether reached through the lagna lord or another selector added later.
SIGN_RULERS: dict[int, str] = {
    1: "mars",       # Mesha (Aries)
    2: "venus",      # Vrishabha (Taurus)
    3: "mercury",    # Mithuna (Gemini)
    4: "moon",       # Karka (Cancer)
    5: "sun",        # Simha (Leo)
    6: "mercury",    # Kanya (Virgo)
    7: "venus",      # Tula (Libra)
    8: "mars",       # Vrishchika (Scorpio)
    9: "jupiter",    # Dhanu (Sagittarius)
    10: "saturn",    # Makara (Capricorn)
    11: "saturn",    # Kumbha (Aquarius)
    12: "jupiter",   # Meena (Pisces)
}

# The quantity a subject expresses in v1: the graha ruling the sidereal
# ascendant sign. Named so a later selector (atmakaraka, a graha's own
# placement) is a different quantity rather than an edit to this one.
LAGNA_LORD = "lagna_lord"

COMPUTABLE_QUANTITIES: tuple[str, ...] = (LAGNA_LORD,)

# A denotation of a graha's own nature (karakatva), independent of the quantity
# through which the graha was reached -- the Vedic analogue of numerology's
# VALUE_ITSELF. The Sun signifies the same whether it rules the lagna or is
# selected another way, so a karakatva passage keys to this sentinel and applies
# wherever the graha is named.
GRAHA_ITSELF = "graha_itself"


class VedicExpressionError(ValueError):
    """A Vedic quantity could not be computed as specified."""


@dataclass(frozen=True, slots=True)
class VedicExpression:
    """One computed Vedic quantity for a subject: a graha, and how it was reached."""

    quantity: str
    graha: str
    ascendant_sign: int
    ayanamsa_scheme: str

    def __post_init__(self) -> None:
        if self.graha not in GRAHAS:
            raise VedicExpressionError(f"{self.graha!r} is not a graha.")

        if not 1 <= self.ascendant_sign <= 12:
            raise VedicExpressionError(
                "ascendant sign must lie in 1..12."
            )

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "quantity": self.quantity,
            "graha": self.graha,
            "ascendant_sign": self.ascendant_sign,
            "ayanamsa_scheme": self.ayanamsa_scheme,
            "version": VEDIC_GRAHAS_VERSION,
        }


def sidereal_sign_of_longitude(sidereal_longitude: float) -> int:
    """Return the 1..12 rasi a sidereal ecliptic longitude falls in."""
    normalized = sidereal_longitude % 360.0

    return int(normalized // 30.0) + 1


def lagna_lord_expression(
    sidereal_ascendant_longitude: float,
    *,
    ayanamsa_scheme: str = "lahiri",
) -> VedicExpression:
    """Return the lagna-lord quantity from a sidereal ascendant longitude.

    The ascendant longitude must already be sidereal -- offset by an admitted
    ayanamsa. The scheme is recorded on the expression so a quantity computed
    under an unlicensed ayanamsa cannot be mistaken for a licensed one.
    """
    sign = sidereal_sign_of_longitude(sidereal_ascendant_longitude)

    return VedicExpression(
        quantity=LAGNA_LORD,
        graha=SIGN_RULERS[sign],
        ascendant_sign=sign,
        ayanamsa_scheme=ayanamsa_scheme,
    )
