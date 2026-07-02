"""Activation propagation for unified AtlasGraph objects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.graph.activation import GraphActivation
from atlas.graph.semantic import AtlasGraph


GRAPH_PROPAGATION_VERSION = "0.1"


@dataclass(frozen=True)
class PropagationResult:
    """Result of graph activation propagation."""

    node_scores: dict[str, float]
    top_nodes: tuple[str, ...]
    iterations: int
    decay: float
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe propagation payload."""
        return {
            "version": GRAPH_PROPAGATION_VERSION,
            "node_scores": self.node_scores,
            "top_nodes": list(self.top_nodes),
            "iterations": self.iterations,
            "decay": self.decay,
            "summary": self.summary,
        }


def propagate_activation(
    *,
    graph: AtlasGraph,
    activation: GraphActivation,
    iterations: int = 2,
    decay: float = 0.5,
    top_n: int = 10,
) -> PropagationResult:
    """Propagate activation through graph edges."""
    if iterations < 0:
        raise ValueError("iterations must be greater than or equal to zero")

    if decay < 0:
        raise ValueError("decay must be greater than or equal to zero")

    node_scores = {
        node.id: 0.0
        for node in graph.nodes
    }

    for node_activation in activation.node_activations:
        node_scores[node_activation.node_id] = (
            node_scores.get(node_activation.node_id, 0.0)
            + float(node_activation.activation)
        )

    adjacency = _build_adjacency(graph)

    for _ in range(iterations):
        propagated = dict(node_scores)

        for source, targets in adjacency.items():
            source_score = node_scores.get(source, 0.0)

            if source_score <= 0:
                continue

            for target, weight in targets:
                propagated[target] = (
                    propagated.get(target, 0.0)
                    + source_score * decay * weight
                )

        node_scores = propagated

    normalized_scores = _normalize_scores(node_scores)

    sorted_nodes = tuple(
        node_id
        for node_id, _score in sorted(
            normalized_scores.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )

    top_nodes = sorted_nodes[:top_n]

    return PropagationResult(
        node_scores=normalized_scores,
        top_nodes=top_nodes,
        iterations=iterations,
        decay=decay,
        summary={
            "node_count": len(normalized_scores),
            "top_node": top_nodes[0] if top_nodes else None,
            "max_score": (
                normalized_scores[top_nodes[0]]
                if top_nodes
                else 0.0
            ),
            "total_score": sum(normalized_scores.values()),
            "propagation_status": "computed",
        },
    )


def _build_adjacency(
    graph: AtlasGraph,
) -> dict[str, list[tuple[str, float]]]:
    """Build weighted directed adjacency list."""
    adjacency: dict[str, list[tuple[str, float]]] = {
        node.id: []
        for node in graph.nodes
    }

    for edge in graph.edges:
        adjacency.setdefault(edge.source, []).append(
            (
                edge.target,
                max(0.0, float(edge.weight)),
            )
        )

    return adjacency


def _normalize_scores(
    scores: dict[str, float],
) -> dict[str, float]:
    """Normalize scores to max 1.0 while preserving zeros."""
    max_score = max(scores.values(), default=0.0)

    if max_score <= 0:
        return {
            node_id: 0.0
            for node_id in scores
        }

    return {
        node_id: score / max_score
        for node_id, score in scores.items()
    }
