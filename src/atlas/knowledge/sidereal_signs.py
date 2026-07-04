"""Sidereal sign knowledge definitions for Atlas."""

from __future__ import annotations

from typing import Any


SIDEREAL_SIGNS: dict[str, dict[str, Any]] = {
    "aries": {
        "name": "Aries",
        "element": "Fire",
        "modality": "Cardinal",
        "ruler": "Mars",
        "core_theme": "initiation, courage, action, emergence, directness",
        "description": (
            "Aries is a cardinal fire sign associated with initiation, courage, direct action, "
            "independence, and the impulse to begin. It tends to express through immediacy, "
            "assertion, and decisive movement."
        ),
        "strengths": ["initiative", "courage", "directness", "momentum"],
        "shadow": ["impatience", "reactivity", "impulsiveness"],
    },
    "taurus": {
        "name": "Taurus",
        "element": "Earth",
        "modality": "Fixed",
        "ruler": "Venus",
        "core_theme": "stability, embodiment, resources, endurance, value",
        "description": (
            "Taurus is a fixed earth sign associated with stability, embodiment, patience, "
            "resources, pleasure, and value preservation. It favors consistency, sensory reality, "
            "and durable growth."
        ),
        "strengths": ["stability", "patience", "resourcefulness", "embodiment"],
        "shadow": ["stubbornness", "resistance to change", "attachment"],
    },
    "gemini": {
        "name": "Gemini",
        "element": "Air",
        "modality": "Mutable",
        "ruler": "Mercury",
        "core_theme": "communication, adaptability, curiosity, information exchange",
        "description": (
            "Gemini is a mutable air sign associated with communication, curiosity, learning, "
            "exchange, flexibility, and movement between ideas."
        ),
        "strengths": ["curiosity", "communication", "adaptability", "mental agility"],
        "shadow": ["scattering", "inconsistency", "surface-level processing"],
    },
    "cancer": {
        "name": "Cancer",
        "element": "Water",
        "modality": "Cardinal",
        "ruler": "Moon",
        "core_theme": "care, memory, protection, belonging, emotional initiation",
        "description": (
            "Cancer is a cardinal water sign associated with emotional intelligence, protection, "
            "memory, care, belonging, home, and the initiation of emotional bonds."
        ),
        "strengths": ["care", "empathy", "memory", "protection"],
        "shadow": ["defensiveness", "emotional retreat", "attachment loops"],
    },
    "leo": {
        "name": "Leo",
        "element": "Fire",
        "modality": "Fixed",
        "ruler": "Sun",
        "core_theme": "creative identity, visibility, leadership, authorship, radiance",
        "description": (
            "Leo is a fixed fire sign associated with creative identity, visibility, leadership, "
            "generosity, authorship, performance, confidence, and the desire to create meaningful impact."
        ),
        "strengths": ["creative expression", "leadership", "confidence", "warmth"],
        "shadow": ["pride", "need for recognition", "dramatic fixation"],
    },
    "virgo": {
        "name": "Virgo",
        "element": "Earth",
        "modality": "Mutable",
        "ruler": "Mercury",
        "core_theme": "refinement, analysis, service, precision, improvement",
        "description": (
            "Virgo is a mutable earth sign associated with refinement, analysis, service, "
            "discernment, improvement, precision, and practical intelligence."
        ),
        "strengths": ["discernment", "precision", "service", "practical analysis"],
        "shadow": ["perfectionism", "criticism", "over-correction"],
    },
    "libra": {
        "name": "Libra",
        "element": "Air",
        "modality": "Cardinal",
        "ruler": "Venus",
        "core_theme": "balance, relationship, harmony, justice, social intelligence",
        "description": (
            "Libra is a cardinal air sign associated with balance, relationship, aesthetics, "
            "justice, diplomacy, harmony, and social coordination."
        ),
        "strengths": ["diplomacy", "balance", "aesthetic judgment", "relational awareness"],
        "shadow": ["indecision", "people-pleasing", "conflict avoidance"],
    },
    "scorpio": {
        "name": "Scorpio",
        "element": "Water",
        "modality": "Fixed",
        "ruler": "Mars",
        "core_theme": "depth, transformation, intensity, secrecy, regeneration",
        "description": (
            "Scorpio is a fixed water sign associated with depth, intensity, transformation, "
            "emotional power, secrecy, regeneration, and the confrontation of hidden forces."
        ),
        "strengths": ["depth", "focus", "resilience", "transformational insight"],
        "shadow": ["control", "suspicion", "emotional fixation"],
    },
    "sagittarius": {
        "name": "Sagittarius",
        "element": "Fire",
        "modality": "Mutable",
        "ruler": "Jupiter",
        "core_theme": "meaning, expansion, exploration, wisdom, truth-seeking",
        "description": (
            "Sagittarius is a mutable fire sign associated with exploration, philosophy, "
            "meaning, teaching, long-range vision, truth-seeking, and expansion."
        ),
        "strengths": ["vision", "teaching", "optimism", "philosophy"],
        "shadow": ["restlessness", "dogmatism", "overextension"],
    },
    "capricorn": {
        "name": "Capricorn",
        "element": "Earth",
        "modality": "Cardinal",
        "ruler": "Saturn",
        "core_theme": "structure, responsibility, ambition, discipline, mastery",
        "description": (
            "Capricorn is a cardinal earth sign associated with structure, responsibility, "
            "discipline, ambition, mastery, endurance, and long-term achievement."
        ),
        "strengths": ["discipline", "strategy", "responsibility", "endurance"],
        "shadow": ["rigidity", "fear of failure", "emotional withholding"],
    },
    "aquarius": {
        "name": "Aquarius",
        "element": "Air",
        "modality": "Fixed",
        "ruler": "Saturn",
        "core_theme": "systems, innovation, networks, abstraction, collective structure",
        "description": (
            "Aquarius is a fixed air sign associated with systems, networks, abstraction, "
            "innovation, collective intelligence, future orientation, and unconventional structure."
        ),
        "strengths": ["systems thinking", "innovation", "objectivity", "network awareness"],
        "shadow": ["detachment", "alienation", "fixed ideology"],
    },
    "pisces": {
        "name": "Pisces",
        "element": "Water",
        "modality": "Mutable",
        "ruler": "Jupiter",
        "core_theme": "imagination, dissolution, compassion, intuition, transcendence",
        "description": (
            "Pisces is a mutable water sign associated with imagination, compassion, intuition, "
            "dreams, dissolution, spiritual sensitivity, and transcendence."
        ),
        "strengths": ["compassion", "imagination", "intuition", "surrender"],
        "shadow": ["escapism", "confusion", "boundary loss"],
    },
}


def normalize_sign_key(value: str) -> str:
    """Normalize sign names."""
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def get_sidereal_sign(value: str) -> dict[str, Any]:
    """Return sidereal sign knowledge record."""
    key = normalize_sign_key(value)
    return SIDEREAL_SIGNS.get(
        key,
        {
            "name": str(value).title() if value else "Unknown Sign",
            "element": "",
            "modality": "",
            "ruler": "",
            "core_theme": "",
            "description": "This sidereal sign is not yet defined in the Atlas knowledge layer.",
            "strengths": [],
            "shadow": [],
        },
    )
