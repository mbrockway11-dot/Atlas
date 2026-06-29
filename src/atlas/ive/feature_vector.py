"""Planet feature vector builder."""

from __future__ import annotations

from typing import Any

from atlas.ive.schema import (
    IVE_VERSION,
    VECTOR_FEATURES,
    PlanetFeatureVector,
)
from atlas.research.attractor_metrics import build_layer_attractor_metrics
from atlas.research.coherence_metrics import build_layer_coherence_metrics
from atlas.research.graph_metrics import build_layer_graph_metrics, safe_ratio
from atlas.research.reduction_metrics import build_layer_reduction_metrics


def build_planet_feature_vector(
    layer: dict[str, Any],
    profile_name: str,
) -> PlanetFeatureVector:
    """Build one normalized planet feature vector from one identity layer."""
    features = build_layer_vector_features(layer)

    return PlanetFeatureVector(
        version=IVE_VERSION,
        name=profile_name,
        cipher=layer["cipher"],
        planet=layer["planet"],
        kamea=layer["kamea"],
        grid_size=int(layer["grid_size"]),
        features=features,
    )


def build_layer_vector_features(layer: dict[str, Any]) -> dict[str, float]:
    """Build bounded vector features from one layer."""
    graph_metrics = build_layer_graph_metrics(layer)
    coherence_metrics = build_layer_coherence_metrics(layer)
    reduction_metrics = build_layer_reduction_metrics(layer)
    attractor_metrics = build_layer_attractor_metrics(layer)

    base_features = layer["features"]
    path = base_features["path_views"]["analysis_path"]

    node_weights = path["node_weights"]
    edge_weights = path["edge_weights"]

    grid_size = int(layer["grid_size"])
    grid_capacity = grid_size * grid_size

    unique_nodes = len(node_weights)
    unique_edges = len(edge_weights)

    max_possible_edges = grid_capacity * (grid_capacity - 1)

    raw = {
        "node_coverage": safe_ratio(unique_nodes, grid_capacity),
        "edge_coverage": safe_ratio(unique_edges, max_possible_edges),
        "density": base_features.get("density", 0.0),
        "entropy": base_features.get("entropy", 0.0),
        "axis_strength": base_features.get("axis_strength", 0.0),
        "graph_coherence": coherence_metrics["graph_coherence"],
        "core_survival_score": reduction_metrics["core_survival_score"],
        "topology_stability": reduction_metrics["topology_stability"],
        "attractor_stability": attractor_metrics["attractor_stability"],
        "bridge_ratio": graph_metrics["bridge_ratio"],
        "articulation_ratio": graph_metrics["articulation_ratio"],
        "loop_ratio": safe_ratio(base_features.get("self_loops", 0), unique_edges),
        "hub_ratio": graph_metrics["hub_ratio"],
        "leaf_ratio": graph_metrics["leaf_ratio"],
        "reduction_entropy": reduction_metrics["reduction_entropy"],
        "node_survival_auc": reduction_metrics["node_survival_auc"],
        "edge_survival_auc": reduction_metrics["edge_survival_auc"],
    }

    return {
        feature: clamp(float(raw.get(feature, 0.0)))
        for feature in VECTOR_FEATURES
    }


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))