"""Graph resonance comparison for propagated activation fields."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.graph.propagation import PropagationResult


GRAPH_RESONANCE_VERSION = "0.1"


@dataclass(frozen=True)
class GraphResonance:
    """Resonance comparison between two propagation fields."""

    overall_score: float
    node_overlap: float
    activation_overlap: float
    shared_nodes: tuple[str, ...]
    unique_left: tuple[str, ...]
    unique_right: tuple[str, ...]
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe resonance payload."""
        return {
            "version": GRAPH_RESONANCE_VERSION,
            "overall_score": self.overall_score,
            "node_overlap": self.node_overlap,
            "activation_overlap": self.activation_overlap,
            "shared_nodes": list(self.shared_nodes),
            "unique_left": list(self.unique_left),
            "unique_right": list(self.unique_right),
            "summary": self.summary,
        }


def compute_graph_resonance(
    left: PropagationResult,
    right: PropagationResult,
) -> GraphResonance:
    """Compute deterministic resonance between two propagation fields."""
    left_nodes = set(left.node_scores)
    right_nodes = set(right.node_scores)

    shared = tuple(sorted(left_nodes & right_nodes))
    unique_left = tuple(sorted(left_nodes - right_nodes))
    unique_right = tuple(sorted(right_nodes - left_nodes))

    node_overlap = _jaccard(left_nodes, right_nodes)
    activation_overlap = _activation_overlap(
        left.node_scores,
        right.node_scores,
        shared,
    )

    overall_score = (
        0.5 * node_overlap
        + 0.5 * activation_overlap
    )

    return GraphResonance(
        overall_score=overall_score,
        node_overlap=node_overlap,
        activation_overlap=activation_overlap,
        shared_nodes=shared,
        unique_left=unique_left,
        unique_right=unique_right,
        summary={
            "shared_node_count": len(shared),
            "unique_left_count": len(unique_left),
            "unique_right_count": len(unique_right),
            "resonance_status": "computed",
        },
    )


def _jaccard(
    left: set[str],
    right: set[str],
) -> float:
    """Return Jaccard overlap."""
    if not left and not right:
        return 1.0

    union = left | right

    if not union:
        return 0.0

    return len(left & right) / len(union)


def _activation_overlap(
    left_scores: dict[str, float],
    right_scores: dict[str, float],
    shared_nodes: tuple[str, ...],
) -> float:
    """Return average activation similarity across shared nodes."""
    if not shared_nodes:
        return 0.0

    similarities = []

    for node_id in shared_nodes:
        left = float(left_scores.get(node_id, 0.0))
        right = float(right_scores.get(node_id, 0.0))

        similarities.append(
            max(0.0, 1.0 - abs(left - right))
        )

    return sum(similarities) / len(similarities)
