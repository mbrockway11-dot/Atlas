"""Functional Role v2 diagnostics.

This module audits how Functional Role v2 behaves across a research matrix.
It answers:
- Which roles dominate?
- Which modifiers dominate?
- How confident is the classifier?
- Which metrics are most often used as strongest evidence?
- How much layer consensus exists across each profile?
"""

from __future__ import annotations

from collections import Counter
from statistics import mean
from typing import Any

from atlas.classification.functional_role_v2 import (
    ROLE_NAMES,
    classify_functional_role_v2,
    classify_profile_functional_role_v2,
)


def audit_functional_roles_v2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit Functional Role v2 results across research rows."""
    if not rows:
        return empty_role_diagnostics()

    layer_results = [
        classify_functional_role_v2(row)
        for row in rows
    ]

    grouped = group_rows_by_profile(rows)
    profile_results = {
        name: classify_profile_functional_role_v2(profile_rows)
        for name, profile_rows in grouped.items()
    }

    return {
        "valid": True,
        "row_count": len(rows),
        "profile_count": len(grouped),
        "role_distribution": role_distribution(layer_results),
        "modifier_distribution": modifier_distribution(layer_results),
        "profile_role_distribution": role_distribution(
            list(profile_results.values())
        ),
        "profile_modifier_distribution": modifier_distribution(
            list(profile_results.values())
        ),
        "confidence_summary": confidence_summary(layer_results),
        "profile_confidence_summary": confidence_summary(
            list(profile_results.values())
        ),
        "evidence_metric_distribution": evidence_metric_distribution(layer_results),
        "role_metric_signal": role_metric_signal(rows, layer_results),
        "profile_consensus": profile_consensus(profile_results),
        "profile_results": profile_results,
    }


def group_rows_by_profile(rows: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Group research rows by profile name."""
    grouped: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        name = str(row.get("name", "unknown"))
        grouped.setdefault(name, [])
        grouped[name].append(row)

    return grouped


def role_distribution(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count primary roles."""
    counter = Counter(
        result.get("primary_role", "Unknown")
        for result in results
    )

    total = sum(counter.values())

    return [
        {
            "role": role,
            "count": counter.get(role, 0),
            "ratio": safe_ratio(counter.get(role, 0), total),
        }
        for role in sorted(counter)
    ]


def modifier_distribution(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count modifiers."""
    counter = Counter(
        result.get("modifier", "Unknown")
        for result in results
    )

    total = sum(counter.values())

    return [
        {
            "modifier": modifier,
            "count": counter.get(modifier, 0),
            "ratio": safe_ratio(counter.get(modifier, 0), total),
        }
        for modifier in sorted(counter)
    ]


def confidence_summary(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize classifier confidence."""
    confidences = [
        float(result.get("confidence", 0.0))
        for result in results
    ]

    if not confidences:
        return {
            "mean": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "hybrid_ratio": 0.0,
        }

    hybrids = [
        result
        for result in results
        if result.get("is_hybrid", False)
    ]

    return {
        "mean": mean(confidences),
        "minimum": min(confidences),
        "maximum": max(confidences),
        "hybrid_ratio": safe_ratio(len(hybrids), len(results)),
    }


def evidence_metric_distribution(results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Count strongest evidence metrics."""
    counter = Counter(
        result.get("evidence", {}).get("strongest_metric", "unknown")
        for result in results
    )

    total = sum(counter.values())

    return [
        {
            "metric": metric,
            "count": count,
            "ratio": safe_ratio(count, total),
        }
        for metric, count in counter.most_common()
    ]


def role_metric_signal(
    rows: list[dict[str, Any]],
    results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Estimate average metric values by primary role."""
    records = []

    metrics = [
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
    ]

    paired = list(zip(rows, results))

    for role in ROLE_NAMES:
        role_rows = [
            row
            for row, result in paired
            if result.get("primary_role") == role
        ]

        if not role_rows:
            continue

        for metric in metrics:
            values = [
                float(row[metric])
                for row in role_rows
                if metric in row and is_numeric(row[metric])
            ]

            if not values:
                continue

            records.append(
                {
                    "role": role,
                    "metric": metric,
                    "mean": mean(values),
                    "count": len(values),
                }
            )

    return sorted(
        records,
        key=lambda item: (
            item["role"],
            -item["mean"],
        ),
    )


def profile_consensus(
    profile_results: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize layer consensus for each profile classification."""
    records = []

    for name, result in profile_results.items():
        layer_results = result.get("layer_results", [])
        primary_role = result.get("primary_role", "Unknown")
        modifier = result.get("modifier", "Unknown")

        role_matches = [
            layer
            for layer in layer_results
            if layer.get("primary_role") == primary_role
        ]

        modifier_matches = [
            layer
            for layer in layer_results
            if layer.get("modifier") == modifier
        ]

        records.append(
            {
                "name": name,
                "primary_role": primary_role,
                "modifier": modifier,
                "subtype": result.get("subtype", "Unknown"),
                "confidence": result.get("confidence", 0.0),
                "role_consensus": safe_ratio(len(role_matches), len(layer_results)),
                "modifier_consensus": safe_ratio(
                    len(modifier_matches),
                    len(layer_results),
                ),
                "is_hybrid": result.get("is_hybrid", False),
            }
        )

    return sorted(
        records,
        key=lambda item: (
            item["primary_role"],
            item["name"],
        ),
    )


def empty_role_diagnostics() -> dict[str, Any]:
    """Return empty role diagnostics result."""
    return {
        "valid": False,
        "row_count": 0,
        "profile_count": 0,
        "role_distribution": [],
        "modifier_distribution": [],
        "profile_role_distribution": [],
        "profile_modifier_distribution": [],
        "confidence_summary": {
            "mean": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "hybrid_ratio": 0.0,
        },
        "profile_confidence_summary": {
            "mean": 0.0,
            "minimum": 0.0,
            "maximum": 0.0,
            "hybrid_ratio": 0.0,
        },
        "evidence_metric_distribution": [],
        "role_metric_signal": [],
        "profile_consensus": [],
        "profile_results": {},
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