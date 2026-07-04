"""Planetary knowledge definitions for Atlas dossier."""

from __future__ import annotations

from typing import Any


PLANET_DEFINITIONS: dict[str, dict[str, Any]] = {
    "sun": {
        "symbol": "☉",
        "name": "Sun",
        "domain": "Identity & Purpose",
        "represents": (
            "The Sun represents conscious identity, vitality, creative expression, "
            "purpose, confidence, and the organizing principle of the self."
        ),
        "structural_question": "How does this person seek to express purpose and identity?",
        "keywords": ["purpose", "vitality", "confidence", "creative will", "identity"],
    },
    "moon": {
        "symbol": "☾",
        "name": "Moon",
        "domain": "Emotional Processing",
        "represents": (
            "The Moon represents emotional memory, instinctive response, internal "
            "security, attachment patterns, and unconscious regulation."
        ),
        "structural_question": "How does this person process emotion and seek internal safety?",
        "keywords": ["emotion", "memory", "instinct", "security", "attachment"],
    },
    "mercury": {
        "symbol": "☿",
        "name": "Mercury",
        "domain": "Cognition & Communication",
        "represents": (
            "Mercury represents learning, language, reasoning, communication, memory, "
            "analysis, and information processing."
        ),
        "structural_question": "How does this person think, learn, speak, and organize information?",
        "keywords": ["thinking", "communication", "learning", "analysis", "language"],
    },
    "venus": {
        "symbol": "♀",
        "name": "Venus",
        "domain": "Relationships & Values",
        "represents": (
            "Venus represents attraction, values, harmony, beauty, relational style, "
            "pleasure, attachment, and aesthetic preference."
        ),
        "structural_question": "How does this person form bonds, value beauty, and seek harmony?",
        "keywords": ["values", "relationships", "beauty", "harmony", "attachment"],
    },
    "mars": {
        "symbol": "♂",
        "name": "Mars",
        "domain": "Action & Drive",
        "represents": (
            "Mars represents initiative, assertion, conflict, courage, physical drive, "
            "motivation, and how energy becomes action."
        ),
        "structural_question": "How does this person act, confront resistance, and pursue goals?",
        "keywords": ["action", "drive", "conflict", "initiative", "courage"],
    },
    "jupiter": {
        "symbol": "♃",
        "name": "Jupiter",
        "domain": "Growth & Wisdom",
        "represents": (
            "Jupiter represents expansion, wisdom, teaching, belief systems, meaning, "
            "optimism, guidance, and the search for broader truth."
        ),
        "structural_question": "How does this person expand understanding and build meaning?",
        "keywords": ["growth", "wisdom", "belief", "teaching", "meaning"],
    },
    "saturn": {
        "symbol": "♄",
        "name": "Saturn",
        "domain": "Discipline & Structure",
        "represents": (
            "Saturn represents discipline, limits, responsibility, mastery, time, "
            "structure, patience, consequences, and long-range development."
        ),
        "structural_question": "How does this person meet responsibility, limitation, and mastery?",
        "keywords": ["discipline", "structure", "time", "limits", "mastery"],
    },
    "rahu": {
        "symbol": "☊",
        "name": "Rahu",
        "domain": "Evolutionary Direction",
        "represents": (
            "Rahu represents hunger for growth, future direction, novelty, obsession, "
            "amplification, and the unfamiliar territory the profile is pulled toward."
        ),
        "structural_question": "Where is this person being pulled toward growth and unfamiliar experience?",
        "keywords": ["growth edge", "future", "amplification", "desire", "novelty"],
    },
    "ketu": {
        "symbol": "☋",
        "name": "Ketu",
        "domain": "Inherited Tendencies",
        "represents": (
            "Ketu represents inherited mastery, detachment, past tendencies, instinctive "
            "competence, spiritual separation, and what the profile already knows too well."
        ),
        "structural_question": "What does this person already carry, know, or detach from instinctively?",
        "keywords": ["past mastery", "detachment", "inheritance", "instinct", "release"],
    },
}


PLANET_ORDER = [
    "sun",
    "moon",
    "mercury",
    "venus",
    "mars",
    "jupiter",
    "saturn",
    "rahu",
    "ketu",
]


ALIASES = {
    "surya": "sun",
    "chandra": "moon",
    "budha": "mercury",
    "shukra": "venus",
    "mangal": "mars",
    "kuja": "mars",
    "guru": "jupiter",
    "brihaspati": "jupiter",
    "shani": "saturn",
    "north node": "rahu",
    "south node": "ketu",
}


def normalize_planet_key(value: str) -> str:
    """Normalize planet key."""
    key = str(value or "").strip().lower().replace("_", " ")
    return ALIASES.get(key, key.replace(" ", "_"))


def get_planet_definition(value: str) -> dict[str, Any]:
    """Return planet definition."""
    key = normalize_planet_key(value)
    return PLANET_DEFINITIONS.get(
        key,
        {
            "symbol": "○",
            "name": str(value).title(),
            "domain": "Planetary Factor",
            "represents": "This planetary factor is available in the compiled temporal layer.",
            "structural_question": "How does this factor contribute to the profile?",
            "keywords": [],
        },
    )
