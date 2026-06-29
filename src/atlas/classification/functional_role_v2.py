"""Functional Role Classifier v2.

This classifier is Atlas v2-native.

It uses research-matrix metrics instead of the legacy TopologyGraph scoring model.
Roles are competitive: Driver, Amplifier, Regulator, Integrator, and Explorer
are scored from the same evidence field and then normalized.
"""

from __future__ import annotations

from math import exp
from statistics import mean
from typing import Any


ROLE_NAMES = [
    "Driver",
    "Amplifier",
    "Regulator",
    "Integrator",
    "Explorer",
]


MODIFIER_NAMES = [
    "Axial",
    "Radial",
    "Coherent",
    "Persistent",
    "Bridge",
    "Expansive",
    "Diffuse",
    "Compressive",
    "Volatile",
    "Balanced",
]


def classify_functional_role_v2(row: dict[str, Any]) -> dict[str, Any]:
    """Classify one research-matrix row into a functional role."""
    raw_scores = score_functional_roles(row)
    scores = normalize_scores(raw_scores)

    ranked_roles = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    primary_role = ranked_roles[0][0]
    secondary_role = ranked_roles[1][0]
    confidence = ranked_roles[0][1] - ranked_roles[1][1]

    modifier_scores = score_modifiers(row)
    ranked_modifiers = sorted(
        modifier_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    modifier = ranked_modifiers[0][0]

    return {
        "version": "2.0",
        "primary_role": primary_role,
        "secondary_role": secondary_role,
        "modifier": modifier,
        "subtype": f"{primary_role}-{modifier}",
        "scores": scores,
        "raw_scores": raw_scores,
        "modifier_scores": modifier_scores,
        "confidence": confidence,
        "is_hybrid": confidence < 0.12,
        "evidence": build_evidence_summary(
            row=row,
            primary_role=primary_role,
            modifier=modifier,
        ),
    }


def classify_profile_functional_role_v2(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Classify a full profile from its 21 research rows."""
    if not rows:
        return empty_classification()

    layer_results = [
        classify_functional_role_v2(row)
        for row in rows
    ]

    averaged_scores = average_score_dicts(
        [
            result["scores"]
            for result in layer_results
        ]
    )

    averaged_modifier_scores = average_score_dicts(
        [
            result["modifier_scores"]
            for result in layer_results
        ]
    )

    ranked_roles = sorted(
        averaged_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    ranked_modifiers = sorted(
        averaged_modifier_scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    primary_role = ranked_roles[0][0]
    secondary_role = ranked_roles[1][0]
    modifier = ranked_modifiers[0][0]
    confidence = ranked_roles[0][1] - ranked_roles[1][1]

    return {
        "version": "2.0",
        "scope": "profile",
        "primary_role": primary_role,
        "secondary_role": secondary_role,
        "modifier": modifier,
        "subtype": f"{primary_role}-{modifier}",
        "scores": averaged_scores,
        "modifier_scores": averaged_modifier_scores,
        "confidence": confidence,
        "is_hybrid": confidence < 0.12,
        "layer_results": layer_results,
    }


def score_functional_roles(row: dict[str, Any]) -> dict[str, float]:
    """Score all functional roles before normalization."""
    driver = weighted_sum(
        [
            (metric(row, "axis_strength"), 0.24),
            (metric(row, "hub_ratio"), 0.18),
            (metric(row, "articulation_ratio"), 0.16),
            (metric(row, "max_degree"), 0.10),
            (metric(row, "graph_coherence"), 0.18),
            (1.0 - metric(row, "peripheral_node_ratio"), 0.14),
        ]
    )

    amplifier = weighted_sum(
        [
            (metric(row, "density"), 0.18),
            (metric(row, "mean_edge_coherence"), 0.20),
            (metric(row, "edge_survival_auc"), 0.18),
            (normalized_count(row, "max_node_weight"), 0.12),
            (metric(row, "profile_node_persistence_ratio"), 0.16),
            (metric(row, "core_edge_ratio"), 0.16),
        ]
    )

    regulator = weighted_sum(
        [
            (metric(row, "topology_stability"), 0.22),
            (metric(row, "core_survival_score"), 0.20),
            (metric(row, "mean_node_coherence"), 0.18),
            (metric(row, "core_node_ratio"), 0.16),
            (metric(row, "attractor_stability"), 0.16),
            (1.0 - metric(row, "collapse_slope"), 0.08),
        ]
    )

    integrator = weighted_sum(
        [
            (metric(row, "bridge_ratio"), 0.24),
            (metric(row, "articulation_ratio"), 0.22),
            (metric(row, "adaptive_node_ratio"), 0.18),
            (metric(row, "adaptive_edge_ratio"), 0.18),
            (metric(row, "largest_component_ratio"), 0.10),
            (metric(row, "graph_coherence"), 0.08),
        ]
    )

    explorer = weighted_sum(
        [
            (metric(row, "entropy"), 0.22),
            (metric(row, "node_coverage"), 0.20),
            (normalized_count(row, "unique_nodes"), 0.12),
            (metric(row, "peripheral_node_ratio"), 0.16),
            (metric(row, "reduction_entropy"), 0.16),
            (1.0 - metric(row, "core_node_ratio"), 0.14),
        ]
    )

    return {
        "Driver": clamp(driver),
        "Amplifier": clamp(amplifier),
        "Regulator": clamp(regulator),
        "Integrator": clamp(integrator),
        "Explorer": clamp(explorer),
    }


def score_modifiers(row: dict[str, Any]) -> dict[str, float]:
    """Score descriptive modifiers from structural evidence."""
    return {
        "Axial": metric(row, "axis_strength"),
        "Radial": average(
            [
                metric(row, "hub_ratio"),
                normalized_count(row, "max_degree"),
            ]
        ),
        "Coherent": metric(row, "graph_coherence"),
        "Persistent": average(
            [
                metric(row, "core_survival_score"),
                metric(row, "attractor_stability"),
                metric(row, "topology_stability"),
            ]
        ),
        "Bridge": average(
            [
                metric(row, "bridge_ratio"),
                metric(row, "articulation_ratio"),
            ]
        ),
        "Expansive": average(
            [
                metric(row, "entropy"),
                metric(row, "node_coverage"),
                metric(row, "reduction_entropy"),
            ]
        ),
        "Diffuse": average(
            [
                metric(row, "peripheral_node_ratio"),
                1.0 - metric(row, "density"),
            ]
        ),
        "Compressive": average(
            [
                metric(row, "density"),
                metric(row, "core_node_ratio"),
                1.0 - metric(row, "entropy"),
            ]
        ),
        "Volatile": average(
            [
                metric(row, "collapse_slope"),
                1.0 - metric(row, "topology_stability"),
                metric(row, "peripheral_edge_ratio"),
            ]
        ),
        "Balanced": average(
            [
                metric(row, "mean_node_coherence"),
                metric(row, "mean_edge_coherence"),
                metric(row, "adaptive_node_ratio"),
            ]
        ),
    }


def normalize_scores(raw_scores: dict[str, float]) -> dict[str, float]:
    """Normalize role scores with softmax."""
    if not raw_scores:
        return {}

    values = list(raw_scores.values())

    if all(value == 0.0 for value in values):
        even = 1.0 / len(raw_scores)
        return {
            key: even
            for key in raw_scores
        }

    max_value = max(values)

    exponentials = {
        key: exp(value - max_value)
        for key, value in raw_scores.items()
    }

    total = sum(exponentials.values())

    if total == 0:
        even = 1.0 / len(raw_scores)
        return {
            key: even
            for key in raw_scores
        }

    return {
        key: value / total
        for key, value in exponentials.items()
    }


def build_evidence_summary(
    *,
    row: dict[str, Any],
    primary_role: str,
    modifier: str,
) -> dict[str, Any]:
    """Build explanatory evidence summary."""
    candidate_metrics = [
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

    observed = [
        {
            "metric": name,
            "value": metric(row, name),
        }
        for name in candidate_metrics
        if name in row
    ]

    ranked = sorted(
        observed,
        key=lambda item: item["value"],
        reverse=True,
    )

    return {
        "primary_role": primary_role,
        "modifier": modifier,
        "strongest_metric": ranked[0]["metric"] if ranked else None,
        "strongest_value": ranked[0]["value"] if ranked else None,
        "supporting_metrics": ranked[:5],
    }


def average_score_dicts(score_dicts: list[dict[str, float]]) -> dict[str, float]:
    """Average a list of score dictionaries."""
    if not score_dicts:
        return {}

    keys = sorted(
        {
            key
            for scores in score_dicts
            for key in scores
        }
    )

    return {
        key: mean(
            [
                scores.get(key, 0.0)
                for scores in score_dicts
            ]
        )
        for key in keys
    }


def empty_classification() -> dict[str, Any]:
    """Return empty functional role classification."""
    even = 1.0 / len(ROLE_NAMES)

    return {
        "version": "2.0",
        "scope": "profile",
        "primary_role": "Unknown",
        "secondary_role": "Unknown",
        "modifier": "Unknown",
        "subtype": "Unknown",
        "scores": {
            role: even
            for role in ROLE_NAMES
        },
        "modifier_scores": {
            modifier: 0.0
            for modifier in MODIFIER_NAMES
        },
        "confidence": 0.0,
        "is_hybrid": True,
        "layer_results": [],
    }


def metric(row: dict[str, Any], key: str) -> float:
    """Read a bounded metric from a row."""
    value = row.get(key, 0.0)

    try:
        return clamp(float(value))
    except (TypeError, ValueError):
        return 0.0


def normalized_count(row: dict[str, Any], key: str) -> float:
    """Normalize count-like metrics with a soft cap."""
    value = row.get(key, 0.0)

    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return 0.0

    return clamp(numeric / (numeric + 10.0)) if numeric > 0 else 0.0


def weighted_sum(items: list[tuple[float, float]]) -> float:
    """Compute weighted sum from value-weight pairs."""
    total_weight = sum(weight for _, weight in items)

    if total_weight == 0:
        return 0.0

    return sum(value * weight for value, weight in items) / total_weight


def average(values: list[float]) -> float:
    """Average values safely."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))