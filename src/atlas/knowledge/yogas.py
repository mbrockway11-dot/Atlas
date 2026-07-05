"""Atlas yoga knowledge definitions."""

from __future__ import annotations

from typing import Any


YOGAS: dict[str, dict[str, Any]] = {
    "gaja_kesari": {
        "name": "Gaja Kesari Yoga",
        "description": "A Jupiter-Moon configuration traditionally associated with wisdom, protection, reputation, and support.",
        "interpretation": "In Atlas, this yoga is read as a support pattern between emotional intelligence and meaning-making capacity.",
    },
    "raja_yoga": {
        "name": "Raja Yoga",
        "description": "A configuration linking dharma and karma houses or their rulers, associated with authority, rise, and purposeful action.",
        "interpretation": "In Atlas, Raja Yoga is treated as a structural alignment between purpose, action, and public expression.",
    },
    "dharma_karma_adhipati": {
        "name": "Dharma Karma Adhipati Yoga",
        "description": "A connection between the 9th and 10th house principles of dharma and karma.",
        "interpretation": "This suggests that meaning and public action may become structurally linked.",
    },
    "viparita_raja_yoga": {
        "name": "Viparita Raja Yoga",
        "description": "A reversal pattern involving difficult houses that may produce strength through adversity.",
        "interpretation": "In Atlas, this is read as resilience emerging from pressure, inversion, or hidden constraints.",
    },
    "neecha_bhanga": {
        "name": "Neecha Bhanga",
        "description": "A cancellation or mitigation of debilitation under certain chart conditions.",
        "interpretation": "This indicates that a weak or challenged planetary function may recover strength through context.",
    },
    "chandra_mangala": {
        "name": "Chandra Mangala Yoga",
        "description": "A Moon-Mars connection associated with initiative, resource generation, and emotional action.",
        "interpretation": "Atlas reads this as an activation bridge between emotion and execution.",
    },
    "budha_aditya": {
        "name": "Budha Aditya Yoga",
        "description": "A Sun-Mercury combination associated with intelligence, communication, administration, and visibility of thought.",
        "interpretation": "Atlas reads this as identity and cognition operating in close conjunction.",
    },
    "shasha": {
        "name": "Shasha Yoga",
        "description": "A Saturn mahapurusha yoga associated with discipline, authority, endurance, and structural mastery.",
        "interpretation": "Atlas reads this as strong Saturnian architecture and long-range capacity.",
    },
    "ruchaka": {
        "name": "Ruchaka Yoga",
        "description": "A Mars mahapurusha yoga associated with courage, force, action, and command.",
        "interpretation": "Atlas reads this as amplified action architecture and assertive execution.",
    },
    "brihat_parashara_placeholder": {
        "name": "General Yoga",
        "description": "A named Vedic yoga detected by the compiler.",
        "interpretation": "Detailed yoga interpretation has not yet been specialized.",
    },
}


ALIASES = {
    "gajakesari": "gaja_kesari",
    "gaja kesari": "gaja_kesari",
    "raja": "raja_yoga",
    "dharma karma": "dharma_karma_adhipati",
    "dharma karma adhipati": "dharma_karma_adhipati",
    "vipareeta raja": "viparita_raja_yoga",
    "viparita": "viparita_raja_yoga",
    "neecha bhanga": "neecha_bhanga",
    "neechabhanga": "neecha_bhanga",
    "chandra mangala": "chandra_mangala",
    "budha aditya": "budha_aditya",
}


def normalize_yoga(value: str) -> str:
    """Normalize yoga name."""
    key = str(value or "").strip().lower().replace("-", " ").replace("_", " ")
    return ALIASES.get(key, key.replace(" ", "_"))


def get_yoga(value: str) -> dict[str, Any]:
    """Return yoga knowledge."""
    key = normalize_yoga(value)
    return YOGAS.get(
        key,
        {
            "name": str(value).title(),
            "description": "This yoga is present in the compiled temporal layer.",
            "interpretation": "Detailed yoga interpretation has not yet been specialized.",
        },
    )
