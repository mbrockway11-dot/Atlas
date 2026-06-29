"""Canonical Yoga rule definitions for Atlas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


YOGA_RULES_VERSION = "1.0"


# ------------------------------------------------------------
# Rule Components
# ------------------------------------------------------------


@dataclass(frozen=True)
class YogaCondition:
    """One atomic condition inside a Yoga."""

    type: str
    parameters: dict[str, Any]


@dataclass(frozen=True)
class YogaRule:
    """Canonical Yoga definition."""

    name: str

    category: str

    source: str

    description: str

    conditions: tuple[YogaCondition, ...]

    minimum_score: float = 0.0


# ------------------------------------------------------------
# Canonical Yoga Library
# ------------------------------------------------------------

YOGA_RULES: tuple[YogaRule, ...] = (

    YogaRule(
        name="Gaja Kesari Yoga",
        category="Prosperity",
        source="Brihat Parashara Hora Shastra",
        description=(
            "Moon and Jupiter in conjunction or mutual kendra."
        ),
        conditions=(
            YogaCondition(
                "conjunction",
                {
                    "planet_a": "Moon",
                    "planet_b": "Jupiter",
                },
            ),
            YogaCondition(
                "minimum_strength",
                {
                    "planet": "Jupiter",
                    "score": 2.0,
                },
            ),
        ),
    ),

    YogaRule(
        name="Budha Aditya Yoga",
        category="Intelligence",
        source="Classical",
        description=(
            "Sun and Mercury conjunction."
        ),
        conditions=(
            YogaCondition(
                "conjunction",
                {
                    "planet_a": "Sun",
                    "planet_b": "Mercury",
                },
            ),
        ),
    ),

    YogaRule(
        name="Chandra Mangala Yoga",
        category="Wealth",
        source="Classical",
        description=(
            "Moon and Mars conjunction."
        ),
        conditions=(
            YogaCondition(
                "conjunction",
                {
                    "planet_a": "Moon",
                    "planet_b": "Mars",
                },
            ),
        ),
    ),

    YogaRule(
        name="Neecha Bhanga Raja Yoga",
        category="Cancellation",
        source="BPHS",
        description=(
            "Cancellation of debilitation."
        ),
        conditions=(
            YogaCondition(
                "debilitated",
                {
                    "planet": "*",
                },
            ),
            YogaCondition(
                "debilitation_cancelled",
                {
                    "planet": "*",
                },
            ),
        ),
    ),

    YogaRule(
        name="Dharma-Karma Adhipati Yoga",
        category="Raja Yoga",
        source="BPHS",
        description=(
            "Relationship between the 9th and 10th house lords."
        ),
        conditions=(
            YogaCondition(
                "house_lord_relationship",
                {
                    "houses": (9, 10),
                },
            ),
        ),
    ),

    YogaRule(
        name="Vipareeta Raja Yoga",
        category="Raja Yoga",
        source="BPHS",
        description=(
            "Dusthana lords occupying dusthana houses."
        ),
        conditions=(
            YogaCondition(
                "dusthana_exchange",
                {},
            ),
        ),
    ),

    YogaRule(
        name="Pancha Mahapurusha Yoga",
        category="Mahapurusha",
        source="BPHS",
        description=(
            "Mars, Mercury, Jupiter, Venus or Saturn "
            "strong in own/exalted kendra."
        ),
        conditions=(
            YogaCondition(
                "mahapurusha",
                {},
            ),
        ),
    ),

)

# ------------------------------------------------------------
# Lookup
# ------------------------------------------------------------

YOGA_BY_NAME = {
    yoga.name: yoga
    for yoga in YOGA_RULES
}


def get_yoga(
    name: str,
) -> YogaRule:
    """Lookup one Yoga."""

    return YOGA_BY_NAME[name]


def all_yogas() -> tuple[YogaRule, ...]:
    """Return canonical Yoga library."""

    return YOGA_RULES