
"""Atlas Core pipeline."""

from __future__ import annotations

from atlas.core.dependency_graph import resolve_execution_order
from atlas.core.node import Node
from atlas.core.registry import NodeRegistry


class Pipeline:
    def __init__(self, registry: NodeRegistry) -> None:
        self.registry = registry

    def execution_order(self) -> list[Node]:
        return resolve_execution_order(self.registry.all())
