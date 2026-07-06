
"""Structural Impact Engine v1.

Ranks profiles by multi-factor structural impact:
rarity, graph complexity, truth density, Kamea/graph intensity,
population centrality proxy, and classification confidence.
"""

from __future__ import annotations

from statistics import mean
from typing import Any

from atlas.population.structural_neighbors_v2 import build_population_vectors
from atlas.population.structural_rarity import build_structural_rarity_report


STRUCTURAL_IMPACT_VERSION = "1.0"


WEIGHTS = {
    "rarity": 0.25,
    "graph_complexity": 0.20,
    "truth_density": 0.20,
    "motif_richness": 0.15,
    "role_weight": 0.10,
    "centrality_proxy": 0.10,
}


ROLE_IMPACT_PRIORS = {
    "Pattern-Weaver": 1.00,
    "Persistence-Architect": 0.88,
    "Cycle-Weaver": 0.78,
    "Connector-Architect": 0.72,
    "Amplifier-Connector": 0.68,
    "Regulator-Builder": 0.64,
    "Temporal-Interpreter": 0.60,
    "Unclassified Structural Actor": 0.35,
}


def build_structural_impact_report() -> dict[str, Any]:
    """Build structural impact report."""
    vectors = build_population_vectors()
    rarity = build_structural_rarity_report()

    rarity_by_key = {
        item["profile_key"]: item
        for item in rarity.get("profiles", [])
    }

    scored = []

    distributions = build_metric_distributions(vectors)

    for vector in vectors:
        key = vector.get("profile_key")
        rarity_record = rarity_by_key.get(key, {})

        scored.append(
            score_structural_impact(
                vector=vector,
                rarity_record=rarity_record,
                distributions=distributions,
            )
        )

    scored.sort(key=lambda item: item["impact_score"], reverse=True)

    return {
        "success": True,
        "version": STRUCTURAL_IMPACT_VERSION,
        "profile_count": len(scored),
        "weights": WEIGHTS,
        "top_impact_profiles": scored[:100],
        "leaderboards": build_leaderboards(scored),
        "profiles": scored,
    }


def score_structural_impact(
    *,
    vector: dict[str, Any],
    rarity_record: dict[str, Any],
    distributions: dict[str, Any],
) -> dict[str, Any]:
    """Score one profile."""
    rarity_score = float(rarity_record.get("overall_rarity_score") or 0)

    graph_complexity = percentile_like(
        float(vector.get("raw_edges") or 0),
        distributions["raw_edges"],
    )

    truth_density = percentile_like(
        float(vector.get("truth_density") or 0),
        distributions["truth_density"],
    )

    motif_richness = percentile_like(
        float(vector.get("motif_richness") or 0),
        distributions["motif_richness"],
    )

    centrality_proxy = percentile_like(
        float(vector.get("raw_density") or 0),
        distributions["raw_density"],
    )

    role_weight = ROLE_IMPACT_PRIORS.get(
        str(vector.get("role")),
        0.5,
    )

    impact_score = (
        rarity_score * WEIGHTS["rarity"]
        + graph_complexity * WEIGHTS["graph_complexity"]
        + truth_density * WEIGHTS["truth_density"]
        + motif_richness * WEIGHTS["motif_richness"]
        + role_weight * WEIGHTS["role_weight"]
        + centrality_proxy * WEIGHTS["centrality_proxy"]
    )

    return {
        **vector,
        "impact_score": round(impact_score, 6),
        "impact_percent": round(impact_score * 100, 2),
        "impact_label": impact_label(impact_score),
        "components": {
            "rarity": round(rarity_score, 6),
            "graph_complexity": round(graph_complexity, 6),
            "truth_density": round(truth_density, 6),
            "motif_richness": round(motif_richness, 6),
            "role_weight": round(role_weight, 6),
            "centrality_proxy": round(centrality_proxy, 6),
        },
        "rarity_label": rarity_record.get("outlier_label"),
        "rarity_reasons": rarity_record.get("outlier_reasons", []),
        "impact_reasons": build_impact_reasons(
            vector=vector,
            impact_score=impact_score,
            rarity_score=rarity_score,
            graph_complexity=graph_complexity,
            truth_density=truth_density,
            motif_richness=motif_richness,
            role_weight=role_weight,
            centrality_proxy=centrality_proxy,
        ),
    }


def build_metric_distributions(vectors: list[dict[str, Any]]) -> dict[str, list[float]]:
    """Build sorted numeric distributions."""
    fields = [
        "raw_edges",
        "truth_density",
        "motif_richness",
        "raw_density",
    ]

    return {
        field: sorted(float(vector.get(field) or 0) for vector in vectors)
        for field in fields
    }


def percentile_like(value: float, sorted_values: list[float]) -> float:
    """Return simple percentile position 0..1."""
    if not sorted_values:
        return 0.0

    below_or_equal = sum(1 for item in sorted_values if item <= value)
    return below_or_equal / len(sorted_values)


def impact_label(score: float) -> str:
    """Return impact label."""
    if score >= 0.85:
        return "legendary_structural_outlier"
    if score >= 0.75:
        return "high_impact_outlier"
    if score >= 0.65:
        return "strong_structural_signal"
    if score >= 0.50:
        return "notable_structural_signal"
    return "common_structural_signal"


def build_impact_reasons(
    *,
    vector: dict[str, Any],
    impact_score: float,
    rarity_score: float,
    graph_complexity: float,
    truth_density: float,
    motif_richness: float,
    role_weight: float,
    centrality_proxy: float,
) -> list[str]:
    """Build readable reasons."""
    reasons = []

    if rarity_score >= 0.70:
        reasons.append("High structural rarity")

    if graph_complexity >= 0.90:
        reasons.append("Top-decile graph complexity")

    if truth_density >= 0.90:
        reasons.append("Top-decile truth density")

    if motif_richness >= 0.90:
        reasons.append("Top-decile motif richness")

    if centrality_proxy >= 0.90:
        reasons.append("Top-decile raw graph density")

    if role_weight >= 0.85:
        reasons.append(f"High-impact structural role: {vector.get('role')}")

    if impact_score >= 0.75:
        reasons.append("Composite impact remains high across multiple independent metrics")

    if not reasons:
        reasons.append("Moderate impact across combined structural metrics")

    return reasons


def build_leaderboards(scored: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    """Build impact leaderboards."""
    return {
        "overall_impact": [compact(item) for item in sorted(scored, key=lambda x: x["impact_score"], reverse=True)[:50]],
        "graph_complexity": [compact(item) for item in sorted(scored, key=lambda x: x["components"]["graph_complexity"], reverse=True)[:25]],
        "truth_density": [compact(item) for item in sorted(scored, key=lambda x: x["components"]["truth_density"], reverse=True)[:25]],
        "motif_richness": [compact(item) for item in sorted(scored, key=lambda x: x["components"]["motif_richness"], reverse=True)[:25]],
        "rarity": [compact(item) for item in sorted(scored, key=lambda x: x["components"]["rarity"], reverse=True)[:25]],
        "centrality_proxy": [compact(item) for item in sorted(scored, key=lambda x: x["components"]["centrality_proxy"], reverse=True)[:25]],
    }


def compact(item: dict[str, Any]) -> dict[str, Any]:
    """Compact record."""
    return {
        "profile_key": item.get("profile_key"),
        "name": item.get("name"),
        "role": item.get("role"),
        "subtype": item.get("subtype"),
        "topology": item.get("topology"),
        "impact_score": item.get("impact_score"),
        "impact_percent": item.get("impact_percent"),
        "impact_label": item.get("impact_label"),
        "components": item.get("components", {}),
        "impact_reasons": item.get("impact_reasons", []),
    }
