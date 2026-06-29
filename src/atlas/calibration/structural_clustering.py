"""Atlas Structural Clustering.

Discover structural families from a PopulationGraph.

This first version uses connected components over thresholded similarity
edges. Later versions can add modularity, spectral clustering, and layout-aware
community detection.
"""

from __future__ import annotations

import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.calibration.population_graph import PopulationGraph


STRUCTURAL_CLUSTERING_VERSION = "1.0"


@dataclass(frozen=True)
class StructuralCluster:
    """One structural population cluster."""

    cluster_id: str
    member_count: int
    members: list[str]
    internal_edge_count: int
    average_internal_similarity: float
    strongest_pair: dict[str, Any] | None


@dataclass(frozen=True)
class StructuralClusteringResult:
    """Structural clustering result for a population graph."""

    version: str
    cluster_count: int
    clustered_identity_count: int
    singleton_count: int
    clusters: list[StructuralCluster]
    summary: dict[str, Any]


def build_structural_clusters(
    graph: PopulationGraph,
) -> StructuralClusteringResult:
    """Build structural clusters from population graph components."""

    adjacency = build_adjacency(graph)
    components = connected_components(adjacency)

    clusters: list[StructuralCluster] = []

    for index, component in enumerate(components, start=1):
        cluster = build_cluster(
            graph=graph,
            members=component,
            cluster_id=f"cluster_{index:03d}",
        )

        clusters.append(cluster)

    clusters = sorted(
        clusters,
        key=lambda cluster: (
            -cluster.member_count,
            cluster.cluster_id,
        ),
    )

    singleton_count = len(
        [
            cluster
            for cluster in clusters
            if cluster.member_count == 1
        ]
    )

    return StructuralClusteringResult(
        version=STRUCTURAL_CLUSTERING_VERSION,
        cluster_count=len(clusters),
        clustered_identity_count=sum(
            cluster.member_count
            for cluster in clusters
        ),
        singleton_count=singleton_count,
        clusters=clusters,
        summary=build_clustering_summary(clusters),
    )


def build_adjacency(
    graph: PopulationGraph,
) -> dict[str, set[str]]:
    """Build undirected adjacency from a population graph."""

    adjacency: dict[str, set[str]] = {
        identity: set()
        for identity in graph.nodes
    }

    for edge in graph.edges.values():
        source = edge["source"]
        target = edge["target"]

        adjacency.setdefault(source, set()).add(target)
        adjacency.setdefault(target, set()).add(source)

    return adjacency


def connected_components(
    adjacency: dict[str, set[str]],
) -> list[list[str]]:
    """Compute connected components."""

    visited: set[str] = set()
    components: list[list[str]] = []

    for node in sorted(adjacency):
        if node in visited:
            continue

        stack = [node]
        component: list[str] = []

        while stack:
            current = stack.pop()

            if current in visited:
                continue

            visited.add(current)
            component.append(current)

            for neighbor in sorted(adjacency.get(current, set())):
                if neighbor not in visited:
                    stack.append(neighbor)

        components.append(sorted(component))

    return components


def build_cluster(
    *,
    graph: PopulationGraph,
    members: list[str],
    cluster_id: str,
) -> StructuralCluster:
    """Build one structural cluster."""

    member_set = set(members)

    internal_edges = [
        edge
        for edge in graph.edges.values()
        if edge["source"] in member_set
        and edge["target"] in member_set
    ]

    similarities = [
        float(edge.get("similarity", 0.0))
        for edge in internal_edges
    ]

    strongest_edge = (
        max(
            internal_edges,
            key=lambda edge: edge.get("similarity", 0.0),
        )
        if internal_edges
        else None
    )

    strongest_pair = (
        {
            "identity_a": strongest_edge["source"],
            "identity_b": strongest_edge["target"],
            "similarity": strongest_edge["similarity"],
        }
        if strongest_edge
        else None
    )

    average_internal_similarity = (
        sum(similarities) / len(similarities)
        if similarities
        else 0.0
    )

    return StructuralCluster(
        cluster_id=cluster_id,
        member_count=len(members),
        members=sorted(members),
        internal_edge_count=len(internal_edges),
        average_internal_similarity=average_internal_similarity,
        strongest_pair=strongest_pair,
    )


def build_clustering_summary(
    clusters: list[StructuralCluster],
) -> dict[str, Any]:
    """Build clustering summary."""

    if not clusters:
        return {
            "cluster_count": 0,
            "largest_cluster_id": None,
            "largest_cluster_size": 0,
            "singleton_count": 0,
            "mean_cluster_size": 0.0,
        }

    largest = max(
        clusters,
        key=lambda cluster: cluster.member_count,
    )

    singleton_count = len(
        [
            cluster
            for cluster in clusters
            if cluster.member_count == 1
        ]
    )

    return {
        "cluster_count": len(clusters),
        "largest_cluster_id": largest.cluster_id,
        "largest_cluster_size": largest.member_count,
        "singleton_count": singleton_count,
        "mean_cluster_size": (
            sum(cluster.member_count for cluster in clusters)
            / len(clusters)
        ),
    }


def structural_cluster_to_dict(
    cluster: StructuralCluster,
) -> dict[str, Any]:
    """Convert StructuralCluster to dictionary."""

    return asdict(cluster)


def structural_clustering_result_to_dict(
    result: StructuralClusteringResult,
) -> dict[str, Any]:
    """Convert StructuralClusteringResult to dictionary."""

    return {
        "version": result.version,
        "cluster_count": result.cluster_count,
        "clustered_identity_count": result.clustered_identity_count,
        "singleton_count": result.singleton_count,
        "summary": result.summary,
        "clusters": [
            structural_cluster_to_dict(cluster)
            for cluster in result.clusters
        ],
    }


def export_structural_clusters_json(
    result: StructuralClusteringResult,
    output_path: Path,
) -> None:
    """Export structural clustering result as JSON."""

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            structural_clustering_result_to_dict(result),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )