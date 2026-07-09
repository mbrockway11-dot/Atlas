
"""Atlas Core dependency graph."""

from __future__ import annotations

from atlas.core.node import Node


def resolve_execution_order(nodes: list[Node]) -> list[Node]:
    """Resolve node execution order from requires/provides."""
    provided_by = {}

    for node in nodes:
        for output in node.provides:
            provided_by[output] = node.name

    node_map = {node.name: node for node in nodes}
    dependencies = {node.name: set() for node in nodes}

    for node in nodes:
        for requirement in node.requires:
            provider = provided_by.get(requirement)
            if provider and provider != node.name:
                dependencies[node.name].add(provider)

    resolved = []
    remaining = set(node_map.keys())

    while remaining:
        ready = sorted([
            name for name in remaining
            if dependencies[name].issubset({n.name for n in resolved})
        ])

        if not ready:
            raise ValueError(f"Circular or unresolved dependency graph: {dependencies}")

        for name in ready:
            resolved.append(node_map[name])
            remaining.remove(name)

    return resolved
