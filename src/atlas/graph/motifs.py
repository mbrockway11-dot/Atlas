"""Structural Motif Engine.

Motifs are deterministic topology patterns extracted from a Structural Truth
Graph or IdentityGraph-like object.

The engine does not interpret meaning. It measures graph structure.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from itertools import combinations
from typing import Any


MOTIF_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralMotifs:
    """Measured structural motifs for one graph."""

    version: str
    node_count: int
    edge_count: int
    hub_nodes: tuple[str, ...]
    bridge_edges: tuple[str, ...]
    articulation_nodes: tuple[str, ...]
    leaf_nodes: tuple[str, ...]
    chain_count: int
    triangle_count: int
    star_count: int
    bottleneck_count: int
    cycle_like_count: int
    summary: dict[str, Any]


def extract_structural_motifs(graph: dict[str, Any]) -> StructuralMotifs:
    """Extract deterministic motifs from a graph-like object."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", {})

    adjacency = build_undirected_adjacency(graph)

    hub_nodes = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_hub") is True
        )
    )

    bridge_edges = tuple(
        sorted(
            edge_id
            for edge_id, edge in edges.items()
            if edge.get("is_bridge") is True
        )
    )

    articulation_nodes = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_articulation") is True
        )
    )

    leaf_nodes = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_leaf") is True
        )
    )

    chain_count = count_chain_motifs(nodes, adjacency)
    triangle_count = count_triangle_motifs(adjacency)
    star_count = count_star_motifs(adjacency)
    bottleneck_count = len(articulation_nodes) + len(bridge_edges)
    cycle_like_count = count_cycle_like_motifs(nodes, edges, adjacency)

    summary = {
        "definition": (
            "Deterministic graph motif measurements extracted from a "
            "Structural Truth Graph or IdentityGraph-like object."
        ),
        "hub_count": len(hub_nodes),
        "bridge_count": len(bridge_edges),
        "articulation_count": len(articulation_nodes),
        "leaf_count": len(leaf_nodes),
        "chain_count": chain_count,
        "triangle_count": triangle_count,
        "star_count": star_count,
        "bottleneck_count": bottleneck_count,
        "cycle_like_count": cycle_like_count,
        "motif_richness": motif_richness(
            [
                len(hub_nodes),
                len(bridge_edges),
                len(articulation_nodes),
                len(leaf_nodes),
                chain_count,
                triangle_count,
                star_count,
                bottleneck_count,
                cycle_like_count,
            ]
        ),
    }

    return StructuralMotifs(
        version=MOTIF_VERSION,
        node_count=len(nodes),
        edge_count=len(edges),
        hub_nodes=hub_nodes,
        bridge_edges=bridge_edges,
        articulation_nodes=articulation_nodes,
        leaf_nodes=leaf_nodes,
        chain_count=chain_count,
        triangle_count=triangle_count,
        star_count=star_count,
        bottleneck_count=bottleneck_count,
        cycle_like_count=cycle_like_count,
        summary=summary,
    )


def build_undirected_adjacency(
    graph: dict[str, Any],
) -> dict[str, set[str]]:
    """Build undirected adjacency from graph edges."""
    adjacency = {
        node_id: set()
        for node_id in graph.get("nodes", {})
    }

    for edge in graph.get("edges", {}).values():
        source = str(edge["source"])
        target = str(edge["target"])

        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    return adjacency


def count_chain_motifs(
    nodes: dict[str, dict[str, Any]],
    adjacency: dict[str, set[str]],
) -> int:
    """Count simple degree-two chain nodes."""
    return len(
        [
            node_id
            for node_id in nodes
            if len(adjacency.get(node_id, set())) == 2
        ]
    )


def count_triangle_motifs(
    adjacency: dict[str, set[str]],
) -> int:
    """Count undirected triangle motifs."""
    triangles = set()

    for node, neighbors in adjacency.items():
        for left, right in combinations(sorted(neighbors), 2):
            if right in adjacency.get(left, set()):
                triangles.add(tuple(sorted([node, left, right])))

    return len(triangles)


def count_star_motifs(
    adjacency: dict[str, set[str]],
    min_spokes: int = 3,
) -> int:
    """Count star centers by minimum spoke count."""
    return len(
        [
            node_id
            for node_id, neighbors in adjacency.items()
            if len(neighbors) >= min_spokes
        ]
    )


def count_cycle_like_motifs(
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    adjacency: dict[str, set[str]],
) -> int:
    """Estimate independent cycle-like structures.

    Uses the undirected cyclomatic number:
    cycles = E - N + C
    where C is connected component count.
    """
    node_count = len(nodes)
    edge_count = undirected_edge_count(edges)
    component_count = count_components(adjacency)

    return max(0, edge_count - node_count + component_count)


def undirected_edge_count(
    edges: dict[str, dict[str, Any]],
) -> int:
    """Count unique undirected edges."""
    normalized = set()

    for edge in edges.values():
        normalized.add(
            tuple(
                sorted(
                    [
                        str(edge["source"]),
                        str(edge["target"]),
                    ]
                )
            )
        )

    return len(normalized)


def count_components(
    adjacency: dict[str, set[str]],
) -> int:
    """Count connected components."""
    unvisited = set(adjacency)
    components = 0

    while unvisited:
        components += 1
        stack = [unvisited.pop()]

        while stack:
            current = stack.pop()

            for neighbor in adjacency.get(current, set()):
                if neighbor in unvisited:
                    unvisited.remove(neighbor)
                    stack.append(neighbor)

    return components


def motif_richness(values: list[int]) -> float:
    """Return normalized motif richness."""
    if not values:
        return 0.0

    present = len([value for value in values if value > 0])

    return present / len(values)


def structural_motifs_to_dict(
    motifs: StructuralMotifs,
) -> dict[str, Any]:
    """Convert motifs to JSON-safe dictionary."""
    return asdict(motifs)