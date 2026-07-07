
"""Research provenance graph builder."""

from __future__ import annotations

from typing import Any


def build_provenance_graph(
    registry: dict[str, Any],
    lineage: dict[str, Any],
) -> dict[str, Any]:
    """Build graph from registry and lineage."""
    objects = registry.get("objects", {}) or {}

    nodes = [
        {
            "id": object_id,
            "type": item.get("type"),
            "label": item.get("label"),
        }
        for object_id, item in objects.items()
    ]

    edges = [
        {
            "source": rel.get("parent"),
            "target": rel.get("child"),
            "relation": rel.get("relation"),
            "weight": rel.get("weight", 1.0),
        }
        for rel in lineage.get("relations", []) or []
    ]

    return {
        "success": True,
        "nodes": nodes,
        "edges": edges,
        "summary": {
            "node_count": len(nodes),
            "edge_count": len(edges),
            "object_types": count_types(nodes),
        },
    }


def count_types(nodes: list[dict[str, Any]]) -> dict[str, int]:
    """Count node types."""
    counts: dict[str, int] = {}

    for node in nodes:
        key = str(node.get("type", "unknown"))
        counts[key] = counts.get(key, 0) + 1

    return counts
