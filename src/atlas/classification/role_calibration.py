"""Functional Role v2 calibration.

This module estimates which metrics are most useful for separating
Functional Role v2 classes across a research matrix.

It does not mutate the classifier. It produces calibration reports that can
later be used to update or validate role weights.
"""

from __future__ import annotations

from statistics import mean, pvariance
from typing import Any

from atlas.classification.functional_role_v2 import (
    ROLE_NAMES,
    classify_functional_role_v2,
)


CALIBRATION_METRICS = [
    "axis_strength",
    "hub_ratio",
    "articulation_ratio",
    "density",
    "mean_node_coherence",
    "mean_edge_coherence",
    "graph_coherence",
    "core_survival_score",
    "topology_stability",
    "entropy",
    "node_coverage",
    "bridge_ratio",
    "peripheral_node_ratio",
    "attractor_stability",
    "reduction_entropy",
    "edge_survival_auc",
    "node_survival_auc",
    "collapse_slope",
    "core_node_ratio",
    "core_edge_ratio",
]


def calibrate_functional_roles_v2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a Functional Role v2 calibration report."""
    if not rows:
        return empty_calibration_report()

    classified_rows = [
        {
            "row": row,
            "classification": classify_functional_role_v2(row),
        }
        for row in rows
    ]

    metric_separation = build_metric_separation(classified_rows)
    learned_weights = build_learned_role_weights(classified_rows, metric_separation)
    role_distribution = build_role_distribution(classified_rows)
    drift = detect_role_drift(role_distribution)

    return {
        "valid": True,
        "row_count": len(rows),
        "metric_count": len(metric_separation),
        "role_distribution": role_distribution,
        "metric_separation": metric_separation,
        "learned_weights": learned_weights,
        "drift": drift,
    }


def build_metric_separation(
    classified_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Measure how strongly each metric separates the assigned roles."""
    records = []

    for metric_name in CALIBRATION_METRICS:
        role_groups: dict[str, list[float]] = {
            role: []
            for role in ROLE_NAMES
        }

        all_values = []

        for item in classified_rows:
            row = item["row"]
            role = item["classification"]["primary_role"]

            if metric_name not in row or not is_numeric(row[metric_name]):
                continue

            value = float(row[metric_name])
            role_groups.setdefault(role, [])
            role_groups[role].append(value)
            all_values.append(value)

        if not all_values:
            continue

        populated_groups = [
            values
            for values in role_groups.values()
            if values
        ]

        role_means = [
            mean(values)
            for values in populated_groups
        ]

        between_role_variance = (
            pvariance(role_means)
            if len(role_means) > 1
            else 0.0
        )

        within_role_variances = [
            pvariance(values)
            for values in populated_groups
            if len(values) > 1
        ]

        within_role_variance = (
            mean(within_role_variances)
            if within_role_variances
            else 0.0
        )

        separation_score = safe_ratio(
            between_role_variance,
            within_role_variance + 0.000001,
        )

        records.append(
            {
                "metric": metric_name,
                "count": len(all_values),
                "overall_mean": mean(all_values),
                "overall_variance": (
                    pvariance(all_values)
                    if len(all_values) > 1
                    else 0.0
                ),
                "between_role_variance": between_role_variance,
                "within_role_variance": within_role_variance,
                "separation_score": separation_score,
                "role_means": {
                    role: mean(values) if values else 0.0
                    for role, values in role_groups.items()
                },
            }
        )

    return sorted(
        records,
        key=lambda item: item["separation_score"],
        reverse=True,
    )


def build_learned_role_weights(
    classified_rows: list[dict[str, Any]],
    metric_separation: list[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    """Build role-specific suggested weights from separation scores."""
    separation_by_metric = {
        item["metric"]: item["separation_score"]
        for item in metric_separation
    }

    role_weights: dict[str, list[dict[str, Any]]] = {}

    for role in ROLE_NAMES:
        candidates = []

        for metric_name in CALIBRATION_METRICS:
            values_for_role = []
            values_for_others = []

            for item in classified_rows:
                row = item["row"]
                assigned_role = item["classification"]["primary_role"]

                if metric_name not in row or not is_numeric(row[metric_name]):
                    continue

                value = float(row[metric_name])

                if assigned_role == role:
                    values_for_role.append(value)
                else:
                    values_for_others.append(value)

            if not values_for_role:
                continue

            role_mean = mean(values_for_role)
            other_mean = mean(values_for_others) if values_for_others else 0.0
            directional_advantage = max(0.0, role_mean - other_mean)
            separation = separation_by_metric.get(metric_name, 0.0)

            raw_weight = directional_advantage * separation

            candidates.append(
                {
                    "metric": metric_name,
                    "role_mean": role_mean,
                    "other_mean": other_mean,
                    "directional_advantage": directional_advantage,
                    "separation_score": separation,
                    "raw_weight": raw_weight,
                }
            )

        role_weights[role] = normalize_weight_records(candidates)

    return role_weights


def normalize_weight_records(
    records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Normalize raw weight records so role weights sum to one."""
    if not records:
        return []

    total = sum(record["raw_weight"] for record in records)

    if total == 0:
        even = 1.0 / len(records)

        output = [
            {
                **record,
                "weight": even,
            }
            for record in records
        ]
    else:
        output = [
            {
                **record,
                "weight": record["raw_weight"] / total,
            }
            for record in records
        ]

    return sorted(
        output,
        key=lambda record: record["weight"],
        reverse=True,
    )


def build_role_distribution(
    classified_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build primary role distribution."""
    total = len(classified_rows)

    records = []

    for role in ROLE_NAMES:
        count = len(
            [
                item
                for item in classified_rows
                if item["classification"]["primary_role"] == role
            ]
        )

        records.append(
            {
                "role": role,
                "count": count,
                "ratio": safe_ratio(count, total),
            }
        )

    return records


def detect_role_drift(
    role_distribution: list[dict[str, Any]],
) -> dict[str, Any]:
    """Detect whether one role dominates suspiciously."""
    if not role_distribution:
        return {
            "status": "empty",
            "dominant_role": None,
            "dominant_ratio": 0.0,
            "message": "No role distribution available.",
        }

    dominant = max(
        role_distribution,
        key=lambda item: item["ratio"],
    )

    dominant_ratio = dominant["ratio"]

    if dominant_ratio >= 0.75:
        status = "severe_drift"
        message = (
            f"{dominant['role']} dominates {dominant_ratio:.2%} of rows. "
            "Classifier is likely over-biased."
        )
    elif dominant_ratio >= 0.55:
        status = "moderate_drift"
        message = (
            f"{dominant['role']} dominates {dominant_ratio:.2%} of rows. "
            "Classifier may need calibration."
        )
    else:
        status = "balanced"
        message = "No severe role dominance detected."

    return {
        "status": status,
        "dominant_role": dominant["role"],
        "dominant_ratio": dominant_ratio,
        "message": message,
    }


def empty_calibration_report() -> dict[str, Any]:
    """Return empty calibration report."""
    return {
        "valid": False,
        "row_count": 0,
        "metric_count": 0,
        "role_distribution": [],
        "metric_separation": [],
        "learned_weights": {},
        "drift": {
            "status": "empty",
            "dominant_role": None,
            "dominant_ratio": 0.0,
            "message": "No rows supplied.",
        },
    }


def is_numeric(value: Any) -> bool:
    """Return whether a value can be treated as numeric."""
    if value is None or isinstance(value, bool):
        return False

    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def safe_ratio(numerator: float, denominator: float) -> float:
    """Safely divide two values."""
    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)