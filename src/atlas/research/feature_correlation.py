"""Feature correlation audit for Atlas research matrices."""

from __future__ import annotations

from math import sqrt
from typing import Any

from atlas.research.feature_variance import AUDIT_FEATURES


def build_feature_correlation_audit(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build pairwise feature correlation audit."""
    audit_rows = []

    for index_a, feature_a in enumerate(AUDIT_FEATURES):
        for feature_b in AUDIT_FEATURES[index_a + 1:]:
            paired = [
                (
                    float(row[feature_a]),
                    float(row[feature_b]),
                )
                for row in rows
                if feature_a in row and feature_b in row
            ]

            if len(paired) < 2:
                continue

            values_a = [item[0] for item in paired]
            values_b = [item[1] for item in paired]

            correlation = pearson_correlation(values_a, values_b)

            audit_rows.append(
                {
                    "feature_a": feature_a,
                    "feature_b": feature_b,
                    "correlation": correlation,
                    "absolute_correlation": abs(correlation),
                    "correlation_class": classify_correlation(correlation),
                    "sample_size": len(paired),
                }
            )

    return sorted(
        audit_rows,
        key=lambda row: row["absolute_correlation"],
        reverse=True,
    )


def pearson_correlation(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Compute Pearson correlation."""
    if len(values_a) != len(values_b):
        raise ValueError("Correlation inputs must have the same length.")

    if len(values_a) < 2:
        return 0.0

    mean_a = sum(values_a) / len(values_a)
    mean_b = sum(values_b) / len(values_b)

    numerator = sum(
        (a - mean_a) * (b - mean_b)
        for a, b in zip(values_a, values_b)
    )

    denominator_a = sqrt(
        sum((a - mean_a) ** 2 for a in values_a)
    )
    denominator_b = sqrt(
        sum((b - mean_b) ** 2 for b in values_b)
    )

    denominator = denominator_a * denominator_b

    if denominator == 0:
        return 0.0

    return numerator / denominator


def classify_correlation(correlation: float) -> str:
    """Classify absolute correlation strength."""
    absolute = abs(correlation)

    if absolute >= 0.95:
        return "near_duplicate"

    if absolute >= 0.80:
        return "very_strong"

    if absolute >= 0.60:
        return "strong"

    if absolute >= 0.40:
        return "moderate"

    if absolute >= 0.20:
        return "weak"

    return "minimal"