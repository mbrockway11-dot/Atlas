"""Structural alignment utilities for topology graphs."""

from atlas.features.metrics import out_degree, weighted_out_degree
from atlas.signatures.fingerprint import build_topology_signature
from atlas.topology.graph import Node, TopologyGraph


def hub_alignment(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return overlap between highest outward-flow nodes."""
    hubs_a = _dominant_out_nodes(graph_a)
    hubs_b = _dominant_out_nodes(graph_b)

    if not hubs_a and not hubs_b:
        return 1.0

    if not hubs_a or not hubs_b:
        return 0.0

    return len(hubs_a & hubs_b) / len(hubs_a | hubs_b)


def pattern_alignment(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return 1.0 if dominant patterns match, else 0.0."""
    signature_a = build_topology_signature(graph_a)
    signature_b = build_topology_signature(graph_b)

    if signature_a.dominant_pattern == signature_b.dominant_pattern:
        return 1.0

    return 0.0


def motif_alignment(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return 1.0 if dominant motifs match, else 0.0."""
    signature_a = build_topology_signature(graph_a)
    signature_b = build_topology_signature(graph_b)

    if signature_a.dominant_motif == signature_b.dominant_motif:
        return 1.0

    return 0.0


def directional_alignment(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return similarity between unweighted out-degree distributions."""
    degree_a = out_degree(graph_a)
    degree_b = out_degree(graph_b)

    nodes = tuple(dict.fromkeys(graph_a.nodes + graph_b.nodes))

    if not nodes:
        return 1.0

    total = 0.0

    for node in nodes:
        value_a = degree_a.get(node, 0)
        value_b = degree_b.get(node, 0)
        max_value = max(value_a, value_b)

        if max_value == 0:
            total += 1.0
        else:
            total += 1 - abs(value_a - value_b) / max_value

    return total / len(nodes)


def structural_alignment(graph_a: TopologyGraph, graph_b: TopologyGraph) -> float:
    """Return composite structural alignment score."""
    return (
        hub_alignment(graph_a, graph_b)
        + pattern_alignment(graph_a, graph_b)
        + motif_alignment(graph_a, graph_b)
        + directional_alignment(graph_a, graph_b)
    ) / 4


def _dominant_out_nodes(graph: TopologyGraph) -> set[Node]:
    """Return nodes with the highest weighted out-degree."""
    degrees = weighted_out_degree(graph)

    if not degrees:
        return set()

    max_degree = max(degrees.values())

    if max_degree <= 0:
        return set()

    return {
        node
        for node, degree in degrees.items()
        if degree == max_degree
    }