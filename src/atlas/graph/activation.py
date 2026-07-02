"""Graph activation utilities for unified AtlasGraph objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.graph.semantic import AtlasGraph


GRAPH_ACTIVATION_VERSION = "0.1"


@dataclass(frozen=True)
class ActivatedNode:
    """Activation state for one graph node."""

    node_id: str
    activation: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe node activation payload."""
        return {
            "node_id": self.node_id,
            "activation": self.activation,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class ActivatedEdge:
    """Activation state for one graph edge."""

    edge_id: str
    source: str
    target: str
    activation: float
    reasons: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe edge activation payload."""
        return {
            "edge_id": self.edge_id,
            "source": self.source,
            "target": self.target,
            "activation": self.activation,
            "reasons": list(self.reasons),
        }


@dataclass(frozen=True)
class GraphActivation:
    """Graph activation result."""

    node_activations: tuple[ActivatedNode, ...]
    edge_activations: tuple[ActivatedEdge, ...]
    summary: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe graph activation payload."""
        return {
            "version": GRAPH_ACTIVATION_VERSION,
            "node_activations": [
                node.to_dict()
                for node in self.node_activations
            ],
            "edge_activations": [
                edge.to_dict()
                for edge in self.edge_activations
            ],
            "summary": self.summary,
            "metadata": self.metadata,
        }


def build_graph_activation(
    graph: AtlasGraph,
) -> GraphActivation:
    """Build deterministic activation from an AtlasGraph."""
    edge_activations = tuple(
        _activate_edge(edge)
        for edge in graph.edges
    )

    node_scores: dict[str, float] = {
        node.id: 0.0
        for node in graph.nodes
    }

    node_reasons: dict[str, list[str]] = {
        node.id: []
        for node in graph.nodes
    }

    for node in graph.nodes:
        base = max(0.0, float(node.weight))
        if base > 0:
            node_scores[node.id] += base
            node_reasons[node.id].append("node_weight")

    for edge_activation in edge_activations:
        propagated = edge_activation.activation / 2.0

        node_scores[edge_activation.source] = (
            node_scores.get(edge_activation.source, 0.0)
            + propagated
        )
        node_scores[edge_activation.target] = (
            node_scores.get(edge_activation.target, 0.0)
            + propagated
        )

        node_reasons.setdefault(edge_activation.source, []).append(
            f"edge:{edge_activation.edge_id}"
        )
        node_reasons.setdefault(edge_activation.target, []).append(
            f"edge:{edge_activation.edge_id}"
        )

    node_activations = tuple(
        ActivatedNode(
            node_id=node_id,
            activation=activation,
            reasons=tuple(node_reasons.get(node_id, [])),
        )
        for node_id, activation in sorted(
            node_scores.items(),
            key=lambda item: (-item[1], item[0]),
        )
        if activation > 0
    )

    max_node_activation = (
        node_activations[0].activation
        if node_activations
        else 0.0
    )

    activation_center = (
        node_activations[0].node_id
        if node_activations
        else None
    )

    return GraphActivation(
        node_activations=node_activations,
        edge_activations=edge_activations,
        summary={
            "activated_node_count": len(node_activations),
            "activated_edge_count": len(edge_activations),
            "max_node_activation": max_node_activation,
            "activation_center": activation_center,
            "total_node_activation": sum(
                node.activation
                for node in node_activations
            ),
            "total_edge_activation": sum(
                edge.activation
                for edge in edge_activations
            ),
        },
        metadata={
            "activation_version": GRAPH_ACTIVATION_VERSION,
            "graph_type": graph.metadata.get("graph_type"),
            "profile_key": graph.metadata.get("profile_key"),
        },
    )


def _activate_edge(edge) -> ActivatedEdge:
    """Build activation for one graph edge."""
    reasons: list[str] = ["edge_weight"]
    activation = max(0.0, float(edge.weight))

    if edge.kind == "transit_contact":
        reasons.append("transit_contact")

        if edge.attributes.get("same_sign"):
            activation += 1.0
            reasons.append("same_sign")

        if edge.attributes.get("opposition"):
            activation += 0.75
            reasons.append("opposition")

    return ActivatedEdge(
        edge_id=edge.id,
        source=edge.source,
        target=edge.target,
        activation=activation,
        reasons=tuple(reasons),
    )
