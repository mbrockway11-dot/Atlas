
"""Causal candidate scanner."""

from __future__ import annotations

import math
from typing import Any


def scan_causal_candidates(
    records: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Scan records for candidate causal evidence."""
    results = []

    for candidate in candidates:
        rows = extract_pairs(records, candidate.get("cause", ""), candidate.get("effect", ""))
        correlation = pearson(
            [row["cause_value"] for row in rows],
            [row["effect_value"] for row in rows],
        )

        results.append(
            {
                "candidate_id": candidate.get("candidate_id"),
                "claim": candidate.get("claim"),
                "mechanism": candidate.get("mechanism"),
                "cause": candidate.get("cause"),
                "effect": candidate.get("effect"),
                "sample_size": len(rows),
                "correlation": correlation,
                "direction": direction(correlation),
                "strength": strength(correlation, len(rows)),
                "rows": rows[:50],
            }
        )

    return results


def extract_pairs(records: list[dict[str, Any]], cause_path: str, effect_path: str) -> list[dict[str, Any]]:
    """Extract numeric cause/effect pairs."""
    rows = []

    for record in records:
        cause = read_path(record, cause_path)
        effect = read_path(record, effect_path)

        try:
            cause_value = float(cause)
            effect_value = float(effect)
        except Exception:
            continue

        rows.append(
            {
                "profile_key": record.get("profile_key"),
                "cause_value": cause_value,
                "effect_value": effect_value,
            }
        )

    return rows


def pearson(xs: list[float], ys: list[float]) -> float:
    """Compute Pearson correlation."""
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0

    mx = sum(xs) / len(xs)
    my = sum(ys) / len(ys)

    numerator = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    dx = math.sqrt(sum((x - mx) ** 2 for x in xs))
    dy = math.sqrt(sum((y - my) ** 2 for y in ys))

    if dx * dy == 0:
        return 0.0

    return round(numerator / (dx * dy), 6)


def direction(value: float) -> str:
    """Correlation direction."""
    if value > 0.05:
        return "positive"
    if value < -0.05:
        return "negative"
    return "neutral"


def strength(value: float, sample_size: int) -> str:
    """Correlation strength."""
    if sample_size < 20:
        return "insufficient_sample"

    absolute = abs(value)

    if absolute >= 0.70:
        return "strong"
    if absolute >= 0.45:
        return "moderate"
    if absolute >= 0.25:
        return "weak"
    return "minimal"


def read_path(source: dict[str, Any], path: str) -> Any:
    """Read dotted path."""
    value: Any = source

    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)

    return value
