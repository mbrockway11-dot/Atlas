"""Identity Topology Graph builder."""

from __future__ import annotations

from typing import Any

from atlas.identity.layer import IdentityLayer, identity_layer_to_dict
from atlas.identity.similarity import compare_identity_layers
from atlas.invariant.pipeline import run_invariant_pipeline


def build_identity_layers(name: str) -> list[dict[str, Any]]:
    """Build the 21 identity layers from invariant analysis."""
    invariant = run_invariant_pipeline(name)

    layers = []

    for analysis in invariant["analyses"]:
        layer_id = f"{analysis['cipher']}::{analysis['planet']}"

        features = dict(analysis["features"])
        features["path_views"] = analysis["path_views"]

        layer = IdentityLayer(
            layer_id=layer_id,
            cipher=analysis["cipher"],
            planet=analysis["planet"],
            kamea=analysis["kamea"],
            grid_size=analysis["grid_size"],
            sequence=analysis["sequence"],
            features=features,
            subtype=analysis["subtype"],
            kamea_score=analysis["kamea_score"],
            planetary_function=analysis["planetary_function"],
        )

        layer_dict = identity_layer_to_dict(layer)
        layer_dict["structural_layer_score"] = score_identity_layer(layer_dict)

        layers.append(layer_dict)

    return layers


def build_identity_graph(name: str) -> dict[str, Any]:
    """Build Identity Topology Graph from 21 layers."""
    layers = build_identity_layers(name)
    layer_edges = build_layer_similarity_edges(layers)

    return {
        "name": name,
        "layer_count": len(layers),
        "layers": layers,
        "layer_edges": layer_edges,
        "summary": build_identity_graph_summary(layers, layer_edges),
    }


def build_layer_similarity_edges(
    layers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Build similarity edges between all identity layers."""
    edges = []

    for index_a, layer_a in enumerate(layers):
        for index_b, layer_b in enumerate(layers):
            if index_b <= index_a:
                continue

            comparison = compare_identity_layers(layer_a, layer_b)

            edges.append(
                {
                    "source": layer_a["layer_id"],
                    "target": layer_b["layer_id"],
                    "similarity": comparison["overall_similarity"],
                    "subtype_similarity": comparison["subtype_similarity"],
                    "feature_similarity": comparison["feature_similarity"],
                }
            )

    return sorted(
        edges,
        key=lambda item: item["similarity"],
        reverse=True,
    )


def build_identity_graph_summary(
    layers: list[dict[str, Any]],
    layer_edges: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize identity graph."""
    strongest_layer = max(
        layers,
        key=lambda layer: layer.get("structural_layer_score", 0.0),
    )

    legacy_strongest_layer = max(
        layers,
        key=lambda layer: layer.get("kamea_score", 0.0),
    )

    average_similarity = (
        sum(edge["similarity"] for edge in layer_edges) / len(layer_edges)
        if layer_edges
        else 0.0
    )

    return {
        "strongest_layer": strongest_layer["layer_id"],
        "strongest_planet": strongest_layer["planet"],
        "strongest_cipher": strongest_layer["cipher"],
        "strongest_structural_score": strongest_layer["structural_layer_score"],
        "legacy_strongest_layer": legacy_strongest_layer["layer_id"],
        "legacy_strongest_planet": legacy_strongest_layer["planet"],
        "legacy_strongest_cipher": legacy_strongest_layer["cipher"],
        "strongest_kamea_score": legacy_strongest_layer["kamea_score"],
        "average_inter_layer_similarity": average_similarity,
        "strongest_layer_edges": layer_edges[:5],
        "weakest_layer_edges": layer_edges[-5:],
    }


def score_identity_layer(layer: dict[str, Any]) -> float:
    """Score an identity layer using structural measurements, not kamea_score."""
    features = layer["features"]
    path = features["path_views"]["analysis_path"]

    grid_capacity = layer["grid_size"] * layer["grid_size"]
    node_weights = path["node_weights"]
    edge_weights = path["edge_weights"]

    unique_nodes = len(node_weights)
    unique_edges = len(edge_weights)

    node_coverage = safe_ratio(unique_nodes, grid_capacity)
    density = safe_float(features.get("density", 0.0))
    entropy = safe_float(features.get("entropy", 0.0))
    axis_strength = safe_float(features.get("axis_strength", 0.0))

    edge_presence = safe_ratio(unique_edges, unique_edges + unique_nodes)

    return clamp(
        node_coverage * 0.25
        + density * 0.20
        + entropy * 0.20
        + axis_strength * 0.20
        + edge_presence * 0.15
    )


def safe_ratio(numerator: float, denominator: float) -> float:
    """Safely divide two values."""
    if denominator == 0:
        return 0.0

    return float(numerator) / float(denominator)


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))