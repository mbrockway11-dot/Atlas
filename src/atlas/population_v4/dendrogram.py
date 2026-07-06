
"""Population Intelligence v4 dendrogram builder."""

from __future__ import annotations

from typing import Any


DENDROGRAM_VERSION = "4.0.0"


def build_cluster_dendrogram(clustering: dict[str, Any]) -> dict[str, Any]:
    """Build lightweight deterministic dendrogram tree from clusters."""
    clusters = clustering.get("clusters", []) or []

    children = []

    for cluster in clusters:
        children.append(
            {
                "id": cluster.get("cluster_id"),
                "label": cluster.get("label"),
                "member_count": cluster.get("member_count"),
                "cohesion": cluster.get("cohesion"),
                "children": [
                    {
                        "id": member,
                        "label": member,
                        "member_count": 1,
                        "cohesion": 1.0,
                        "children": [],
                    }
                    for member in cluster.get("members", [])
                ],
            }
        )

    return {
        "success": True,
        "version": DENDROGRAM_VERSION,
        "root": {
            "id": "population_root",
            "label": "Population",
            "member_count": clustering.get("profile_count", 0),
            "cluster_count": clustering.get("cluster_count", 0),
            "children": children,
        },
    }


def flatten_dendrogram(tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Flatten dendrogram into rows."""
    root = tree.get("root", {})
    rows = []

    def walk(node: dict[str, Any], depth: int) -> None:
        rows.append(
            {
                "id": node.get("id"),
                "label": node.get("label"),
                "depth": depth,
                "member_count": node.get("member_count"),
                "cohesion": node.get("cohesion"),
            }
        )

        for child in node.get("children", []) or []:
            walk(child, depth + 1)

    walk(root, 0)
    return rows
