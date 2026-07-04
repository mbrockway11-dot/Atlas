"""Vedic house knowledge definitions for Atlas."""

from __future__ import annotations

from typing import Any


HOUSES: dict[int, dict[str, Any]] = {
    1: {"name": "1st House", "domain": "Self & Embodiment", "description": "The 1st house represents body, identity, appearance, vitality, self-orientation, and how the person enters life directly."},
    2: {"name": "2nd House", "domain": "Resources & Speech", "description": "The 2nd house represents speech, family resources, values, food, money, memory, and accumulated support."},
    3: {"name": "3rd House", "domain": "Effort & Communication", "description": "The 3rd house represents courage, effort, siblings, communication, skill-building, hands, practice, and self-initiated movement."},
    4: {"name": "4th House", "domain": "Home & Inner Foundation", "description": "The 4th house represents home, mother, emotional foundation, private life, land, vehicles, and inner security."},
    5: {"name": "5th House", "domain": "Creativity & Intelligence", "description": "The 5th house represents creativity, children, education, romance, performance, mantra, intelligence, and self-expression."},
    6: {"name": "6th House", "domain": "Work & Challenge", "description": "The 6th house represents work, service, health, competition, conflict resolution, discipline, enemies, and daily effort."},
    7: {"name": "7th House", "domain": "Partnership & Exchange", "description": "The 7th house represents marriage, partnership, contracts, public interaction, clients, negotiation, and direct others."},
    8: {"name": "8th House", "domain": "Transformation & Hidden Forces", "description": "The 8th house represents transformation, secrets, inheritance, vulnerability, occult knowledge, crisis, and psychological depth."},
    9: {"name": "9th House", "domain": "Wisdom & Dharma", "description": "The 9th house represents dharma, teachers, philosophy, religion, higher learning, father, fortune, and guiding meaning."},
    10: {"name": "10th House", "domain": "Career & Public Action", "description": "The 10th house represents career, public reputation, authority, action in the world, responsibility, and visible contribution."},
    11: {"name": "11th House", "domain": "Networks & Gains", "description": "The 11th house represents gains, communities, networks, aspirations, large groups, friends, and realized ambitions."},
    12: {"name": "12th House", "domain": "Release & Transcendence", "description": "The 12th house represents retreat, loss, sleep, foreign lands, isolation, liberation, expenditure, and spiritual dissolution."},
}


def normalize_house(value: Any) -> int | None:
    """Normalize house value."""
    if value in (None, ""):
        return None

    try:
        text = str(value).strip().lower().replace("house", "").replace("st", "").replace("nd", "").replace("rd", "").replace("th", "")
        number = int(text)
        if 1 <= number <= 12:
            return number
    except ValueError:
        return None

    return None


def get_house(value: Any) -> dict[str, Any]:
    """Return house knowledge record."""
    house = normalize_house(value)
    if house is None:
        return {
            "name": "Unknown House",
            "domain": "",
            "description": "House placement is not available in the current canonical payload.",
        }

    return HOUSES[house]
