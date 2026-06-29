"""Dynamic motion profile research tools.

This module intentionally avoids legacy kamea_score ranking.
Motion is now derived from observable structural features.
"""

from __future__ import annotations

from typing import Any

from atlas.research.feature_variance import AUDIT_FEATURES


MOTION_FEATURES = [
    "max_depth",
    "max_node_weight",
    "self_loops",
    "unique_edges",
    "entropy",
    "density",
    "axis_strength",
    "profile_node_persistence_ratio",
    "profile_edge_persistence_ratio",
]


def build_dynamic_motion_profile(
    acf: dict[str, Any],
) -> dict[str, Any]:
    """Build a dynamic motion profile from observable layer metrics."""
    from atlas.research.matrix import build_profile_matrix_rows

    rows = build_profile_matrix_rows(acf)

    feature_summary = summarize_motion_features(rows)
    planet_summary = summarize_motion_by_planet(rows)

    return {
        "name": acf["identity"]["name"],
        "feature_summary": feature_summary,
        "planet_summary": planet_summary,
        "motion_summary": build_motion_summary(
            feature_summary,
            planet_summary,
        ),
    }


def summarize_motion_features(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize motion-relevant features across all layers."""
    output = []

    for feature in MOTION_FEATURES:
        values = [
            float(row[feature])
            for row in rows
            if feature in row
        ]

        if not values:
            continue

        output.append(
            {
                "feature": feature,
                "mean": _mean(values),
                "minimum": min(values),
                "maximum": max(values),
                "range": max(values) - min(values),
                "total": sum(values),
                "motion_role": classify_motion_role(feature),
            }
        )

    return sorted(
        output,
        key=lambda row: (row["range"], row["total"]),
        reverse=True,
    )


def summarize_motion_by_planet(
    rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Summarize structural motion by planet without kamea_score."""
    grouped: dict[str, list[dict[str, Any]]] = {}

    for row in rows:
        grouped.setdefault(row["planet"], [])
        grouped[row["planet"]].append(row)

    output = []

    for planet, planet_rows in grouped.items():
        depth = _mean(
            [
                float(row["max_depth"])
                for row in planet_rows
            ]
        )
        entropy = _mean(
            [
                float(row["entropy"])
                for row in planet_rows
            ]
        )
        edge_activity = _mean(
            [
                float(row["unique_edges"])
                for row in planet_rows
            ]
        )
        loop_activity = _mean(
            [
                float(row["self_loops"])
                for row in planet_rows
            ]
        )
        axis_strength = _mean(
            [
                float(row["axis_strength"])
                for row in planet_rows
            ]
        )

        structural_motion = (
            depth
            + entropy
            + edge_activity
            + loop_activity
            + axis_strength
        ) / 5.0

        output.append(
            {
                "planet": planet,
                "depth": depth,
                "entropy": entropy,
                "edge_activity": edge_activity,
                "loop_activity": loop_activity,
                "axis_strength": axis_strength,
                "structural_motion": structural_motion,
            }
        )

    return sorted(
        output,
        key=lambda row: row["structural_motion"],
        reverse=True,
    )


def classify_motion_role(feature: str) -> str:
    """Classify a feature's motion role."""
    if feature in {
        "max_depth",
        "max_node_weight",
        "self_loops",
    }:
        return "recurrence / depth"

    if feature in {
        "unique_edges",
        "density",
        "entropy",
    }:
        return "flow complexity"

    if feature in {
        "axis_strength",
    }:
        return "directional structure"

    if feature in {
        "profile_node_persistence_ratio",
        "profile_edge_persistence_ratio",
    }:
        return "identity persistence"

    return "structural feature"


def build_motion_summary(
    feature_summary: list[dict[str, Any]],
    planet_summary: list[dict[str, Any]],
) -> str:
    """Build human-readable motion summary."""
    top_features = [
        row["feature"]
        for row in feature_summary[:3]
    ]

    top_planets = [
        row["planet"]
        for row in planet_summary[:3]
    ]

    return (
        "Motion is currently described by observable graph features, not legacy "
        "planetary score ranking. Strongest differentiating feature families are "
        f"{', '.join(top_features)}. Highest structural-motion planetary fields are "
        f"{', '.join(top_planets)}."
    )


def compare_motion_profiles(
    acf_a: dict[str, Any],
    acf_b: dict[str, Any],
) -> dict[str, Any]:
    """Compare two profiles by actual feature differences."""
    from atlas.research.feature_importance import (
        compare_profile_feature_importance,
        summarize_feature_importance,
    )
    from atlas.research.matrix import build_profile_matrix_rows

    rows_a = build_profile_matrix_rows(acf_a)
    rows_b = build_profile_matrix_rows(acf_b)

    importance = compare_profile_feature_importance(rows_a, rows_b)
    summary = summarize_feature_importance(importance)

    return {
        "name_a": acf_a["identity"]["name"],
        "name_b": acf_b["identity"]["name"],
        "top_layer_differences": summary["top_layer_differences"],
        "top_feature_families": summary["top_feature_families"],
    }


def _mean(values: list[float]) -> float:
    """Mean helper."""
    if not values:
        return 0.0

    return sum(values) / len(values)