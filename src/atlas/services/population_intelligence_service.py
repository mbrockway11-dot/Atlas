"""Population Intelligence service layer.

Dashboard-safe wrapper for similarity, nearest-neighbor, graph, and clustering
operations.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.calibration.nearest_neighbor import (
    find_nearest_neighbors,
    neighbor_result_to_dict,
)
from atlas.calibration.population_graph import (
    build_population_graph,
    population_graph_to_dict,
)
from atlas.calibration.similarity_matrix import (
    build_similarity_matrix_from_library,
    similarity_matrix_to_dict,
)
from atlas.calibration.structural_clustering import (
    build_structural_clusters,
    structural_clustering_result_to_dict,
)


DEFAULT_PROFILE_DIR = Path("output/library")


def profile_library_exists(profile_dir: str | Path = DEFAULT_PROFILE_DIR) -> bool:
    """Return whether the profile library directory exists."""
    return Path(profile_dir).exists()


def build_population_intelligence_payload(
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
    *,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Build full population intelligence payload.

    This keeps calibration/backend imports out of the dashboard.
    """
    root = Path(profile_dir)

    if not root.exists():
        return {
            "success": False,
            "profile_dir": str(root),
            "errors": [f"Profile directory not found: {root}"],
            "warnings": [],
            "data": None,
            "metrics": {},
        }

    matrix = build_similarity_matrix_from_library(root)
    graph = build_population_graph(matrix, threshold=threshold)
    clusters = build_structural_clusters(graph)

    return {
        "success": True,
        "profile_dir": str(root),
        "threshold": threshold,
        "errors": [],
        "warnings": [],
        "data": {
            "matrix": matrix,
            "graph": graph,
            "clusters": clusters,
            "matrix_dict": similarity_matrix_to_dict(matrix),
            "graph_dict": population_graph_to_dict(graph),
            "clusters_dict": structural_clustering_result_to_dict(clusters),
        },
        "metrics": {
            "profiles": matrix.profile_count,
            "similarity_pairs": matrix.pair_count,
            "graph_edges": graph.edge_count,
            "clusters": clusters.cluster_count,
            "mean_similarity": matrix.summary.get("mean_similarity", 0.0),
            "graph_density": graph.summary.get("density", 0.0),
            "largest_cluster": clusters.summary.get("largest_cluster_size", 0),
            "singletons": clusters.singleton_count,
        },
    }


def collect_population_identities(matrix: Any) -> list[str]:
    """Collect identities represented in a similarity matrix."""
    identities: set[str] = set()

    for result in getattr(matrix, "results", []):
        identities.add(result.identity_a)
        identities.add(result.identity_b)

    return sorted(identities)


def build_cluster_rows(clusters: Any) -> list[dict[str, Any]]:
    """Convert structural clusters into dashboard table rows."""
    rows: list[dict[str, Any]] = []

    for cluster in getattr(clusters, "clusters", []):
        rows.append(
            {
                "cluster_id": cluster.cluster_id,
                "member_count": cluster.member_count,
                "internal_edge_count": cluster.internal_edge_count,
                "average_internal_similarity": cluster.average_internal_similarity,
                "members": ", ".join(cluster.members),
                "strongest_pair": format_strongest_pair(cluster.strongest_pair),
            }
        )

    return rows


def build_neighbor_payload(
    matrix: Any,
    identity: str,
    *,
    limit: int = 10,
) -> dict[str, Any]:
    """Build nearest-neighbor report for one identity."""
    neighbors = find_nearest_neighbors(matrix, identity, limit=limit)

    return {
        "success": True,
        "identity": identity,
        "limit": limit,
        "neighbors": neighbors.neighbors,
        "report": neighbor_result_to_dict(neighbors),
    }


def json_export(data: Any) -> str:
    """Serialize dashboard export payloads consistently."""
    return json.dumps(data, indent=2, sort_keys=True)


def slugify(value: str) -> str:
    """Build safe filename slug."""
    return (
        value.casefold()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )


def format_strongest_pair(pair: Any) -> str:
    """Format strongest pair display."""
    if not pair:
        return ""

    return (
        f"{pair['identity_a']} ↔ {pair['identity_b']} "
        f"({round(pair['similarity'], 4)})"
    )