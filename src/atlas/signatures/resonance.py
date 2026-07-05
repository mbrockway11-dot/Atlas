"""Deterministic motif detection for topology graphs."""

from atlas.features.metrics import edge_density, graph_symmetry, out_degree
from atlas.topology.graph import TopologyGraph


def dominant_pattern(graph: TopologyGraph) -> str:
    """Classify the dominant structural pattern."""
    if graph.node_count == 0:
        return "empty"

    if graph.edge_count == 0:
        return "isolated"

    symmetry = graph_symmetry(graph)
    density = edge_density(graph)
    out_degrees = out_degree(graph)

    max_out = max(out_degrees.values()) if out_degrees else 0

    if symmetry >= 0.75:
        return "reciprocal"

    if max_out >= 3:
        return "radiating"

    if density >= 0.5:
        return "dense"

    if graph.edge_count >= graph.node_count:
        return "looping"

    return "linear"


def branching_level(graph: TopologyGraph) -> str:
    """Classify branching intensity."""
    if graph.node_count == 0:
        return "none"

    degrees = out_degree(graph)
    max_out = max(degrees.values()) if degrees else 0

    if max_out >= 4:
        return "high"

    if max_out >= 2:
        return "medium"

    if max_out == 1:
        return "low"

    return "none"


def reciprocity_level(graph: TopologyGraph) -> str:
    """Classify reciprocal edge strength."""
    symmetry = graph_symmetry(graph)

    if symmetry >= 0.75:
        return "high"

    if symmetry >= 0.35:
        return "medium"

    if symmetry > 0:
        return "low"

    return "none"


def compression_level(graph: TopologyGraph) -> str:
    """Classify structural compression from edge density."""
    density = edge_density(graph)

    if density >= 0.5:
        return "high"

    if density >= 0.2:
        return "medium"

    if density > 0:
        return "low"

    return "none"
