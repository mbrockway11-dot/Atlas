
"""Numerology evidence adapter.

Converts birth-date numerology into standardized StructuralEvidence.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from atlas.synthesis.evidence import StructuralEvidence
from atlas.synthesis.adapters.utils import make_record, safe_dict


def collect(payload: dict[str, Any]) -> list[StructuralEvidence]:
    """Collect numerology evidence from birth date."""
    birth = safe_dict(payload.get("birth"))
    birth_date = birth.get("date") or payload.get("birth_date") or ""

    if not birth_date:
        return []

    parsed = parse_date(str(birth_date))

    if not parsed:
        return []

    evidence: list[StructuralEvidence] = []

    life_path = digital_root(sum_digits(parsed.isoformat()))
    day_root = digital_root(parsed.day)
    month_root = digital_root(parsed.month)
    year_root = digital_root(parsed.year)

    evidence.extend(evidence_from_number("numerology.life_path", life_path, 0.78))
    evidence.extend(evidence_from_number("numerology.day", day_root, 0.68))
    evidence.extend(evidence_from_number("numerology.month", month_root, 0.64))
    evidence.extend(evidence_from_number("numerology.year", year_root, 0.62))

    if life_path in {11, 22, 33}:
        evidence.append(make_record("numerology.life_path", "high_impact_signature", life_path, 0.82))

    if len({life_path, day_root, month_root, year_root}) <= 2:
        evidence.append(make_record("numerology.birth_matrix", "reduction_stability", [life_path, day_root, month_root, year_root], 0.78))

    if life_path == day_root:
        evidence.append(make_record("numerology.birth_matrix", "symbolic_coherence", [life_path, day_root], 0.74))

    return evidence


def evidence_from_number(engine: str, number: int, confidence: float) -> list[StructuralEvidence]:
    """Map reduced number to structural evidence."""
    evidence: list[StructuralEvidence] = []

    if number in {1, 4, 8}:
        evidence.append(make_record(engine, "persistent_architecture", number, confidence))

    if number in {2, 6}:
        evidence.append(make_record(engine, "internal_stabilization", number, confidence))

    if number in {3}:
        evidence.append(make_record(engine, "expressive_catalysis", number, confidence))

    if number in {5}:
        evidence.append(make_record(engine, "activation_driven_action", number, confidence))

    if number in {7}:
        evidence.append(make_record(engine, "abstraction_pattern", number, confidence))

    if number in {9}:
        evidence.append(make_record(engine, "transformation_pattern", number, confidence))

    return evidence


def parse_date(value: str) -> date | None:
    """Parse YYYY-MM-DD date safely."""
    try:
        parts = value.strip().split("-")
        if len(parts) != 3:
            return None

        year, month, day = [int(part) for part in parts]
        return date(year, month, day)
    except Exception:
        return None


def sum_digits(value: str) -> int:
    """Sum all digits in a string."""
    return sum(int(char) for char in value if char.isdigit())


def digital_root(value: int) -> int:
    """Compute digital root."""
    value = abs(int(value))
    if value == 0:
        return 0
    return 1 + ((value - 1) % 9)
