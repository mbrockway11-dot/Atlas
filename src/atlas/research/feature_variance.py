"""Feature variance audit for Atlas research matrices."""

from __future__ import annotations

from statistics import mean, pvariance, pstdev
from typing import Any


AUDIT_FEATURES = [
    "node_coverage",
    "density",
    "entropy",
    "axis_strength",
    "unique_nodes",
    "unique_edges",
    "max_node_weight",
    "max_depth",
    "self_loops",
    "profile_node_persistence_ratio",
    "profile_edge_persistence_ratio",
]


def build_feature_variance_audit(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Audit feature variance across a research matrix."""
    audit_rows = []

    for feature in AUDIT_FEATURES:
        values = [
            float(row[feature])
            for row in rows
            if feature in row
        ]

        if not values:
            continue

        variance = pvariance(values) if len(values) > 1 else 0.0
        std = pstdev(values) if len(values) > 1 else 0.0

        audit_rows.append(
            {
                "feature": feature,
                "count": len(values),
                "mean": mean(values),
                "std": std,
                "variance": variance,
                "minimum": min(values),
                "maximum": max(values),
                "range": max(values) - min(values),
                "variance_class": classify_variance(std),
            }
        )

    return sorted(
        audit_rows,
        key=lambda row: row["std"],
        reverse=True,
    )


def classify_variance(std: float) -> str:
    """Classify feature variance from standard deviation."""
    if std >= 2.0:
        return "very_high"

    if std >= 0.75:
        return "high"

    if std >= 0.25:
        return "medium"

    if std > 0.0:
        return "low"

    return "none"