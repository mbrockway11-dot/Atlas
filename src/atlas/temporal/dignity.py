"""Planetary dignity engine for Atlas Temporal Intelligence."""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.temporal.models import NatalChart


DIGNITY_ENGINE_VERSION = "1.0"

SIGNS = [
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpio",
    "Sagittarius",
    "Capricorn",
    "Aquarius",
    "Pisces",
]


@dataclass(frozen=True)
class PlanetDignity:
    """Computed dignity state for one planet."""

    planet: str
    sign: str

    ruler: str

    own_sign: bool
    exalted: bool
    debilitated: bool
    moolatrikona: bool

    relationship: str

    strength_score: float


@dataclass(frozen=True)
class DignityChart:
    """Complete dignity chart."""

    version: str
    name: str
    dignities: dict[str, PlanetDignity]
    summary: dict[str, Any]

SIGN_RULERS = {
    "Aries": "Mars",
    "Taurus": "Venus",
    "Gemini": "Mercury",
    "Cancer": "Moon",
    "Leo": "Sun",
    "Virgo": "Mercury",
    "Libra": "Venus",
    "Scorpio": "Mars",
    "Sagittarius": "Jupiter",
    "Capricorn": "Saturn",
    "Aquarius": "Saturn",
    "Pisces": "Jupiter",
}

EXALTATION_SIGNS = {
    "Sun": "Aries",
    "Moon": "Taurus",
    "Mars": "Capricorn",
    "Mercury": "Virgo",
    "Jupiter": "Cancer",
    "Venus": "Pisces",
    "Saturn": "Libra",
}

DEBILITATION_SIGNS = {
    "Sun": "Libra",
    "Moon": "Scorpio",
    "Mars": "Cancer",
    "Mercury": "Pisces",
    "Jupiter": "Capricorn",
    "Venus": "Virgo",
    "Saturn": "Aries",
}

OWN_SIGNS = {
    "Sun": {"Leo"},
    "Moon": {"Cancer"},
    "Mars": {"Aries", "Scorpio"},
    "Mercury": {"Gemini", "Virgo"},
    "Jupiter": {"Sagittarius", "Pisces"},
    "Venus": {"Taurus", "Libra"},
    "Saturn": {"Capricorn", "Aquarius"},
}

MOOLATRIKONA_SIGNS = {
    "Sun": "Leo",
    "Moon": "Taurus",
    "Mars": "Aries",
    "Mercury": "Virgo",
    "Jupiter": "Sagittarius",
    "Venus": "Libra",
    "Saturn": "Aquarius",
}

FRIENDS = {
    "Sun": {"Moon", "Mars", "Jupiter"},
    "Moon": {"Sun", "Mercury"},
    "Mars": {"Sun", "Moon", "Jupiter"},
    "Mercury": {"Sun", "Venus"},
    "Jupiter": {"Sun", "Moon", "Mars"},
    "Venus": {"Mercury", "Saturn"},
    "Saturn": {"Mercury", "Venus"},
}

ENEMIES = {
    "Sun": {"Venus", "Saturn"},
    "Moon": set(),
    "Mars": {"Mercury"},
    "Mercury": {"Moon"},
    "Jupiter": {"Mercury", "Venus"},
    "Venus": {"Sun", "Moon"},
    "Saturn": {"Sun", "Moon"},
}

def planetary_relationship(
    planet: str,
    ruler: str,
) -> str:
    """Return friend, neutral, or enemy."""

    if ruler == planet:
        return "own"

    if ruler in FRIENDS.get(planet, set()):
        return "friend"

    if ruler in ENEMIES.get(planet, set()):
        return "enemy"

    return "neutral"

def dignity_strength(
    *,
    exalted: bool,
    own_sign: bool,
    moolatrikona: bool,
    debilitated: bool,
    relationship: str,
) -> float:
    """Simple deterministic dignity score."""

    score = 0.0

    if exalted:
        score += 5.0

    if own_sign:
        score += 4.0

    if moolatrikona:
        score += 4.5

    if debilitated:
        score -= 5.0

    if relationship == "friend":
        score += 1.0

    elif relationship == "enemy":
        score -= 1.0

    return score

def dignity_chart_to_dict(
    chart: DignityChart,
) -> dict[str, Any]:
    return {
        "version": chart.version,
        "name": chart.name,
        "dignities": {
            planet: asdict(dignity)
            for planet, dignity in chart.dignities.items()
        },
        "summary": chart.summary,
    }