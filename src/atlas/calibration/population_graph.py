"""Atlas Population Graph.

Convert pairwise similarity matrices into population graphs.

Nodes represent identities.
Edges represent similarity relationships above a threshold.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.calibration.similarity_matrix import SimilarityMatrix


POPULATION_GRAPH_VERSION = "1.0"


@dataclass(frozen=True)
class PopulationGraph:
    """Graph representation of population similarity structure."""

    version: str
    node_count: int
    edge_count: int
    threshold: float
    nodes: dict[str, dict[str, Any]]
    edges: dict[str, dict[str, Any]]
    summary: dict[str, Any]


def build_population_graph(
    matrix: SimilarityMatrix,
    *,
    threshold: float = 0.85,
) -> PopulationGraph:
    """Build a population graph from a similarity matrix."""
    nodes = collect_population_nodes(matrix)
    edges = collect_population_edges(
        matrix,
        threshold=threshold,
    )

    return PopulationGraph(
        version=POPULATION_GRAPH_VERSION,
        node_count=len(nodes),
        edge_count=len(edges),
        threshold=threshold,
        nodes=nodes,
        edges=edges,
        summary=build_population_graph_summary(
            nodes=nodes,
            edges=edges,
            threshold=threshold,
        ),
    )


def collect_population_nodes(
    matrix: SimilarityMatrix,
) -> dict[str, dict[str, Any]]:
    """Collect population graph nodes."""
    nodes: dict[str, dict[str, Any]] = {}

    for result in matrix.results:
        if result.identity_a not in nodes:
            nodes[result.identity_a] = build_node_record(
                identity=result.identity_a,
            )

        if result.identity_b not in nodes:
            nodes[result.identity_b] = build_node_record(
                identity=result.identity_b,
            )

    return nodes


def build_node_record(
    *,
    identity: str,
) -> dict[str, Any]:
    """Build one node record."""
    return {
        "id": identity,
        "label": identity,
    }


def collect_population_edges(
    matrix: SimilarityMatrix,
    *,
    threshold: float,
) -> dict[str, dict[str, Any]]:
    """Collect population graph edges above threshold."""
    edges: dict[str, dict[str, Any]] = {}

    for result in matrix.results:
        if result.identity_a == result.identity_b:
            continue

        if result.similarity < threshold:
            continue

        edge_id = build_edge_id(
            result.identity_a,
            result.identity_b,
        )

        edges[edge_id] = build_edge_record(
            edge_id=edge_id,
            source=result.identity_a,
            target=result.identity_b,
            similarity=result.similarity,
            distance=result.distance,
            metric_count=result.metric_count,
        )

    return edges


def build_edge_record(
    *,
    edge_id: str,
    source: str,
    target: str,
    similarity: float,
    distance: float,
    metric_count: int,
) -> dict[str, Any]:
    """Build one edge record."""
    return {
        "id": edge_id,
        "source": source,
        "target": target,
        "weight": similarity,
        "similarity": similarity,
        "distance": distance,
        "metric_count": metric_count,
    }


def build_edge_id(
    identity_a: str,
    identity_b: str,
) -> str:
    """Build stable undirected edge id."""
    left, right = sorted(
        [
            identity_a,
            identity_b,
        ]
    )

    return f"{left}::{right}"


def build_population_graph_summary(
    *,
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
    threshold: float,
) -> dict[str, Any]:
    """Build graph summary."""
    degrees = compute_degrees(
        nodes=nodes,
        edges=edges,
    )

    if not nodes:
        return {
            "threshold": threshold,
            "node_count": 0,
            "edge_count": 0,
            "density": 0.0,
            "average_degree": 0.0,
            "max_degree": 0,
            "most_connected_identity": None,
        }

    average_degree = (
        sum(degrees.values()) / len(degrees)
        if degrees
        else 0.0
    )

    most_connected_identity = (
        max(
            degrees,
            key=lambda identity: degrees[identity],
        )
        if degrees
        else None
    )

    return {
        "threshold": threshold,
        "node_count": len(nodes),
        "edge_count": len(edges),
        "density": graph_density(
            node_count=len(nodes),
            edge_count=len(edges),
        ),
        "average_degree": average_degree,
        "max_degree": max(degrees.values()) if degrees else 0,
        "most_connected_identity": most_connected_identity,
    }


def compute_degrees(
    *,
    nodes: dict[str, dict[str, Any]],
    edges: dict[str, dict[str, Any]],
) -> dict[str, int]:
    """Compute graph degrees."""
    degrees = {
        identity: 0
        for identity in nodes
    }

    for edge in edges.values():
        source = edge["source"]
        target = edge["target"]

        if source in degrees:
            degrees[source] += 1

        if target in degrees:
            degrees[target] += 1

    return degrees


def graph_density(
    *,
    node_count: int,
    edge_count: int,
) -> float:
    """Compute undirected graph density."""
    if node_count < 2:
        return 0.0

    possible_edges = node_count * (node_count - 1) / 2

    if possible_edges <= 0:
        return 0.0

    return edge_count / possible_edges


def population_graph_to_dict(
    graph: PopulationGraph,
) -> dict[str, Any]:
    """Convert PopulationGraph to dictionary."""
    return asdict(graph)


def export_population_graph_json(
    graph: PopulationGraph,
    output_path: Path,
) -> None:
    """Export population graph as JSON."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            population_graph_to_dict(graph),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )