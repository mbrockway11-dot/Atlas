"""Motif detection for Atlas IdentityGraph v2."""

from __future__ import annotations

from collections import Counter
from typing import Any


def detect_identity_graph_motifs(
    graph: dict[str, Any],
) -> dict[str, Any]:
    """Detect motifs from an analyzed IdentityGraph v2."""
    nodes = graph["nodes"]
    edges = graph["edges"]

    motifs = {
        "chains": detect_chain_motifs(nodes),
        "hubs": detect_hub_motifs(nodes),
        "leaves": detect_leaf_motifs(nodes),
        "bridges": detect_bridge_motifs(edges),
        "articulations": detect_articulation_motifs(nodes),
        "reciprocal_pairs": detect_reciprocal_edge_motifs(edges),
    }

    return {
        "motifs": motifs,
        "summary": build_identity_motif_summary(motifs),
    }


def detect_chain_motifs(
    nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect pass-through chain nodes."""
    return [
        build_node_motif("chain", node)
        for node in nodes.values()
        if node.get("in_degree") == 1
        and node.get("out_degree") == 1
    ]


def detect_hub_motifs(
    nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect hub nodes."""
    return [
        build_node_motif("hub", node)
        for node in nodes.values()
        if node.get("is_hub") is True
    ]


def detect_leaf_motifs(
    nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect leaf nodes."""
    return [
        build_node_motif("leaf", node)
        for node in nodes.values()
        if node.get("is_leaf") is True
    ]


def detect_articulation_motifs(
    nodes: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect articulation point motifs."""
    return [
        build_node_motif("articulation", node)
        for node in nodes.values()
        if node.get("is_articulation") is True
    ]


def detect_bridge_motifs(
    edges: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect bridge edge motifs."""
    return [
        build_edge_motif("bridge", edge)
        for edge in edges.values()
        if edge.get("is_bridge") is True
    ]


def detect_reciprocal_edge_motifs(
    edges: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    """Detect reciprocal edge motifs."""
    edge_pairs = {
        (edge["source"], edge["target"])
        for edge in edges.values()
    }

    seen = set()
    motifs = []

    for source, target in edge_pairs:
        if source == target:
            continue

        forward = (source, target)
        reverse = (target, source)

        if forward in seen or reverse in seen:
            continue

        if reverse in edge_pairs:
            motifs.append(
                {
                    "type": "reciprocal_pair",
                    "nodes": sorted([source, target]),
                    "edges": [
                        f"{source}->{target}",
                        f"{target}->{source}",
                    ],
                    "size": 2,
                }
            )
            seen.add(forward)
            seen.add(reverse)

    return motifs


def build_node_motif(
    motif_type: str,
    node: dict[str, Any],
) -> dict[str, Any]:
    """Build node motif record."""
    return {
        "type": motif_type,
        "node": node["id"],
        "weight": node.get("weight", 0),
        "degree": node.get("degree", 0),
        "in_degree": node.get("in_degree", 0),
        "out_degree": node.get("out_degree", 0),
        "cipher_count": node.get("cipher_count", 0),
        "planet_count": node.get("planet_count", 0),
        "coherence": node.get("coherence", {}),
    }


def build_edge_motif(
    motif_type: str,
    edge: dict[str, Any],
) -> dict[str, Any]:
    """Build edge motif record."""
    return {
        "type": motif_type,
        "edge": edge["id"],
        "source": edge["source"],
        "target": edge["target"],
        "weight": edge.get("weight", 0),
        "cipher_count": edge.get("cipher_count", 0),
        "planet_count": edge.get("planet_count", 0),
        "coherence": edge.get("coherence", {}),
    }


def build_identity_motif_summary(
    motifs: dict[str, list[dict[str, Any]]],
) -> dict[str, Any]:
    """Build motif summary."""
    counts = {
        motif_type: len(records)
        for motif_type, records in motifs.items()
    }

    total = sum(counts.values())

    dominant = "none"
    if counts:
        dominant = max(counts.items(), key=lambda item: item[1])[0]

    return {
        "total_motifs": total,
        "counts": counts,
        "dominant_motif": dominant,
    }
