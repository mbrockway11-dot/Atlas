"""Composite resonance calculations."""

from dataclasses import dataclass

from atlas.resonance.alignment import structural_alignment
from atlas.resonance.similarity import (
    edge_jaccard_similarity,
    edge_weight_similarity,
    node_jaccard_similarity,
    node_weight_similarity,
    topology_vector_similarity,
)
from atlas.topology.graph import TopologyGraph


@dataclass(frozen=True)
class ResonanceResult:
    """Deterministic resonance comparison between two topology graphs."""

    overall: float
    node_similarity: float
    edge_similarity: float
    node_weight_similarity: float
    edge_weight_similarity: float
    vector_similarity: float
    alignment_similarity: float


def calculate_resonance(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> ResonanceResult:
    """Calculate deterministic resonance between two graphs."""
    node_similarity = node_jaccard_similarity(graph_a, graph_b)
    edge_similarity = edge_jaccard_similarity(graph_a, graph_b)
    node_weight = node_weight_similarity(graph_a, graph_b)
    edge_weight = edge_weight_similarity(graph_a, graph_b)
    vector_similarity = topology_vector_similarity(graph_a, graph_b)
    alignment_similarity = structural_alignment(graph_a, graph_b)

    overall = (
        node_similarity
        + edge_similarity
        + node_weight
        + edge_weight
        + vector_similarity
        + alignment_similarity
    ) / 6

    return ResonanceResult(
        overall=overall,
        node_similarity=node_similarity,
        edge_similarity=edge_similarity,
        node_weight_similarity=node_weight,
        edge_weight_similarity=edge_weight,
        vector_similarity=vector_similarity,
        alignment_similarity=alignment_similarity,
    )