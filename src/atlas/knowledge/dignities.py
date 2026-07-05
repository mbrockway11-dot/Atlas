"""Atlas planetary dignity knowledge definitions."""

from __future__ import annotations

from typing import Any


DIGNITIES: dict[str, dict[str, Any]] = {
    "exalted": {
        "name": "Exalted",
        "description": "The planet operates with heightened clarity, visibility, and functional strength.",
        "interpretation": "This placement often expresses the planet's function with unusual effectiveness, though it may also amplify the planet's themes.",
    },
    "debilitated": {
        "name": "Debilitated",
        "description": "The planet operates in a sign where its function may require refinement, compensation, or conscious development.",
        "interpretation": "This does not mean failure. It indicates that the planetary function may need maturity, support, or deliberate integration.",
    },
    "own_sign": {
        "name": "Own Sign",
        "description": "The planet occupies a sign it rules and therefore has stable access to its own operating principles.",
        "interpretation": "This placement can express the planet's function with coherence, familiarity, and self-sufficiency.",
    },
    "moolatrikona": {
        "name": "Moolatrikona",
        "description": "The planet occupies a highly functional zone close to its essential operating principle.",
        "interpretation": "This is often read as strong, purposeful, and structurally aligned planetary expression.",
    },
    "friendly": {
        "name": "Friendly Sign",
        "description": "The planet occupies a supportive environment.",
        "interpretation": "This placement tends to function with cooperation, ease, and available support.",
    },
    "neutral": {
        "name": "Neutral Sign",
        "description": "The planet occupies an environment that neither strongly supports nor strongly obstructs its function.",
        "interpretation": "This placement is context-dependent and should be read through house, aspects, and the whole chart.",
    },
    "enemy": {
        "name": "Enemy Sign",
        "description": "The planet occupies an environment that may challenge its natural expression.",
        "interpretation": "This placement may require adaptation, discipline, or compensating strengths elsewhere in the chart.",
    },
    "combust": {
        "name": "Combust",
        "description": "The planet is close to the Sun and may have its independent function overwhelmed by solar intensity.",
        "interpretation": "Combustion can indicate pressure, internalization, or a need to separate the planet's function from identity pressure.",
    },
    "retrograde": {
        "name": "Retrograde",
        "description": "The planet appears to move backward from Earth's perspective.",
        "interpretation": "Retrograde motion often internalizes, revises, intensifies, or delays the planet's expression until it is processed more consciously.",
    },
}


ALIASES = {
    "exaltation": "exalted",
    "exalt": "exalted",
    "debilitation": "debilitated",
    "fall": "debilitated",
    "own": "own_sign",
    "own sign": "own_sign",
    "own_sign": "own_sign",
    "moola trikona": "moolatrikona",
    "mula trikona": "moolatrikona",
    "friend": "friendly",
    "friendly sign": "friendly",
    "enemy sign": "enemy",
    "combustion": "combust",
    "retro": "retrograde",
}


def normalize_dignity(value: str) -> str:
    """Normalize dignity name."""
    key = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return ALIASES.get(key, key.replace(" ", "_"))


def get_dignity(value: str) -> dict[str, Any]:
    """Return dignity knowledge."""
    key = normalize_dignity(value)
    return DIGNITIES.get(
        key,
        {
            "name": str(value).title(),
            "description": "This dignity or planetary condition is present in the compiled temporal layer.",
            "interpretation": "Detailed dignity interpretation has not yet been specialized.",
        },
    )
