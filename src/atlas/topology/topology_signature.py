"""Canonical topology signatures for Atlas IdentityGraph objects."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any


@dataclass(frozen=True)
class TopologySignature:
    """Canonical graph-space signature for an IdentityGraph."""

    node_ids: tuple[str, ...]
    edge_ids: tuple[str, ...]
    hub_ids: tuple[str, ...]
    bridge_ids: tuple[str, ...]
    articulation_ids: tuple[str, ...]
    leaf_ids: tuple[str, ...]
    node_weight_rank: tuple[str, ...]
    edge_weight_rank: tuple[str, ...]
    node_count: int
    edge_count: int
    density: float
    average_degree: float


@dataclass(frozen=True)
class TopologySignatureSimilarity:
    """Similarity between two topology signatures."""

    node_overlap: float
    edge_overlap: float
    hub_overlap: float
    bridge_overlap: float
    articulation_overlap: float
    leaf_overlap: float
    node_rank_similarity: float
    edge_rank_similarity: float
    density_similarity: float
    degree_similarity: float
    structural_similarity: float


def build_topology_signature(graph: dict[str, Any]) -> TopologySignature:
    """Build a canonical topology signature from an analyzed IdentityGraph."""
    nodes = graph.get("nodes", {})
    edges = graph.get("edges", {})

    node_ids = tuple(sorted(nodes))
    edge_ids = tuple(sorted(edges))

    hub_ids = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_hub") is True
        )
    )

    articulation_ids = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_articulation") is True
        )
    )

    leaf_ids = tuple(
        sorted(
            node_id
            for node_id, node in nodes.items()
            if node.get("is_leaf") is True
        )
    )

    bridge_ids = tuple(
        sorted(
            edge_id
            for edge_id, edge in edges.items()
            if edge.get("is_bridge") is True
        )
    )

    node_weight_rank = tuple(
        node_id
        for node_id, _ in sorted(
            nodes.items(),
            key=lambda item: (
                item[1].get("weight", 0),
                item[1].get("cipher_count", 0),
                item[1].get("planet_count", 0),
                item[0],
            ),
            reverse=True,
        )
    )

    edge_weight_rank = tuple(
        edge_id
        for edge_id, _ in sorted(
            edges.items(),
            key=lambda item: (
                item[1].get("weight", 0),
                item[1].get("cipher_count", 0),
                item[1].get("planet_count", 0),
                item[0],
            ),
            reverse=True,
        )
    )

    node_count = len(node_ids)
    edge_count = len(edge_ids)
    density = _density(node_count, edge_count)

    degrees = [
        float(node.get("degree", 0))
        for node in nodes.values()
    ]

    average_degree = _mean(degrees)

    return TopologySignature(
        node_ids=node_ids,
        edge_ids=edge_ids,
        hub_ids=hub_ids,
        bridge_ids=bridge_ids,
        articulation_ids=articulation_ids,
        leaf_ids=leaf_ids,
        node_weight_rank=node_weight_rank,
        edge_weight_rank=edge_weight_rank,
        node_count=node_count,
        edge_count=edge_count,
        density=density,
        average_degree=average_degree,
    )


def compare_topology_signatures(
    signature_a: TopologySignature,
    signature_b: TopologySignature,
) -> TopologySignatureSimilarity:
    """Compare two canonical topology signatures."""
    node_overlap = _jaccard(signature_a.node_ids, signature_b.node_ids)
    edge_overlap = _jaccard(signature_a.edge_ids, signature_b.edge_ids)
    hub_overlap = _jaccard(signature_a.hub_ids, signature_b.hub_ids)
    bridge_overlap = _jaccard(signature_a.bridge_ids, signature_b.bridge_ids)
    articulation_overlap = _jaccard(
        signature_a.articulation_ids,
        signature_b.articulation_ids,
    )
    leaf_overlap = _jaccard(signature_a.leaf_ids, signature_b.leaf_ids)

    node_rank_similarity = _rank_similarity(
        signature_a.node_weight_rank,
        signature_b.node_weight_rank,
    )
    edge_rank_similarity = _rank_similarity(
        signature_a.edge_weight_rank,
        signature_b.edge_weight_rank,
    )

    density_similarity = _bounded_difference_similarity(
        signature_a.density,
        signature_b.density,
    )
    degree_similarity = _bounded_difference_similarity(
        signature_a.average_degree,
        signature_b.average_degree,
        scale=max(signature_a.average_degree, signature_b.average_degree, 1.0),
    )

    structural_similarity = _mean(
        [
            node_overlap,
            edge_overlap,
            hub_overlap,
            bridge_overlap,
            articulation_overlap,
            leaf_overlap,
            node_rank_similarity,
            edge_rank_similarity,
            density_similarity,
            degree_similarity,
        ]
    )

    return TopologySignatureSimilarity(
        node_overlap=node_overlap,
        edge_overlap=edge_overlap,
        hub_overlap=hub_overlap,
        bridge_overlap=bridge_overlap,
        articulation_overlap=articulation_overlap,
        leaf_overlap=leaf_overlap,
        node_rank_similarity=node_rank_similarity,
        edge_rank_similarity=edge_rank_similarity,
        density_similarity=density_similarity,
        degree_similarity=degree_similarity,
        structural_similarity=structural_similarity,
    )


def topology_signature_to_dict(signature: TopologySignature) -> dict[str, Any]:
    """Convert topology signature to JSON-safe dictionary."""
    return {
        "node_ids": list(signature.node_ids),
        "edge_ids": list(signature.edge_ids),
        "hub_ids": list(signature.hub_ids),
        "bridge_ids": list(signature.bridge_ids),
        "articulation_ids": list(signature.articulation_ids),
        "leaf_ids": list(signature.leaf_ids),
        "node_weight_rank": list(signature.node_weight_rank),
        "edge_weight_rank": list(signature.edge_weight_rank),
        "node_count": signature.node_count,
        "edge_count": signature.edge_count,
        "density": signature.density,
        "average_degree": signature.average_degree,
    }


def topology_signature_similarity_to_dict(
    similarity: TopologySignatureSimilarity,
) -> dict[str, float]:
    """Convert topology signature similarity to JSON-safe dictionary."""
    return {
        "node_overlap": similarity.node_overlap,
        "edge_overlap": similarity.edge_overlap,
        "hub_overlap": similarity.hub_overlap,
        "bridge_overlap": similarity.bridge_overlap,
        "articulation_overlap": similarity.articulation_overlap,
        "leaf_overlap": similarity.leaf_overlap,
        "node_rank_similarity": similarity.node_rank_similarity,
        "edge_rank_similarity": similarity.edge_rank_similarity,
        "density_similarity": similarity.density_similarity,
        "degree_similarity": similarity.degree_similarity,
        "structural_similarity": similarity.structural_similarity,
    }


def _jaccard(a: tuple[str, ...], b: tuple[str, ...]) -> float:
    """Return Jaccard overlap between two item sets."""
    set_a = set(a)
    set_b = set(b)

    if not set_a and not set_b:
        return 1.0

    union = set_a | set_b

    if not union:
        return 0.0

    return len(set_a & set_b) / len(union)


def _rank_similarity(
    rank_a: tuple[str, ...],
    rank_b: tuple[str, ...],
) -> float:
    """Compare weighted rank order using shared item rank distances."""
    shared = sorted(set(rank_a) & set(rank_b))

    if not shared:
        return 0.0

    positions_a = {
        item: index
        for index, item in enumerate(rank_a)
    }
    positions_b = {
        item: index
        for index, item in enumerate(rank_b)
    }

    max_length = max(len(rank_a), len(rank_b), 1)

    squared = sum(
        (
            positions_a[item] - positions_b[item]
        ) ** 2
        for item in shared
    )

    distance = sqrt(squared) / (sqrt(len(shared)) * max_length)

    return _clamp_01(1.0 - distance)


def _bounded_difference_similarity(
    value_a: float,
    value_b: float,
    scale: float = 1.0,
) -> float:
    """Return similarity from bounded absolute difference."""
    if scale == 0:
        return 1.0 if value_a == value_b else 0.0

    return _clamp_01(1.0 - abs(value_a - value_b) / scale)


def _density(node_count: int, edge_count: int) -> float:
    """Return undirected density approximation."""
    if node_count <= 1:
        return 0.0

    possible_edges = node_count * (node_count - 1) / 2

    if possible_edges == 0:
        return 0.0

    return edge_count / possible_edges


def _mean(values: list[float]) -> float:
    """Return arithmetic mean."""
    if not values:
        return 0.0

    return sum(values) / len(values)


def _clamp_01(value: float) -> float:
    """Clamp value to 0-1."""
    return max(0.0, min(1.0, float(value)))