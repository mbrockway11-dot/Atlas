"""Layer-level coherence summary metrics for Atlas research rows."""

from __future__ import annotations

from statistics import mean, median, pstdev
from typing import Any

from atlas.research.graph_metrics import (
    build_undirected_adjacency,
    find_articulation_points,
    find_bridges,
    safe_ratio,
)


def build_layer_coherence_metrics(layer: dict[str, Any]) -> dict[str, Any]:
    """Build coherence summary metrics for one construction layer."""
    path = layer["features"]["path_views"]["analysis_path"]
    visits = path["visit_history"]["visits"]
    node_weights = path["node_weights"]
    edge_weights = path["edge_weights"]

    nodes = {
        str(visit["node"])
        for visit in visits
    }

    directed_edges = [
        (
            str(source["node"]),
            str(target["node"]),
        )
        for source, target in zip(visits[:-1], visits[1:])
    ]

    adjacency = build_undirected_adjacency(
        nodes=nodes,
        directed_edges=directed_edges,
    )

    bridges = find_bridges(nodes, adjacency)
    articulations = find_articulation_points(nodes, adjacency)

    node_scores = [
        score_node_coherence(
            node=node,
            node_weights=node_weights,
            adjacency=adjacency,
            articulations=articulations,
        )
        for node in sorted(nodes)
    ]

    edge_scores = [
        score_edge_coherence(
            source=source,
            target=target,
            edge_weights=edge_weights,
            bridges=bridges,
        )
        for source, target in directed_edges
    ]

    node_regions = [
        classify_coherence(score)
        for score in node_scores
    ]

    edge_regions = [
        classify_coherence(score)
        for score in edge_scores
    ]

    mean_node = mean(node_scores) if node_scores else 0.0
    mean_edge = mean(edge_scores) if edge_scores else 0.0

    structural_stability = (
        region_ratio(node_regions, "core") * 0.50
        + region_ratio(edge_regions, "core") * 0.30
        + (1.0 - region_ratio(node_regions, "peripheral")) * 0.20
    )

    graph_coherence = (
        mean_node * 0.40
        + mean_edge * 0.40
        + structural_stability * 0.20
    )

    return {
        "mean_node_coherence": mean_node,
        "median_node_coherence": median(node_scores) if node_scores else 0.0,
        "std_node_coherence": pstdev(node_scores) if len(node_scores) > 1 else 0.0,
        "mean_edge_coherence": mean_edge,
        "median_edge_coherence": median(edge_scores) if edge_scores else 0.0,
        "std_edge_coherence": pstdev(edge_scores) if len(edge_scores) > 1 else 0.0,
        "core_node_ratio": region_ratio(node_regions, "core"),
        "adaptive_node_ratio": region_ratio(node_regions, "adaptive"),
        "peripheral_node_ratio": region_ratio(node_regions, "peripheral"),
        "core_edge_ratio": region_ratio(edge_regions, "core"),
        "adaptive_edge_ratio": region_ratio(edge_regions, "adaptive"),
        "peripheral_edge_ratio": region_ratio(edge_regions, "peripheral"),
        "graph_coherence": graph_coherence,
    }


def score_node_coherence(
    *,
    node: str,
    node_weights: dict[Any, Any],
    adjacency: dict[str, set[str]],
    articulations: set[str],
) -> float:
    """Score one node's structural coherence."""
    weight = float(node_weights.get(node, node_weights.get(int_or_self(node), 0)))
    max_weight = max([float(value) for value in node_weights.values()], default=1.0)

    weight_support = safe_ratio(weight, max_weight)
    degree = len(adjacency.get(node, set()))
    degree_support = safe_ratio(degree, 6.0)
    articulation_support = 1.0 if node in articulations else 0.0
    hub_support = 1.0 if degree >= 3 else 0.0
    leaf_penalty = 0.25 if degree == 1 else 0.0

    score = (
        weight_support * 0.35
        + degree_support * 0.25
        + articulation_support * 0.20
        + hub_support * 0.20
        - leaf_penalty
    )

    return clamp(score)


def score_edge_coherence(
    *,
    source: str,
    target: str,
    edge_weights: dict[Any, Any],
    bridges: set[tuple[str, str]],
) -> float:
    """Score one edge's structural coherence."""
    edge_id = f"{source}->{target}"
    reverse_id = f"{target}->{source}"
    tuple_id = (source, target)

    weight = float(
        edge_weights.get(
            edge_id,
            edge_weights.get(
                reverse_id,
                edge_weights.get(tuple_id, 1),
            ),
        )
    )

    max_weight = max([float(value) for value in edge_weights.values()], default=1.0)
    weight_support = safe_ratio(weight, max_weight)

    bridge_support = 1.0 if tuple(sorted((source, target))) in bridges else 0.0
    self_loop_penalty = 0.25 if source == target else 0.0

    score = (
        weight_support * 0.70
        + bridge_support * 0.30
        - self_loop_penalty
    )

    return clamp(score)


def classify_coherence(score: float) -> str:
    """Classify one coherence score."""
    if score >= 0.70:
        return "core"

    if score >= 0.35:
        return "adaptive"

    return "peripheral"


def region_ratio(regions: list[str], region: str) -> float:
    """Return ratio of records in a region."""
    if not regions:
        return 0.0

    return regions.count(region) / len(regions)


def int_or_self(value: str) -> int | str:
    """Convert numeric strings to int when possible."""
    try:
        return int(value)
    except ValueError:
        return value


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))