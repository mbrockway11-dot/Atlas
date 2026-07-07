
"""Research provenance lineage."""

from __future__ import annotations

from typing import Any


def create_lineage() -> dict[str, Any]:
    """Create empty lineage graph."""
    return {
        "success": True,
        "relations": [],
    }


def add_relation(
    lineage: dict[str, Any],
    parent_id: str,
    child_id: str,
    *,
    relation: str = "supports",
    weight: float = 1.0,
) -> dict[str, Any]:
    """Add parent-child relation."""
    lineage.setdefault("relations", []).append(
        {
            "parent": parent_id,
            "child": child_id,
            "relation": relation,
            "weight": float(weight),
        }
    )
    return lineage


def trace_ancestors(lineage: dict[str, Any], object_id: str) -> list[dict[str, Any]]:
    """Trace all ancestors for an object."""
    relations = lineage.get("relations", []) or []
    results = []
    visited = set()

    def walk(current_id: str) -> None:
        for rel in relations:
            if rel.get("child") == current_id:
                parent = rel.get("parent")
                if parent and parent not in visited:
                    visited.add(parent)
                    results.append(rel)
                    walk(parent)

    walk(object_id)
    return results


def trace_descendants(lineage: dict[str, Any], object_id: str) -> list[dict[str, Any]]:
    """Trace all descendants for an object."""
    relations = lineage.get("relations", []) or []
    results = []
    visited = set()

    def walk(current_id: str) -> None:
        for rel in relations:
            if rel.get("parent") == current_id:
                child = rel.get("child")
                if child and child not in visited:
                    visited.add(child)
                    results.append(rel)
                    walk(child)

    walk(object_id)
    return results
