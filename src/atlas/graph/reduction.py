"""Structural reduction engine for Atlas IdentityGraph v2.

Reduction is visual/topological simplification. It does not replace the raw
construction graph. It produces a reduced copy and records every step.
"""

from __future__ import annotations

from typing import Any

from atlas.graph.analysis import analyze_identity_graph


MAX_REDUCTION_ITERATIONS = 50


def reduce_identity_graph(
    graph: dict[str, Any],
    max_iterations: int = MAX_REDUCTION_ITERATIONS,
) -> dict[str, Any]:
    """Iteratively reduce an IdentityGraph until stable."""
    reduced = graph_copy(graph)
    reduction_history = []

    for iteration in range(max_iterations):
        analyzed = analyze_identity_graph(reduced)
        removable_nodes = find_removable_leaf_noise(analyzed)

        if not removable_nodes:
            reduced = analyzed
            reduction_history.append(
                {
                    "iteration": iteration,
                    "removed_nodes": [],
                    "removed_edges": [],
                    "stable": True,
                }
            )
            break

        removed_edges = remove_nodes(reduced, removable_nodes)

        reduction_history.append(
            {
                "iteration": iteration,
                "removed_nodes": sorted(removable_nodes),
                "removed_edges": sorted(removed_edges),
                "stable": False,
            }
        )

    final = analyze_identity_graph(reduced)
    final["reduction"] = {
        "version": "1.0",
        "iterations": len(reduction_history),
        "history": reduction_history,
        "raw_node_count": len(graph["nodes"]),
        "raw_edge_count": len(graph["edges"]),
        "reduced_node_count": len(final["nodes"]),
        "reduced_edge_count": len(final["edges"]),
        "removed_node_count": len(graph["nodes"]) - len(final["nodes"]),
        "removed_edge_count": len(graph["edges"]) - len(final["edges"]),
        "converged": (
            bool(reduction_history)
            and reduction_history[-1]["stable"] is True
        ),
    }

    return final


def find_removable_leaf_noise(
    analyzed_graph: dict[str, Any],
) -> set[str]:
    """Find low-coherence leaf nodes that can be removed safely.

    First pass rule:
    remove nodes that are:
    - leaves
    - weight 1
    - not articulation points
    - connected to the largest component or peripheral component

    This intentionally starts conservatively.
    """
    removable = set()

    for node_id, node in analyzed_graph["nodes"].items():
        if is_removable_leaf_noise(node):
            removable.add(node_id)

    return removable


def is_removable_leaf_noise(node: dict[str, Any]) -> bool:
    """Return whether a node is removable first-pass noise."""
    return (
        node.get("is_leaf") is True
        and node.get("weight", 0) <= 1
        and node.get("is_articulation") is False
        and node.get("cipher_count", 0) <= 1
        and node.get("planet_count", 0) <= 1
    )


def remove_nodes(
    graph: dict[str, Any],
    node_ids: set[str],
) -> set[str]:
    """Remove nodes and all attached edges from graph."""
    removed_edges = set()

    for node_id in node_ids:
        graph["nodes"].pop(node_id, None)

    for edge_id, edge in list(graph["edges"].items()):
        if edge["source"] in node_ids or edge["target"] in node_ids:
            removed_edges.add(edge_id)
            graph["edges"].pop(edge_id, None)

    graph["summary"] = build_reduced_summary(graph)

    return removed_edges


def build_reduced_summary(graph: dict[str, Any]) -> dict[str, Any]:
    """Build lightweight summary after reduction."""
    nodes = list(graph["nodes"].values())
    edges = list(graph["edges"].values())

    return {
        **graph.get("summary", {}),
        "node_count": len(nodes),
        "edge_count": len(edges),
        "max_node_weight": max([node["weight"] for node in nodes], default=0),
        "max_edge_weight": max([edge["weight"] for edge in edges], default=0),
    }


def graph_copy(graph: dict[str, Any]) -> dict[str, Any]:
    """Copy an IdentityGraph v2 without mutating the original."""
    return {
        "name": graph["name"],
        "version": graph["version"],
        "nodes": {
            node_id: copy_record(node)
            for node_id, node in graph["nodes"].items()
        },
        "edges": {
            edge_id: copy_record(edge)
            for edge_id, edge in graph["edges"].items()
        },
        "construction_passes": [
            dict(item)
            for item in graph["construction_passes"]
        ],
        "summary": dict(graph["summary"]),
    }


def copy_record(record: dict[str, Any]) -> dict[str, Any]:
    """Copy a node or edge record."""
    output = {}

    for key, value in record.items():
        if isinstance(value, list):
            output[key] = [
                dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        elif isinstance(value, dict):
            output[key] = dict(value)
        else:
            output[key] = value

    return output