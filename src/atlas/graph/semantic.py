"""Unified semantic graph primitives for Atlas."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


ATLAS_GRAPH_VERSION = "0.1"


@dataclass(frozen=True)
class AtlasNode:
    """One semantic Atlas graph node."""

    id: str
    kind: str
    label: str
    weight: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe node payload."""
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "weight": self.weight,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class AtlasEdge:
    """One semantic Atlas graph edge."""

    id: str
    source: str
    target: str
    kind: str
    weight: float = 1.0
    attributes: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe edge payload."""
        return {
            "id": self.id,
            "source": self.source,
            "target": self.target,
            "kind": self.kind,
            "weight": self.weight,
            "attributes": self.attributes,
        }


@dataclass(frozen=True)
class AtlasGraph:
    """Unified semantic graph representation for Atlas."""

    nodes: tuple[AtlasNode, ...]
    edges: tuple[AtlasEdge, ...]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def node_count(self) -> int:
        """Return node count."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Return edge count."""
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe graph payload."""
        return {
            "version": ATLAS_GRAPH_VERSION,
            "nodes": {
                node.id: node.to_dict()
                for node in self.nodes
            },
            "edges": {
                edge.id: edge.to_dict()
                for edge in self.edges
            },
            "summary": {
                "node_count": self.node_count,
                "edge_count": self.edge_count,
            },
            "metadata": self.metadata,
        }
