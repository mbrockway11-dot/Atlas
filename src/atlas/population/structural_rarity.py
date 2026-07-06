
"""Structural Rarity Engine.

Detects outstanding structural outliers across the Atlas profile corpus.
"""

from __future__ import annotations

from statistics import mean, pstdev
from typing import Any

from atlas.population.structural_neighbors_v2 import build_population_vectors


RARITY_VERSION = "1.0"

NUMERIC_FIELDS = [
    "motif_richness",
    "raw_density",
    "truth_density",
    "raw_nodes",
    "raw_edges",
    "truth_nodes",
    "truth_edges",
]


def build_structural_rarity_report() -> dict[str, Any]:
    """Build corpus-wide structural rarity report."""
    vectors = build_population_vectors()

    distributions = build_distributions(vectors)

    scored = [
        score_profile_rarity(vector, vectors, distributions)
        for vector in vectors
    ]

    scored.sort(key=lambda item: item["overall_rarity_score"], reverse=True)

    return {
        "success": True,
        "version": RARITY_VERSION,
        "profile_count": len(vectors),
        "top_outliers": scored[:50],
        "role_outliers": group_top(scored, "role"),
        "topology_outliers": group_top(scored, "topology"),
        "metric_leaders": build_metric_leaders(scored),
        "profiles": scored,
    }


def build_distributions(vectors: list[dict[str, Any]]) -> dict[str, Any]:
    """Build frequency and numeric distributions."""
    role_counts = count_field(vectors, "role")
    subtype_counts = count_field(vectors, "subtype")
    topology_counts = count_field(vectors, "topology")
    axis_counts = count_field(vectors, "axis")

    numeric = {}

    for field in NUMERIC_FIELDS:
        values = [float(item.get(field) or 0) for item in vectors]
        numeric[field] = {
            "mean": mean(values) if values else 0,
            "std": pstdev(values) if len(values) > 1 else 0,
            "min": min(values) if values else 0,
            "max": max(values) if values else 0,
        }

    return {
        "role_counts": role_counts,
        "subtype_counts": subtype_counts,
        "topology_counts": topology_counts,
        "axis_counts": axis_counts,
        "numeric": numeric,
    }


def score_profile_rarity(
    vector: dict[str, Any],
    vectors: list[dict[str, Any]],
    distributions: dict[str, Any],
) -> dict[str, Any]:
    """Score one profile for structural rarity."""
    total = max(len(vectors), 1)

    role_freq = frequency_score(distributions["role_counts"], vector.get("role"), total)
    subtype_freq = frequency_score(distributions["subtype_counts"], vector.get("subtype"), total)
    topology_freq = frequency_score(distributions["topology_counts"], vector.get("topology"), total)
    axis_freq = frequency_score(distributions["axis_counts"], vector.get("axis"), total)

    numeric_scores = {
        field: zscore_abs(float(vector.get(field) or 0), distributions["numeric"][field])
        for field in NUMERIC_FIELDS
    }

    density_outlier = max(
        numeric_scores.get("raw_density", 0),
        numeric_scores.get("truth_density", 0),
    )

    graph_size_outlier = max(
        numeric_scores.get("raw_nodes", 0),
        numeric_scores.get("raw_edges", 0),
        numeric_scores.get("truth_nodes", 0),
        numeric_scores.get("truth_edges", 0),
    )

    motif_outlier = numeric_scores.get("motif_richness", 0)

    categorical_rarity = (
        role_freq * 0.25
        + subtype_freq * 0.30
        + topology_freq * 0.25
        + axis_freq * 0.20
    )

    numeric_rarity = (
        density_outlier * 0.40
        + graph_size_outlier * 0.35
        + motif_outlier * 0.25
    )

    overall = (categorical_rarity * 0.45) + (numeric_rarity * 0.55)

    return {
        **vector,
        "rarity": {
            "role_rarity": round(role_freq, 6),
            "subtype_rarity": round(subtype_freq, 6),
            "topology_rarity": round(topology_freq, 6),
            "axis_rarity": round(axis_freq, 6),
            "categorical_rarity": round(categorical_rarity, 6),
            "density_outlier": round(density_outlier, 6),
            "graph_size_outlier": round(graph_size_outlier, 6),
            "motif_outlier": round(motif_outlier, 6),
            "numeric_rarity": round(numeric_rarity, 6),
        },
        "overall_rarity_score": round(overall, 6),
        "outlier_label": outlier_label(overall),
        "outlier_reasons": build_reasons(
            vector=vector,
            role_freq=role_freq,
            subtype_freq=subtype_freq,
            topology_freq=topology_freq,
            axis_freq=axis_freq,
            numeric_scores=numeric_scores,
        ),
    }


def frequency_score(counts: dict[str, int], value: Any, total: int) -> float:
    """Return rarity score from categorical frequency."""
    count = counts.get(str(value), 0)
    frequency = count / max(total, 1)
    return 1.0 - frequency


def zscore_abs(value: float, distribution: dict[str, float]) -> float:
    """Return normalized absolute z-score capped to 1."""
    std = distribution.get("std", 0)
    avg = distribution.get("mean", 0)

    if std <= 0:
        return 0.0

    z = abs((value - avg) / std)
    return min(z / 3.0, 1.0)


def count_field(vectors: list[dict[str, Any]], field: str) -> dict[str, int]:
    """Count categorical field values."""
    counts: dict[str, int] = {}

    for vector in vectors:
        value = str(vector.get(field, "missing"))
        counts[value] = counts.get(value, 0) + 1

    return counts


def build_reasons(
    *,
    vector: dict[str, Any],
    role_freq: float,
    subtype_freq: float,
    topology_freq: float,
    axis_freq: float,
    numeric_scores: dict[str, float],
) -> list[str]:
    """Build human-readable outlier reasons."""
    reasons = []

    if role_freq >= 0.90:
        reasons.append(f"Rare role: {vector.get('role')}")

    if subtype_freq >= 0.90:
        reasons.append(f"Rare subtype: {vector.get('subtype')}")

    if topology_freq >= 0.90:
        reasons.append(f"Rare topology: {vector.get('topology')}")

    if axis_freq >= 0.80:
        reasons.append(f"Less common dominant axis: {vector.get('axis')}")

    for field, score in sorted(numeric_scores.items(), key=lambda item: item[1], reverse=True):
        if score >= 0.70:
            reasons.append(f"Numeric outlier: {field}={vector.get(field)}")

    if not reasons:
        reasons.append("Moderate structural rarity across combined metrics.")

    return reasons


def outlier_label(score: float) -> str:
    """Return outlier label."""
    if score >= 0.80:
        return "extreme_outlier"
    if score >= 0.65:
        return "strong_outlier"
    if score >= 0.50:
        return "notable_outlier"
    if score >= 0.35:
        return "mild_outlier"
    return "common_profile"


def group_top(scored: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
    """Group top profiles by a categorical field."""
    groups: dict[str, list[dict[str, Any]]] = {}

    for item in scored:
        key = str(item.get(field, "missing"))
        groups.setdefault(key, [])

        if len(groups[key]) < 10:
            groups[key].append(compact(item))

    return groups


def build_metric_leaders(scored: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Find leaders for each numeric field."""
    leaders = {}

    for field in NUMERIC_FIELDS:
        ranked = sorted(scored, key=lambda item: float(item.get(field) or 0), reverse=True)
        leaders[field] = [compact(item) for item in ranked[:10]]

    ranked_rarity = sorted(scored, key=lambda item: item["overall_rarity_score"], reverse=True)
    leaders["overall_rarity"] = [compact(item) for item in ranked_rarity[:25]]

    return leaders


def compact(item: dict[str, Any]) -> dict[str, Any]:
    """Compact profile record for summaries."""
    return {
        "profile_key": item.get("profile_key"),
        "name": item.get("name"),
        "role": item.get("role"),
        "subtype": item.get("subtype"),
        "topology": item.get("topology"),
        "axis": item.get("axis"),
        "motif_richness": item.get("motif_richness"),
        "raw_density": item.get("raw_density"),
        "truth_density": item.get("truth_density"),
        "overall_rarity_score": item.get("overall_rarity_score"),
        "outlier_label": item.get("outlier_label"),
        "outlier_reasons": item.get("outlier_reasons", []),
    }
