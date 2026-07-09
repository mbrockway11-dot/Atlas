
"""Atlas Core node registry."""

from __future__ import annotations

from atlas.core.node import Node


class NodeRegistry:
    def __init__(self) -> None:
        self.nodes: dict[str, Node] = {}

    def register(self, node: Node) -> None:
        if node.name in self.nodes:
            raise ValueError(f"Duplicate node registered: {node.name}")
        self.nodes[node.name] = node

    def get(self, name: str) -> Node:
        return self.nodes[name]

    def all(self) -> list[Node]:
        return list(self.nodes.values())

    def names(self) -> list[str]:
        return list(self.nodes.keys())
