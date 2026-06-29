"""JSON export utilities for Atlas objects."""

import json
from pathlib import Path
from typing import Any

from atlas.features.scoring import TopologyScores
from atlas.resonance.resonance import ResonanceResult
from atlas.signatures.topology_signature import TopologySignature
from atlas.topology.differential import GraphDifferential
from atlas.topology.graph import Edge, Node, TopologyGraph


def graph_to_dict(graph: TopologyGraph) -> dict[str, Any]:
    """Convert a TopologyGraph into a JSON-safe dictionary."""
    return {
        "nodes": [_node_to_list(node) for node in graph.nodes],
        "edges": [_edge_to_list(edge) for edge in graph.edges],
        "node_weights": [
            {
                "node": _node_to_list(node),
                "weight": weight,
            }
            for node, weight in graph.node_weights.items()
        ],
        "edge_weights": [
            {
                "edge": _edge_to_list(edge),
                "weight": weight,
            }
            for edge, weight in graph.edge_weights.items()
        ],
        "summary": {
            "node_count": graph.node_count,
            "edge_count": graph.edge_count,
            "total_node_weight": graph.total_node_weight,
            "total_edge_weight": graph.total_edge_weight,
        },
    }


def scores_to_dict(scores: TopologyScores) -> dict[str, float]:
    """Convert TopologyScores into a JSON-safe dictionary."""
    return {
        "driver": scores.driver,
        "amplifier": scores.amplifier,
        "regulator": scores.regulator,
    }


def signature_to_dict(signature: TopologySignature) -> dict[str, Any]:
    """Convert a TopologySignature into a JSON-safe dictionary."""
    return {
        "scores": {
            "driver": signature.driver,
            "amplifier": signature.amplifier,
            "regulator": signature.regulator,
        },
        "metrics": {
            "node_count": signature.node_count,
            "edge_count": signature.edge_count,
            "edge_density": signature.edge_density,
            "symmetry": signature.symmetry,
            "component_count": signature.component_count,
            "entropy": signature.entropy,
        },
        "patterns": {
            "dominant_pattern": signature.dominant_pattern,
            "branching_level": signature.branching_level,
            "reciprocity_level": signature.reciprocity_level,
            "compression_level": signature.compression_level,
        },
        "motifs": {
            "dominant_motif": signature.dominant_motif,
            "motif_density": signature.motif_density,
            "chains": signature.chains,
            "hubs": signature.hubs,
            "loops": signature.loops,
            "bridges": signature.bridges,
            "dead_ends": signature.dead_ends,
            "reciprocal_pairs": signature.reciprocal_pairs,
            "isolated_nodes": signature.isolated_nodes,
        },
    }


def resonance_to_dict(resonance: ResonanceResult) -> dict[str, float]:
    """Convert ResonanceResult into a JSON-safe dictionary."""
    return {
        "overall": resonance.overall,
        "node_similarity": resonance.node_similarity,
        "edge_similarity": resonance.edge_similarity,
        "node_weight_similarity": resonance.node_weight_similarity,
        "edge_weight_similarity": resonance.edge_weight_similarity,
        "vector_similarity": resonance.vector_similarity,
        "alignment_similarity": resonance.alignment_similarity,
    }


def differential_to_dict(diff: GraphDifferential) -> dict[str, Any]:
    """Convert a GraphDifferential into a JSON-safe dictionary."""
    return {
        "shared_nodes": [_node_to_list(node) for node in diff.shared_nodes],
        "shared_edges": [_edge_to_list(edge) for edge in diff.shared_edges],
        "unique_nodes_a": [_node_to_list(node) for node in diff.unique_nodes_a],
        "unique_nodes_b": [_node_to_list(node) for node in diff.unique_nodes_b],
        "unique_edges_a": [_edge_to_list(edge) for edge in diff.unique_edges_a],
        "unique_edges_b": [_edge_to_list(edge) for edge in diff.unique_edges_b],
        "node_weight_delta": [
            {
                "node": _node_to_list(node),
                "delta": delta,
            }
            for node, delta in diff.node_weight_delta.items()
        ],
        "edge_weight_delta": [
            {
                "edge": _edge_to_list(edge),
                "delta": delta,
            }
            for edge, delta in diff.edge_weight_delta.items()
        ],
        "overlap": {
            "node_overlap_ratio": diff.node_overlap_ratio,
            "edge_overlap_ratio": diff.edge_overlap_ratio,
        },
    }


def write_json(data: dict[str, Any], output_path: str | Path) -> Path:
    """Write a dictionary to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)

    return path


def export_graph_json(graph: TopologyGraph, output_path: str | Path) -> Path:
    """Export a TopologyGraph to JSON."""
    return write_json(graph_to_dict(graph), output_path)


def export_scores_json(scores: TopologyScores, output_path: str | Path) -> Path:
    """Export TopologyScores to JSON."""
    return write_json(scores_to_dict(scores), output_path)


def export_signature_json(
    signature: TopologySignature,
    output_path: str | Path,
) -> Path:
    """Export a TopologySignature to JSON."""
    return write_json(signature_to_dict(signature), output_path)


def export_resonance_json(
    resonance: ResonanceResult,
    output_path: str | Path,
) -> Path:
    """Export a ResonanceResult to JSON."""
    return write_json(resonance_to_dict(resonance), output_path)


def export_differential_json(
    diff: GraphDifferential,
    output_path: str | Path,
) -> Path:
    """Export a GraphDifferential to JSON."""
    return write_json(differential_to_dict(diff), output_path)


def export_graph_with_scores_json(
    graph: TopologyGraph,
    scores: TopologyScores,
    output_path: str | Path,
) -> Path:
    """Export graph and scores together."""
    data = {
        "graph": graph_to_dict(graph),
        "scores": scores_to_dict(scores),
    }

    return write_json(data, output_path)


def export_graph_with_signature_json(
    graph: TopologyGraph,
    signature: TopologySignature,
    output_path: str | Path,
) -> Path:
    """Export graph and signature together."""
    data = {
        "graph": graph_to_dict(graph),
        "signature": signature_to_dict(signature),
    }

    return write_json(data, output_path)


def export_comparison_json(
    graph_a: TopologyGraph,
    graph_b: TopologyGraph,
    diff: GraphDifferential,
    resonance: ResonanceResult,
    output_path: str | Path,
) -> Path:
    """Export two graphs with their differential and resonance."""
    data = {
        "graph_a": graph_to_dict(graph_a),
        "graph_b": graph_to_dict(graph_b),
        "differential": differential_to_dict(diff),
        "resonance": resonance_to_dict(resonance),
    }

    return write_json(data, output_path)


def _node_to_list(node: Node) -> list[int]:
    """Convert a node tuple to a JSON-safe list."""
    return [node[0], node[1]]


def _edge_to_list(edge: Edge) -> list[list[int]]:
    """Convert an edge tuple to a JSON-safe nested list."""
    return [
        _node_to_list(edge[0]),
        _node_to_list(edge[1]),
    ]