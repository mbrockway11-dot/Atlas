"""Gochara transit polarity, sourced from Phaladipika (1E-V-SOURCE-C).

The graha karakatva (1E-V-SOURCE-B) gives a transit its axis and coordinate --
*what* is activated. What it did not give is the transit's *quality*: whether a
graha transiting a given house from the Moon is benefic or malefic. BPHS states
that only through the chart-specific Ashtakavarga method, not a fixed table, so
this module sources the quality from a text that does state it as a table:
Mantreswara's Phaladipika, Adhyaya 23 (Gochara).

Phaladipika lists, for each graha, the houses counted from the Moon in which its
transit is auspicious, and closes (Sloka 10) with the rule that fixes the rest:
"Thus have been described the benefic positions; the rest are to be understood
as malefic." So the polarity is total and defined: in an auspicious house,
positive; otherwise, negative.

Every value here was verified against the page image of the V. Subrahmanya
Sastri translation (2nd ed., 1950) and cross-checked with the repository OCR --
a two-method transcription, the OCR having conflated some from-Moon lists with
from-Sun lists that only the page image disambiguates.

This module is source-layer: it returns bare polarity literals and never imports
the ontology, so the transit quality cannot be shaped to the vocabulary it will
be scored in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.validation.denotation.vedic_grahas import GRAHAS


VEDIC_GOCHARA_SCHEMA = "atlas.validation.denotation.vedic-gochara.v1"


# Provenance of the whole table. A digital surrogate (IA scan), recorded as
# such; the date comes from the copy's own dated preface (13 September 1950).
GOCHARA_SOURCE: dict[str, str] = {
    "work": "Phaladipika (Mantreswara)",
    "translator": "V. Subrahmanya Sastri",
    "edition": "2nd Edition, 1950 (Aruna Press, Bangalore)",
    "chapter": "Adhyaya 23 (Gochara), Slokas 3-10, printed pp. 258-261",
    "scan_identifier": "Phaladeepika2ndEd.1950ByVSubrahmanyaSastri",
    "file_hash": "ddaa647bdffd34ec6430583aeff7d9f0eaeb4c43",
    "worldcat_oclc": "459723994",
    "polarity_rule": (
        "Sloka 10: 'Thus have been described the benefic positions; the rest "
        "are to be understood as malefic.'"
    ),
}


class VedicGocharaError(ValueError):
    """A gochara rule or lookup was constructed or used invalidly."""


@dataclass(frozen=True, slots=True)
class GocharaRule:
    """One graha's auspicious transit houses counted from the Moon."""

    graha: str
    auspicious_houses: frozenset[int]
    sloka: str
    printed_page: str
    scan_leaf: str

    def __post_init__(self) -> None:
        if self.graha not in GRAHAS:
            raise VedicGocharaError(f"{self.graha!r} is not a graha.")

        if not self.auspicious_houses <= frozenset(range(1, 13)):
            raise VedicGocharaError("houses must lie in 1..12.")

        if not (self.sloka and self.printed_page):
            raise VedicGocharaError("a gochara rule needs its provenance.")

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "graha": self.graha,
            "auspicious_houses": sorted(self.auspicious_houses),
            "sloka": self.sloka,
            "printed_page": self.printed_page,
            "scan_leaf": self.scan_leaf,
        }


# The seven star-planets' auspicious transit houses from the Moon, verified
# against the page images (leaf in parentheses). The nodes are omitted: they
# never arise as a lagna lord and Phaladipika's Sloka 8-9 gochara is given for
# the seven. Each set is the benefic houses; Sloka 10 makes every other house
# malefic.
GOCHARA_RULES: tuple[GocharaRule, ...] = (
    GocharaRule("sun", frozenset({3, 6, 10, 11}), "Sloka 3", "258", "n294"),
    GocharaRule(
        "moon", frozenset({1, 3, 6, 7, 10, 11}), "Sloka 4", "258", "n294"
    ),
    GocharaRule("mars", frozenset({3, 6, 11}), "Sloka 5", "259", "n295"),
    GocharaRule(
        "mercury",
        frozenset({2, 4, 6, 8, 10, 11}),
        "Sloka 6",
        "259",
        "n295",
    ),
    GocharaRule(
        "jupiter", frozenset({2, 5, 7, 9, 11}), "Sloka 7", "260", "n296"
    ),
    GocharaRule(
        "venus",
        frozenset({1, 2, 3, 4, 5, 8, 9, 11, 12}),
        "Sloka 8",
        "260",
        "n296",
    ),
    GocharaRule("saturn", frozenset({3, 6, 11}), "Sloka 9", "261", "n297"),
)


_RULES_BY_GRAHA: dict[str, GocharaRule] = {
    rule.graha: rule for rule in GOCHARA_RULES
}


def auspicious_houses(graha: str) -> frozenset[int]:
    """Return a graha's auspicious transit houses from the Moon."""
    rule = _RULES_BY_GRAHA.get(graha)

    if rule is None:
        raise VedicGocharaError(
            f"no sourced gochara rule for {graha!r}; the nodes are out of "
            "scope and no rule may be invented."
        )

    return rule.auspicious_houses


def has_gochara(graha: str) -> bool:
    """Return whether a sourced gochara rule exists for a graha."""
    return graha in _RULES_BY_GRAHA


def gochara_polarity(graha: str, house_from_moon: int) -> str:
    """Return the transit polarity: positive if auspicious, else negative.

    Total by Phaladipika's Sloka 10: the listed houses are benefic and every
    other house is malefic, so there is no neutral gochara position.
    """
    if not 1 <= house_from_moon <= 12:
        raise VedicGocharaError("house must lie in 1..12.")

    return (
        "positive"
        if house_from_moon in auspicious_houses(graha)
        else "negative"
    )


def gochara_manifest() -> dict[str, Any]:
    """Return the sourced gochara table with its provenance, for the record."""
    return {
        "schema": VEDIC_GOCHARA_SCHEMA,
        "source": GOCHARA_SOURCE,
        "rules": [rule.to_dict() for rule in GOCHARA_RULES],
    }
