"""Layer-level structural attractor metrics for Atlas research rows."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from atlas.research.graph_metrics import (
    build_undirected_adjacency,
    connected_component_sizes,
    safe_ratio,
)
from atlas.research.reduction_metrics import (
    build_layer_reduction_graph,
    is_collapsed,
)


def build_layer_attractor_metrics(layer: dict[str, Any]) -> dict[str, Any]:
    """Build structural attractor metrics for one construction layer."""
    graph = build_layer_reduction_graph(layer)

    initial_node_count = len(graph["nodes"])
    initial_edge_count = len(graph["edges"])

    if initial_node_count == 0:
        return empty_attractor_metrics()

    attractor = extract_layer_attractor(graph)

    attractor_nodes = attractor["nodes"]
    attractor_edges = attractor["edges"]
    node_scores = graph["node_scores"]

    attractor_node_scores = [
        node_scores.get(node, 0.0)
        for node in attractor_nodes
    ]

    attractor_node_count = len(attractor_nodes)
    attractor_edge_count = len(attractor_edges)

    return {
        "attractor_node_count": attractor_node_count,
        "attractor_edge_count": attractor_edge_count,
        "attractor_node_ratio": safe_ratio(
            attractor_node_count,
            initial_node_count,
        ),
        "attractor_edge_ratio": safe_ratio(
            attractor_edge_count,
            initial_edge_count,
        ),
        "attractor_density": graph_density(
            attractor_node_count,
            attractor_edge_count,
        ),
        "attractor_mean_node_score": (
            sum(attractor_node_scores) / len(attractor_node_scores)
            if attractor_node_scores
            else 0.0
        ),
        "attractor_min_node_score": (
            min(attractor_node_scores)
            if attractor_node_scores
            else 0.0
        ),
        "attractor_max_node_score": (
            max(attractor_node_scores)
            if attractor_node_scores
            else 0.0
        ),
        "attractor_stability": attractor["stability"],
        "attractor_signature": build_attractor_signature(
            attractor_nodes,
            attractor_edges,
        ),
    }


def extract_layer_attractor(graph: dict[str, Any]) -> dict[str, Any]:
    """Extract the final stable pre-collapse attractor."""
    working_nodes = set(graph["nodes"])
    working_edges = set(graph["edges"])
    node_scores = dict(graph["node_scores"])

    stable_states = []

    iteration = 0

    while working_nodes:
        collapsed = is_collapsed(working_nodes, working_edges)

        if not collapsed:
            stable_states.append(
                {
                    "iteration": iteration,
                    "nodes": set(working_nodes),
                    "edges": set(working_edges),
                }
            )

        if collapsed or len(working_nodes) <= 1:
            break

        weakest_node = min(
            working_nodes,
            key=lambda node: (
                node_scores.get(node, 0.0),
                node,
            ),
        )

        working_nodes.remove(weakest_node)
        working_edges = {
            edge
            for edge in working_edges
            if weakest_node not in edge
        }

        iteration += 1

    if not stable_states:
        return {
            "nodes": set(),
            "edges": set(),
            "stability": 0.0,
        }

    attractor = stable_states[-1]

    return {
        "nodes": attractor["nodes"],
        "edges": attractor["edges"],
        "stability": safe_ratio(
            len(stable_states),
            max(1, iteration + 1),
        ),
    }


def graph_density(
    node_count: int,
    edge_count: int,
) -> float:
    """Compute undirected graph density."""
    if node_count <= 1:
        return 0.0

    possible_edges = node_count * (node_count - 1) / 2

    return safe_ratio(edge_count, possible_edges)


def build_attractor_signature(
    nodes: set[str],
    edges: set[tuple[str, str]],
) -> str:
    """Build deterministic structural attractor signature."""
    node_part = ",".join(sorted(nodes))
    edge_part = ",".join(
        f"{source}-{target}"
        for source, target in sorted(edges)
    )

    payload = f"nodes:{node_part}|edges:{edge_part}"

    return sha256(payload.encode("utf-8")).hexdigest()[:16]


def empty_attractor_metrics() -> dict[str, Any]:
    """Return empty attractor metrics."""
    return {
        "attractor_node_count": 0,
        "attractor_edge_count": 0,
        "attractor_node_ratio": 0.0,
        "attractor_edge_ratio": 0.0,
        "attractor_density": 0.0,
        "attractor_mean_node_score": 0.0,
        "attractor_min_node_score": 0.0,
        "attractor_max_node_score": 0.0,
        "attractor_stability": 0.0,
        "attractor_signature": build_attractor_signature(set(), set()),
    }