"""Atlas Nearest Neighbor Engine.

Find the closest structural neighbors from a SimilarityMatrix.
"""

from __future__ import annotations

from dataclasses import asdict
from dataclasses import dataclass
from typing import Any

from atlas.calibration.similarity_matrix import SimilarityMatrix


NEAREST_NEIGHBOR_VERSION = "1.0"


@dataclass(frozen=True)
class NeighborResult:
    """Nearest-neighbor result for one identity."""

    version: str
    query_identity: str
    neighbor_count: int
    neighbors: list[dict[str, Any]]
    summary: dict[str, Any]


def find_nearest_neighbors(
    matrix: SimilarityMatrix,
    query_identity: str,
    *,
    limit: int = 10,
) -> NeighborResult:
    """Find nearest neighbors for one identity."""
    neighbors: list[dict[str, Any]] = []

    for result in matrix.results:
        if result.identity_a == query_identity:
            neighbors.append(
                build_neighbor_record(
                    identity=result.identity_b,
                    similarity=result.similarity,
                    distance=result.distance,
                    metric_count=result.metric_count,
                )
            )

        elif result.identity_b == query_identity:
            neighbors.append(
                build_neighbor_record(
                    identity=result.identity_a,
                    similarity=result.similarity,
                    distance=result.distance,
                    metric_count=result.metric_count,
                )
            )

    neighbors = sorted(
        neighbors,
        key=lambda record: record["similarity"],
        reverse=True,
    )

    limited = neighbors[:limit]

    return NeighborResult(
        version=NEAREST_NEIGHBOR_VERSION,
        query_identity=query_identity,
        neighbor_count=len(limited),
        neighbors=limited,
        summary=build_neighbor_summary(
            query_identity=query_identity,
            neighbors=limited,
        ),
    )


def build_neighbor_record(
    *,
    identity: str,
    similarity: float,
    distance: float,
    metric_count: int,
) -> dict[str, Any]:
    """Build one neighbor record."""
    return {
        "identity": identity,
        "similarity": similarity,
        "distance": distance,
        "metric_count": metric_count,
    }


def build_neighbor_summary(
    *,
    query_identity: str,
    neighbors: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build summary for nearest-neighbor result."""
    if not neighbors:
        return {
            "query_identity": query_identity,
            "neighbor_count": 0,
            "top_neighbor": None,
            "top_similarity": 0.0,
            "mean_similarity": 0.0,
        }

    similarities = [
        neighbor["similarity"]
        for neighbor in neighbors
    ]

    top_neighbor = neighbors[0]

    return {
        "query_identity": query_identity,
        "neighbor_count": len(neighbors),
        "top_neighbor": top_neighbor["identity"],
        "top_similarity": top_neighbor["similarity"],
        "mean_similarity": sum(similarities) / len(similarities),
    }


def find_all_nearest_neighbors(
    matrix: SimilarityMatrix,
    *,
    limit: int = 10,
) -> dict[str, NeighborResult]:
    """Find nearest neighbors for every identity in the matrix."""
    identities = collect_identities(matrix)

    return {
        identity: find_nearest_neighbors(
            matrix,
            identity,
            limit=limit,
        )
        for identity in identities
    }


def collect_identities(
    matrix: SimilarityMatrix,
) -> list[str]:
    """Collect all identities represented in a matrix."""
    identities: set[str] = set()

    for result in matrix.results:
        identities.add(result.identity_a)
        identities.add(result.identity_b)

    return sorted(identities)


def neighbor_result_to_dict(
    result: NeighborResult,
) -> dict[str, Any]:
    """Convert NeighborResult to dictionary."""
    return asdict(result)


def all_neighbors_to_dict(
    results: dict[str, NeighborResult],
) -> dict[str, Any]:
    """Convert all nearest-neighbor results to dictionary."""
    return {
        identity: neighbor_result_to_dict(result)
        for identity, result in results.items()
    }