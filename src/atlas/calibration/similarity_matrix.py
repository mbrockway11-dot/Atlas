"""Atlas Similarity Matrix.

Build pairwise similarity matrices across a population of ProfileMetrics.
"""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.calibration.models import ProfileMetrics
from atlas.calibration.population_statistics import load_population_metrics
from atlas.calibration.similarity_engine import (
    SimilarityResult,
    compare_profile_metrics,
    similarity_result_to_dict,
)


SIMILARITY_MATRIX_VERSION = "1.0"


@dataclass(frozen=True)
class SimilarityMatrix:
    """Pairwise similarity matrix for a population."""

    version: str
    profile_count: int
    pair_count: int
    results: list[SimilarityResult]
    summary: dict[str, Any]


def build_similarity_matrix(
    profiles: list[ProfileMetrics],
    *,
    include_self: bool = False,
) -> SimilarityMatrix:
    """Build all pairwise similarity results for profile metrics."""
    results: list[SimilarityResult] = []

    for index_a, profile_a in enumerate(profiles):
        for index_b, profile_b in enumerate(profiles):
            if not include_self and index_a == index_b:
                continue

            if not include_self and index_b <= index_a:
                continue

            results.append(
                compare_profile_metrics(
                    profile_a,
                    profile_b,
                )
            )

    return SimilarityMatrix(
        version=SIMILARITY_MATRIX_VERSION,
        profile_count=len(profiles),
        pair_count=len(results),
        results=results,
        summary=build_similarity_matrix_summary(results),
    )


def build_similarity_matrix_from_library(
    profile_library: Path,
    *,
    include_self: bool = False,
) -> SimilarityMatrix:
    """Build similarity matrix from a profile library directory."""
    profiles = load_population_metrics(profile_library)

    return build_similarity_matrix(
        profiles,
        include_self=include_self,
    )


def build_similarity_matrix_summary(
    results: list[SimilarityResult],
) -> dict[str, Any]:
    """Build matrix-level summary."""
    if not results:
        return {
            "result_count": 0,
            "mean_similarity": 0.0,
            "max_similarity": 0.0,
            "min_similarity": 0.0,
            "most_similar_pair": None,
            "least_similar_pair": None,
        }

    similarities = [
        result.similarity
        for result in results
    ]

    most_similar = max(
        results,
        key=lambda result: result.similarity,
    )

    least_similar = min(
        results,
        key=lambda result: result.similarity,
    )

    return {
        "result_count": len(results),
        "mean_similarity": sum(similarities) / len(similarities),
        "max_similarity": max(similarities),
        "min_similarity": min(similarities),
        "most_similar_pair": {
            "identity_a": most_similar.identity_a,
            "identity_b": most_similar.identity_b,
            "similarity": most_similar.similarity,
        },
        "least_similar_pair": {
            "identity_a": least_similar.identity_a,
            "identity_b": least_similar.identity_b,
            "similarity": least_similar.similarity,
        },
    }


def similarity_matrix_to_dict(
    matrix: SimilarityMatrix,
) -> dict[str, Any]:
    """Convert similarity matrix to JSON-safe dict."""
    return {
        "version": matrix.version,
        "profile_count": matrix.profile_count,
        "pair_count": matrix.pair_count,
        "summary": matrix.summary,
        "results": [
            similarity_result_to_dict(result)
            for result in matrix.results
        ],
    }


def export_similarity_matrix_json(
    matrix: SimilarityMatrix,
    output_path: Path,
) -> None:
    """Export similarity matrix as JSON."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            similarity_matrix_to_dict(matrix),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def export_similarity_matrix_csv(
    matrix: SimilarityMatrix,
    output_path: Path,
) -> None:
    """Export similarity matrix as edge-list CSV."""
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=[
                "identity_a",
                "identity_b",
                "similarity",
                "distance",
                "metric_count",
            ],
        )

        writer.writeheader()

        for result in matrix.results:
            writer.writerow(
                {
                    "identity_a": result.identity_a,
                    "identity_b": result.identity_b,
                    "similarity": result.similarity,
                    "distance": result.distance,
                    "metric_count": result.metric_count,
                }
            )