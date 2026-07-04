"""Atlas planetary knowledge definitions."""

from __future__ import annotations

from typing import Any


PLANETS: dict[str, dict[str, Any]] = {
    "sun": {
        "name": "Sun",
        "symbol": "☉",
        "domain": "Identity & Purpose",
        "represents": (
            "The Sun represents conscious identity, vitality, purpose, confidence, "
            "creative expression, authorship, and the organizing principle of selfhood."
        ),
        "behavioral_function": (
            "It describes where the person seeks visibility, meaning, creative authority, "
            "and a felt sense of personal direction."
        ),
        "strengths": [
            "Purpose",
            "Creative will",
            "Self-expression",
            "Leadership",
            "Vitality",
        ],
        "shadow": [
            "Ego rigidity",
            "Over-identification",
            "Need for recognition",
        ],
    },
    "moon": {
        "name": "Moon",
        "symbol": "☾",
        "domain": "Emotional Processing",
        "represents": (
            "The Moon represents emotional memory, instinctive response, internal security, "
            "nurturing patterns, attachment, and unconscious regulation."
        ),
        "behavioral_function": (
            "It describes how the person processes emotion, seeks safety, reacts under pressure, "
            "and returns to inner equilibrium."
        ),
        "strengths": [
            "Emotional intelligence",
            "Adaptation",
            "Memory",
            "Care",
            "Instinct",
        ],
        "shadow": [
            "Mood reactivity",
            "Attachment loops",
            "Defensive emotional habits",
        ],
    },
    "mercury": {
        "name": "Mercury",
        "symbol": "☿",
        "domain": "Cognition & Communication",
        "represents": (
            "Mercury represents cognition, speech, learning, language, reasoning, analysis, "
            "memory formation, and symbolic processing."
        ),
        "behavioral_function": (
            "It describes how the person thinks, learns, organizes information, makes distinctions, "
            "and communicates ideas."
        ),
        "strengths": [
            "Learning",
            "Communication",
            "Analysis",
            "Language",
            "Adaptability",
        ],
        "shadow": [
            "Overthinking",
            "Nervous fragmentation",
            "Argumentative reasoning",
        ],
    },
    "venus": {
        "name": "Venus",
        "symbol": "♀",
        "domain": "Relationships & Values",
        "represents": (
            "Venus represents attraction, relational style, beauty, harmony, pleasure, values, "
            "attachment, aesthetics, and social bonding."
        ),
        "behavioral_function": (
            "It describes what the person values, how they bond, how they seek pleasure, "
            "and how they create harmony or aesthetic coherence."
        ),
        "strengths": [
            "Harmony",
            "Relational intelligence",
            "Beauty",
            "Values",
            "Attraction",
        ],
        "shadow": [
            "Avoidance of conflict",
            "Over-attachment",
            "Value confusion",
        ],
    },
    "mars": {
        "name": "Mars",
        "symbol": "♂",
        "domain": "Action & Drive",
        "represents": (
            "Mars represents initiative, assertion, conflict, courage, energy, motivation, "
            "competition, and how intention becomes action."
        ),
        "behavioral_function": (
            "It describes how the person acts, pursues goals, responds to resistance, "
            "and expresses force or urgency."
        ),
        "strengths": [
            "Initiative",
            "Courage",
            "Execution",
            "Drive",
            "Decisiveness",
        ],
        "shadow": [
            "Impulsiveness",
            "Conflict escalation",
            "Impatience",
        ],
    },
    "jupiter": {
        "name": "Jupiter",
        "symbol": "♃",
        "domain": "Growth & Wisdom",
        "represents": (
            "Jupiter represents expansion, wisdom, teaching, philosophy, belief, optimism, "
            "meaning, generosity, and the search for broader truth."
        ),
        "behavioral_function": (
            "It describes how the person grows, teaches, learns from experience, finds meaning, "
            "and expands their worldview."
        ),
        "strengths": [
            "Wisdom",
            "Teaching",
            "Meaning",
            "Generosity",
            "Expansion",
        ],
        "shadow": [
            "Overextension",
            "Dogmatism",
            "Excess optimism",
        ],
    },
    "saturn": {
        "name": "Saturn",
        "symbol": "♄",
        "domain": "Discipline & Structure",
        "represents": (
            "Saturn represents discipline, limitation, time, responsibility, mastery, structure, "
            "patience, consequence, and long-range development."
        ),
        "behavioral_function": (
            "It describes how the person meets constraint, develops mastery, carries duty, "
            "and builds durable structures over time."
        ),
        "strengths": [
            "Discipline",
            "Mastery",
            "Responsibility",
            "Endurance",
            "Structure",
        ],
        "shadow": [
            "Fear",
            "Rigidity",
            "Delay",
            "Excess self-criticism",
        ],
    },
    "rahu": {
        "name": "Rahu",
        "symbol": "☊",
        "domain": "Evolutionary Direction",
        "represents": (
            "Rahu represents desire, amplification, unfamiliar growth, obsession, future direction, "
            "novel experience, and the pull toward what has not yet been integrated."
        ),
        "behavioral_function": (
            "It describes where the person is pulled toward growth, novelty, hunger, ambition, "
            "and boundary-crossing experience."
        ),
        "strengths": [
            "Innovation",
            "Growth hunger",
            "Experimentation",
            "Future orientation",
        ],
        "shadow": [
            "Obsession",
            "Over-amplification",
            "Restlessness",
        ],
    },
    "ketu": {
        "name": "Ketu",
        "symbol": "☋",
        "domain": "Inherited Tendencies",
        "represents": (
            "Ketu represents inherited mastery, instinctive competence, detachment, past tendencies, "
            "spiritual separation, and what the profile already knows too well."
        ),
        "behavioral_function": (
            "It describes what feels familiar, automatic, detached, mastered, or ready to be released."
        ),
        "strengths": [
            "Instinctive mastery",
            "Detachment",
            "Spiritual insight",
            "Pattern memory",
        ],
        "shadow": [
            "Disconnection",
            "Avoidance",
            "Under-engagement",
        ],
    },
}


PLANET_ALIASES = {
    "surya": "sun",
    "chandra": "moon",
    "budha": "mercury",
    "shukra": "venus",
    "mangal": "mars",
    "kuja": "mars",
    "guru": "jupiter",
    "brihaspati": "jupiter",
    "shani": "saturn",
    "north_node": "rahu",
    "north node": "rahu",
    "south_node": "ketu",
    "south node": "ketu",
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


def normalize_planet_key(value: str) -> str:
    """Normalize planet names and aliases."""
    key = str(value or "").strip().lower().replace("-", "_")
    key = key.replace(" ", "_")
    return PLANET_ALIASES.get(key, key)


def get_planet(value: str) -> dict[str, Any]:
    """Return planet knowledge record."""
    key = normalize_planet_key(value)
    return PLANETS.get(
        key,
        {
            "name": str(value).title(),
            "symbol": "○",
            "domain": "Planetary Factor",
            "represents": "This planetary factor is present in the temporal layer.",
            "behavioral_function": "Atlas has not yet specialized this planetary factor.",
            "strengths": [],
            "shadow": [],
        },
    )



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
    "north_node": "rahu",
    "north node": "rahu",
    "south_node": "ketu",
    "south node": "ketu",
}

def normalize_planet(value: str) -> str:
    """Normalize a planet name."""
    key = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return ALIASES.get(key, key.replace(" ", "_"))
