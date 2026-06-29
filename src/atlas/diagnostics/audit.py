"""Research matrix diagnostic audit."""

from __future__ import annotations

from statistics import mean, median, pvariance, pstdev
from typing import Any


NUMERIC_EXCLUDED_COLUMNS = [
    "name",
    "cipher",
    "planet",
    "kamea",
    "subtype_primary",
    "subtype_secondary",
]


def audit_research_matrix(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit all numeric metrics in a research matrix."""
    if not rows:
        return {
            "valid": False,
            "row_count": 0,
            "metric_count": 0,
            "metrics": [],
        }

    columns = numeric_columns(rows)

    metrics = [
        audit_metric(rows, column)
        for column in columns
    ]

    metrics = sorted(
        metrics,
        key=lambda item: (
            item["quality_rank"],
            item["std"],
            item["unique_value_count"],
        ),
        reverse=True,
    )

    return {
        "valid": True,
        "row_count": len(rows),
        "metric_count": len(metrics),
        "metrics": metrics,
    }


def numeric_columns(rows: list[dict[str, Any]]) -> list[str]:
    """Return columns that can be safely treated as numeric metrics."""
    if not rows:
        return []

    columns = sorted(
        {
            column
            for row in rows
            for column in row
        }
    )

    output = []

    for column in columns:
        if column in NUMERIC_EXCLUDED_COLUMNS:
            continue

        values = [
            row.get(column)
            for row in rows
            if column in row
        ]

        if values and all(is_numeric(value) for value in values):
            output.append(column)

    return output


def audit_metric(
    rows: list[dict[str, Any]],
    metric: str,
) -> dict[str, Any]:
    """Audit one numeric metric across research rows."""
    values = [
        float(row[metric])
        for row in rows
        if metric in row and is_numeric(row[metric])
    ]

    row_count = len(rows)
    value_count = len(values)
    null_count = row_count - value_count

    if not values:
        return empty_metric_audit(metric, row_count)

    unique_values = sorted(set(values))
    metric_mean = mean(values)
    metric_median = median(values)
    metric_std = pstdev(values) if len(values) > 1 else 0.0
    metric_variance = pvariance(values) if len(values) > 1 else 0.0
    metric_min = min(values)
    metric_max = max(values)
    metric_range = metric_max - metric_min

    constant_ratio = most_common_ratio(values)
    coefficient_of_variation = (
        metric_std / abs(metric_mean)
        if metric_mean != 0
        else 0.0
    )

    quality_rank = score_metric_quality(
        unique_value_count=len(unique_values),
        row_count=value_count,
        std=metric_std,
        value_range=metric_range,
        constant_ratio=constant_ratio,
    )

    return {
        "metric": metric,
        "row_count": row_count,
        "value_count": value_count,
        "null_count": null_count,
        "minimum": metric_min,
        "maximum": metric_max,
        "mean": metric_mean,
        "median": metric_median,
        "std": metric_std,
        "variance": metric_variance,
        "range": metric_range,
        "unique_value_count": len(unique_values),
        "constant_ratio": constant_ratio,
        "coefficient_of_variation": coefficient_of_variation,
        "quality_rank": quality_rank,
        "quality_grade": quality_grade(quality_rank),
        "diagnostic": diagnostic_statement(
            metric=metric,
            unique_value_count=len(unique_values),
            row_count=value_count,
            std=metric_std,
            value_range=metric_range,
            constant_ratio=constant_ratio,
        ),
    }


def empty_metric_audit(metric: str, row_count: int) -> dict[str, Any]:
    """Return empty audit result for a metric with no numeric values."""
    return {
        "metric": metric,
        "row_count": row_count,
        "value_count": 0,
        "null_count": row_count,
        "minimum": None,
        "maximum": None,
        "mean": None,
        "median": None,
        "std": 0.0,
        "variance": 0.0,
        "range": 0.0,
        "unique_value_count": 0,
        "constant_ratio": 1.0,
        "coefficient_of_variation": 0.0,
        "quality_rank": 0.0,
        "quality_grade": "F",
        "diagnostic": "No numeric values available.",
    }


def most_common_ratio(values: list[float]) -> float:
    """Return ratio occupied by the most common value."""
    if not values:
        return 1.0

    counts: dict[float, int] = {}

    for value in values:
        counts[value] = counts.get(value, 0) + 1

    return max(counts.values()) / len(values)


def score_metric_quality(
    *,
    unique_value_count: int,
    row_count: int,
    std: float,
    value_range: float,
    constant_ratio: float,
) -> float:
    """Score how diagnostically useful a metric appears to be."""
    if row_count == 0:
        return 0.0

    uniqueness = unique_value_count / row_count
    variation = 1.0 if std > 0 else 0.0
    spread = 1.0 if value_range > 0 else 0.0
    non_constant = 1.0 - constant_ratio

    score = (
        uniqueness * 0.35
        + variation * 0.20
        + spread * 0.20
        + non_constant * 0.25
    )

    return clamp(score)


def quality_grade(score: float) -> str:
    """Convert quality score to a letter grade."""
    if score >= 0.80:
        return "A"

    if score >= 0.65:
        return "B"

    if score >= 0.50:
        return "C"

    if score >= 0.35:
        return "D"

    return "F"


def diagnostic_statement(
    *,
    metric: str,
    unique_value_count: int,
    row_count: int,
    std: float,
    value_range: float,
    constant_ratio: float,
) -> str:
    """Build plain-language diagnostic statement."""
    if row_count == 0:
        return f"{metric} has no values."

    if unique_value_count <= 1 or value_range == 0:
        return f"{metric} is constant and has little discriminative value."

    if constant_ratio >= 0.90:
        return f"{metric} is highly compressed; most rows share the same value."

    if std == 0:
        return f"{metric} has no measurable variation."

    if unique_value_count / row_count >= 0.75:
        return f"{metric} has strong row-level variation."

    return f"{metric} has moderate diagnostic variation."


def is_numeric(value: Any) -> bool:
    """Return whether a value can be treated as numeric."""
    if value is None:
        return False

    if isinstance(value, bool):
        return False

    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))