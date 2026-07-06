
"""Discovery correlation scanner."""

from __future__ import annotations

import math
from typing import Any


def scan_correlations(
    records: list[dict[str, Any]],
    questions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Scan records for question correlations."""
    results = []

    for question in questions:
        if question.get("kind") != "numeric_correlation":
            continue

        rows = extract_numeric_pairs(
            records,
            question.get("x_field", ""),
            question.get("y_field", ""),
        )

        result = build_correlation_result(question, rows)
        results.append(result)

    return results


def extract_numeric_pairs(
    records: list[dict[str, Any]],
    x_field: str,
    y_field: str,
) -> list[dict[str, Any]]:
    """Extract numeric x/y pairs from records."""
    rows = []

    for record in records:
        x_value = read_path(record, x_field)
        y_value = read_path(record, y_field)

        if x_value is None or y_value is None:
            continue

        try:
            x = float(x_value)
            y = float(y_value)
        except Exception:
            continue

        rows.append(
            {
                "profile_key": record.get("profile_key"),
                "x": x,
                "y": y,
            }
        )

    return rows


def build_correlation_result(
    question: dict[str, Any],
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build one correlation result."""
    coefficient = pearson(
        [row["x"] for row in rows],
        [row["y"] for row in rows],
    )

    return {
        "question_id": question.get("question_id"),
        "question": question.get("question"),
        "kind": question.get("kind"),
        "x_field": question.get("x_field"),
        "y_field": question.get("y_field"),
        "sample_size": len(rows),
        "correlation": coefficient,
        "strength": correlation_strength(coefficient, len(rows)),
        "direction": correlation_direction(coefficient),
        "supporting_rows": sorted(
            rows,
            key=lambda item: abs(item.get("x", 0.0) * item.get("y", 0.0)),
            reverse=True,
        )[:20],
    }


def pearson(xs: list[float], ys: list[float]) -> float:
    """Compute Pearson correlation."""
    if len(xs) < 2 or len(xs) != len(ys):
        return 0.0

    mean_x = sum(xs) / len(xs)
    mean_y = sum(ys) / len(ys)

    numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    denom_x = math.sqrt(sum((x - mean_x) ** 2 for x in xs))
    denom_y = math.sqrt(sum((y - mean_y) ** 2 for y in ys))

    denominator = denom_x * denom_y

    if denominator == 0:
        return 0.0

    return round(numerator / denominator, 6)


def correlation_strength(value: float, sample_size: int) -> str:
    """Label correlation strength."""
    absolute = abs(value)

    if sample_size < 5:
        return "insufficient_sample"

    if absolute >= 0.70:
        return "strong"
    if absolute >= 0.45:
        return "moderate"
    if absolute >= 0.25:
        return "weak"
    return "minimal"


def correlation_direction(value: float) -> str:
    """Label correlation direction."""
    if value > 0.05:
        return "positive"
    if value < -0.05:
        return "negative"
    return "neutral"


def read_path(source: dict[str, Any], path: str) -> Any:
    """Read dotted path from nested dict."""
    value: Any = source

    for part in path.split("."):
        if not isinstance(value, dict):
            return None
        value = value.get(part)

    return value
