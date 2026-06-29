"""Similarity functions for topology graphs."""

import math

from atlas.resonance.vector import build_topology_vector, vector_to_tuple
from atlas.topology.graph import Edge, Node, TopologyGraph


def node_jaccard_similarity(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return Jaccard similarity between graph node sets."""
    return _jaccard(set(graph_a.nodes), set(graph_b.nodes))


def edge_jaccard_similarity(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return Jaccard similarity between graph edge sets."""
    return _jaccard(set(graph_a.edges), set(graph_b.edges))


def node_weight_similarity(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return similarity between node weight maps."""
    nodes = tuple(dict.fromkeys(graph_a.nodes + graph_b.nodes))

    if not nodes:
        return 1.0

    return _weighted_map_similarity(
        keys=nodes,
        values_a=graph_a.node_weights,
        values_b=graph_b.node_weights,
    )


def edge_weight_similarity(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return similarity between edge weight maps."""
    edges = tuple(dict.fromkeys(graph_a.edges + graph_b.edges))

    if not edges:
        return 1.0

    return _weighted_map_similarity(
        keys=edges,
        values_a=graph_a.edge_weights,
        values_b=graph_b.edge_weights,
    )


def topology_vector_similarity(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
) -> float:
    """Return cosine similarity between topology vectors normalized to 0-1."""
    vector_a = vector_to_tuple(build_topology_vector(graph_a))
    vector_b = vector_to_tuple(build_topology_vector(graph_b))

    return _cosine_similarity_0_1(vector_a, vector_b)


def _jaccard(values_a: set, values_b: set) -> float:
    """Return Jaccard similarity for two sets."""
    if not values_a and not values_b:
        return 1.0

    union = values_a | values_b

    if not union:
        return 1.0

    intersection = values_a & values_b

    return len(intersection) / len(union)


def _weighted_map_similarity(
    keys: tuple[Node, ...] | tuple[Edge, ...],
    values_a: dict,
    values_b: dict,
) -> float:
    """Return normalized similarity between two weighted maps."""
    total_similarity = 0.0

    for key in keys:
        value_a = values_a.get(key, 0)
        value_b = values_b.get(key, 0)
        max_value = max(value_a, value_b)

        if max_value == 0:
            total_similarity += 1.0
        else:
            total_similarity += 1 - abs(value_a - value_b) / max_value

    return total_similarity / len(keys)


def _cosine_similarity_0_1(
    vector_a: tuple[float, ...],
    vector_b: tuple[float, ...],
) -> float:
    """Return cosine similarity mapped into 0.0-1.0 range."""
    dot_product = sum(a * b for a, b in zip(vector_a, vector_b))
    magnitude_a = math.sqrt(sum(a * a for a in vector_a))
    magnitude_b = math.sqrt(sum(b * b for b in vector_b))

    if magnitude_a == 0 and magnitude_b == 0:
        return 1.0

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    cosine = dot_product / (magnitude_a * magnitude_b)

    return max(0.0, min(1.0, cosine))