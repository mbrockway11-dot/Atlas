"""Coherence engine for Atlas IdentityGraph v2.

Coherence measures how structurally essential a node or edge is to the
single merged IdentityGraph.

It is different from resonance:
- coherence = structural contribution
- resonance = propagation / activation through the field
"""

from __future__ import annotations

from typing import Any

from atlas.graph.analysis import analyze_identity_graph


def compute_coherence_field(
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Return graph enriched with node and edge coherence."""
    analyzed = analyze_identity_graph(graph)

    for node in analyzed["nodes"].values():
        node["coherence"] = compute_node_coherence(node)

    for edge in analyzed["edges"].values():
        edge["coherence"] = compute_edge_coherence(edge)

    analyzed["coherence"] = build_coherence_summary(analyzed)

    return analyzed


def compute_node_coherence(node: dict[str, Any]) -> dict[str, Any]:
    """Compute node coherence components."""
    construction_support = normalized(
        node.get("weight", 0),
        21,
    )

    cipher_support = normalized(
        node.get("cipher_count", 0),
        3,
    )

    planet_support = normalized(
        node.get("planet_count", 0),
        7,
    )

    degree_support = normalized(
        node.get("degree", 0),
        6,
    )

    bridge_support = 1.0 if node.get("is_articulation") else 0.0
    hub_support = 1.0 if node.get("is_hub") else 0.0
    leaf_penalty = 0.35 if node.get("is_leaf") else 0.0

    score = (
        construction_support * 0.25
        + cipher_support * 0.20
        + planet_support * 0.20
        + degree_support * 0.15
        + bridge_support * 0.10
        + hub_support * 0.10
        - leaf_penalty
    )

    score = clamp(score)

    return {
        "score": score,
        "region": classify_coherence(score),
        "construction_support": construction_support,
        "cipher_support": cipher_support,
        "planet_support": planet_support,
        "degree_support": degree_support,
        "bridge_support": bridge_support,
        "hub_support": hub_support,
        "leaf_penalty": leaf_penalty,
    }


def compute_edge_coherence(edge: dict[str, Any]) -> dict[str, Any]:
    """Compute edge coherence components."""
    construction_support = normalized(
        edge.get("weight", 0),
        21,
    )

    cipher_support = normalized(
        edge.get("cipher_count", 0),
        3,
    )

    planet_support = normalized(
        edge.get("planet_count", 0),
        7,
    )

    bridge_support = 1.0 if edge.get("is_bridge") else 0.0

    score = (
        construction_support * 0.35
        + cipher_support * 0.25
        + planet_support * 0.25
        + bridge_support * 0.15
    )

    score = clamp(score)

    return {
        "score": score,
        "region": classify_coherence(score),
        "construction_support": construction_support,
        "cipher_support": cipher_support,
        "planet_support": planet_support,
        "bridge_support": bridge_support,
    }


def build_coherence_summary(
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Build coherence summary."""
    nodes = list(graph["nodes"].values())
    edges = list(graph["edges"].values())

    return {
        "node_count": len(nodes),
        "edge_count": len(edges),
        "core_node_count": count_region(nodes, "core"),
        "core_edge_count": count_region(edges, "core"),
        "adaptive_node_count": count_region(nodes, "adaptive"),
        "adaptive_edge_count": count_region(edges, "adaptive"),
        "peripheral_node_count": count_region(nodes, "peripheral"),
        "peripheral_edge_count": count_region(edges, "peripheral"),
        "top_nodes": top_by_coherence(nodes),
        "top_edges": top_by_coherence(edges),
    }


def count_region(
    records: list[dict[str, Any]],
    region: str,
) -> int:
    """Count records in coherence region."""
    return len(
        [
            record
            for record in records
            if record["coherence"]["region"] == region
        ]
    )


def top_by_coherence(
    records: list[dict[str, Any]],
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Return top records by coherence score."""
    return sorted(
        records,
        key=lambda record: record["coherence"]["score"],
        reverse=True,
    )[:limit]


def classify_coherence(score: float) -> str:
    """Classify coherence score."""
    if score >= 0.70:
        return "core"

    if score >= 0.35:
        return "adaptive"

    return "peripheral"


def normalized(
    value: float,
    maximum: float,
) -> float:
    """Normalize value to 0-1."""
    if maximum <= 0:
        return 0.0

    return clamp(float(value) / maximum)


def clamp(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, value))