"""Structural archetype definitions."""

from __future__ import annotations


STRUCTURAL_ARCHETYPES = {
    "core_dominant": {
        "label": "Core Dominant",
        "description": (
            "Structural activity concentrates around durable central regions "
            "that remain important through reduction."
        ),
        "primary_metrics": [
            "core_survival_score",
            "topology_stability",
            "attractor_stability",
        ],
    },
    "hub_dominant": {
        "label": "Hub Dominant",
        "description": (
            "Information repeatedly concentrates through a small set of highly "
            "connected regions."
        ),
        "primary_metrics": [
            "hub_ratio",
            "graph_coherence",
            "node_survival_auc",
        ],
    },
    "bridge_dominant": {
        "label": "Bridge Dominant",
        "description": (
            "Transitions depend on connector regions that link otherwise "
            "separate parts of the topology."
        ),
        "primary_metrics": [
            "bridge_ratio",
            "articulation_ratio",
            "edge_survival_auc",
        ],
    },
    "distributed": {
        "label": "Distributed",
        "description": (
            "Activity spreads broadly across the available measurement space "
            "rather than concentrating in a narrow center."
        ),
        "primary_metrics": [
            "entropy",
            "node_coverage",
            "edge_coverage",
        ],
    },
    "recursive": {
        "label": "Recursive",
        "description": (
            "The structure repeatedly returns to established pathways, loops, "
            "or reinforcing anchors."
        ),
        "primary_metrics": [
            "loop_ratio",
            "reduction_entropy",
            "attractor_stability",
        ],
    },
    "sparse_terminal": {
        "label": "Sparse Terminal",
        "description": (
            "The topology shows weaker connectivity and more terminal or "
            "low-degree regions."
        ),
        "primary_metrics": [
            "leaf_ratio",
            "density",
            "edge_coverage",
        ],
    },
}


def list_archetypes() -> list[str]:
    """Return known structural archetype keys."""
    return sorted(STRUCTURAL_ARCHETYPES)


def get_archetype(key: str) -> dict:
    """Return one archetype definition."""
    return STRUCTURAL_ARCHETYPES[key]


def score_archetype(
    features: dict[str, float],
    archetype_key: str,
) -> float:
    """Score one archetype from feature values."""
    archetype = get_archetype(archetype_key)
    metrics = archetype["primary_metrics"]

    values = [
        float(features.get(metric, 0.0))
        for metric in metrics
    ]

    if not values:
        return 0.0

    if archetype_key == "sparse_terminal":
        return clamp(
            (
                float(features.get("leaf_ratio", 0.0))
                + (1.0 - float(features.get("density", 0.0)))
                + (1.0 - float(features.get("edge_coverage", 0.0)))
            )
            / 3.0
        )

    return clamp(sum(values) / len(values))


def score_archetypes(features: dict[str, float]) -> dict[str, float]:
    """Score all archetypes from feature values."""
    return {
        key: score_archetype(features, key)
        for key in STRUCTURAL_ARCHETYPES
    }


def rank_archetypes(features: dict[str, float]) -> list[dict[str, float | str]]:
    """Rank archetypes by score descending."""
    scores = score_archetypes(features)

    ranked = sorted(
        scores.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    return [
        {
            "key": key,
            "label": STRUCTURAL_ARCHETYPES[key]["label"],
            "score": score,
            "description": STRUCTURAL_ARCHETYPES[key]["description"],
        }
        for key, score in ranked
    ]


def clamp(value: float) -> float:
    """Clamp to 0-1."""
    return max(0.0, min(1.0, float(value)))