"""Atlas aspect knowledge definitions."""

from __future__ import annotations

from typing import Any


ASPECTS: dict[str, dict[str, Any]] = {
    "conjunction": {
        "name": "Conjunction",
        "angle": 0,
        "description": "Two planetary functions combine, intensify, or merge into a shared field of expression.",
        "interpretation": "This can create concentration, fusion, and strong emphasis, but may reduce separation between the planets involved.",
    },
    "opposition": {
        "name": "Opposition",
        "angle": 180,
        "description": "Two planetary functions face one another across a polarity.",
        "interpretation": "This creates tension, awareness, projection, and the need to integrate opposite ends of an axis.",
    },
    "trine": {
        "name": "Trine",
        "angle": 120,
        "description": "Two planetary functions flow together with relative ease.",
        "interpretation": "This supports natural talent, harmony, and effortless exchange, though it may be underused without conscious activation.",
    },
    "square": {
        "name": "Square",
        "angle": 90,
        "description": "Two planetary functions challenge each other through friction and pressure.",
        "interpretation": "This creates development through effort, conflict, and the need to build capacity.",
    },
    "sextile": {
        "name": "Sextile",
        "angle": 60,
        "description": "Two planetary functions cooperate through opportunity and supportive exchange.",
        "interpretation": "This aspect benefits from conscious use and practical engagement.",
    },
    "graha_drishti": {
        "name": "Graha Drishti",
        "angle": None,
        "description": "A Vedic planetary sight or influence cast from one planet to another.",
        "interpretation": "Graha drishti shows where a planet directs attention, pressure, support, or activation.",
    },
    "rahu_ketu_axis": {
        "name": "Rahu-Ketu Axis",
        "angle": 180,
        "description": "The nodal axis linking future appetite and inherited detachment.",
        "interpretation": "This axis describes evolutionary tension between unfamiliar growth and instinctive past mastery.",
    },
}


ALIASES = {
    "conjunct": "conjunction",
    "opp": "opposition",
    "opposite": "opposition",
    "tri": "trine",
    "sqr": "square",
    "squ": "square",
    "sext": "sextile",
    "drishti": "graha_drishti",
    "aspect": "graha_drishti",
    "node axis": "rahu_ketu_axis",
    "nodal axis": "rahu_ketu_axis",
}


def normalize_aspect(value: str) -> str:
    """Normalize aspect name."""
    key = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return ALIASES.get(key, key.replace(" ", "_"))


def get_aspect(value: str) -> dict[str, Any]:
    """Return aspect knowledge."""
    key = normalize_aspect(value)
    return ASPECTS.get(
        key,
        {
            "name": str(value).title(),
            "angle": None,
            "description": "This aspect is present in the compiled temporal layer.",
            "interpretation": "Detailed aspect interpretation has not yet been specialized.",
        },
    )
