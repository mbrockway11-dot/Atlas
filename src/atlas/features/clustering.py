"""Corpus clustering utilities."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

import pandas as pd

from atlas.corpus.similarity import numeric_similarity_columns, standardize_features


@dataclass(frozen=True)
class ClusterResult:
    """Corpus clustering result."""

    cluster_count: int
    feature_count: int
    assignments: list[dict[str, Any]]
    clusters: list[dict[str, Any]]
    outliers: list[dict[str, Any]]


def cluster_corpus(
    dataframe: pd.DataFrame,
    cluster_count: int = 4,
    min_std: float = 0.005,
    max_iterations: int = 100,
) -> ClusterResult:
    """Cluster corpus profiles using deterministic k-means."""
    if "name" not in dataframe.columns:
        raise ValueError("Corpus dataframe must contain a 'name' column.")

    dataframe = dataframe.copy()
    dataframe["name"] = dataframe["name"].apply(clean_profile_name)

    feature_columns = numeric_similarity_columns(
        dataframe=dataframe,
        min_std=min_std,
    )

    if not feature_columns:
        raise ValueError("No usable numeric feature columns found.")

    matrix = build_feature_matrix(dataframe, feature_columns)
    k = min(cluster_count, len(matrix))
    centroids = initialize_centroids(matrix, k)

    assignments: list[int] = []

    for _ in range(max_iterations):
        new_assignments = assign_clusters(matrix, centroids)

        if new_assignments == assignments:
            break

        assignments = new_assignments
        centroids = recompute_centroids(
            matrix=matrix,
            assignments=assignments,
            cluster_count=k,
            previous_centroids=centroids,
        )

    assignment_rows = build_assignment_rows(
        dataframe=dataframe,
        matrix=matrix,
        assignments=assignments,
        centroids=centroids,
    )

    cluster_rows = build_cluster_rows(
        dataframe=dataframe,
        matrix=matrix,
        assignments=assignments,
        centroids=centroids,
        feature_columns=feature_columns,
        cluster_count=k,
    )

    outliers = sorted(
        assignment_rows,
        key=lambda row: row["distance_to_centroid"],
        reverse=True,
    )[: min(10, len(assignment_rows))]

    return ClusterResult(
        cluster_count=k,
        feature_count=len(feature_columns),
        assignments=assignment_rows,
        clusters=cluster_rows,
        outliers=outliers,
    )


def build_feature_matrix(
    dataframe: pd.DataFrame,
    feature_columns: list[str],
) -> list[list[float]]:
    """Build standardized numeric feature matrix."""
    standardized = standardize_features(
        dataframe=dataframe,
        columns=feature_columns,
    )

    return [
        [float(row[column]) for column in feature_columns]
        for _, row in standardized.iterrows()
    ]


def initialize_centroids(
    matrix: list[list[float]],
    cluster_count: int,
) -> list[list[float]]:
    """Initialize centroids deterministically by evenly spaced rows."""
    if not matrix:
        return []

    if cluster_count <= 1:
        return [matrix[0]]

    last_index = len(matrix) - 1

    indices = [
        round(index * last_index / (cluster_count - 1))
        for index in range(cluster_count)
    ]

    return [list(matrix[index]) for index in indices]


def assign_clusters(
    matrix: list[list[float]],
    centroids: list[list[float]],
) -> list[int]:
    """Assign each row to nearest centroid."""
    assignments = []

    for values in matrix:
        distances = [
            euclidean_distance(values, centroid)
            for centroid in centroids
        ]

        assignments.append(
            min(range(len(distances)), key=lambda index: distances[index])
        )

    return assignments


def recompute_centroids(
    matrix: list[list[float]],
    assignments: list[int],
    cluster_count: int,
    previous_centroids: list[list[float]],
) -> list[list[float]]:
    """Recompute centroids from assignments."""
    centroids = []

    for cluster_id in range(cluster_count):
        members = [
            values
            for values, assignment in zip(matrix, assignments)
            if assignment == cluster_id
        ]

        if not members:
            centroids.append(previous_centroids[cluster_id])
        else:
            centroids.append(mean_vector(members))

    return centroids


def build_assignment_rows(
    dataframe: pd.DataFrame,
    matrix: list[list[float]],
    assignments: list[int],
    centroids: list[list[float]],
) -> list[dict[str, Any]]:
    """Build per-profile assignment rows."""
    rows = []

    for index, values in enumerate(matrix):
        cluster_id = assignments[index]
        distance = euclidean_distance(values, centroids[cluster_id])

        rows.append(
            {
                "name": clean_profile_name(dataframe.iloc[index]["name"]),
                "cluster_id": cluster_id,
                "distance_to_centroid": distance,
            }
        )

    return rows


def build_cluster_rows(
    dataframe: pd.DataFrame,
    matrix: list[list[float]],
    assignments: list[int],
    centroids: list[list[float]],
    feature_columns: list[str],
    cluster_count: int,
) -> list[dict[str, Any]]:
    """Build cluster summaries."""
    rows = []

    for cluster_id in range(cluster_count):
        member_indices = [
            index
            for index, assignment in enumerate(assignments)
            if assignment == cluster_id
        ]

        members = [
            clean_profile_name(dataframe.iloc[index]["name"])
            for index in member_indices
        ]

        distances = [
            euclidean_distance(matrix[index], centroids[cluster_id])
            for index in member_indices
        ]

        representative = None

        if member_indices:
            best_local_index = min(
                range(len(member_indices)),
                key=lambda index: distances[index],
            )
            representative = clean_profile_name(
                dataframe.iloc[member_indices[best_local_index]]["name"]
            )

        dominant_features = dominant_cluster_features(
            centroid=centroids[cluster_id],
            feature_columns=feature_columns,
            top_n=10,
        )

        rows.append(
            {
                "cluster_id": cluster_id,
                "size": len(members),
                "members": members,
                "representative": representative,
                "mean_distance_to_centroid": (
                    sum(distances) / len(distances)
                    if distances
                    else 0.0
                ),
                "dominant_features": dominant_features,
                "centroid": {
                    feature: centroids[cluster_id][index]
                    for index, feature in enumerate(feature_columns)
                },
            }
        )

    return rows


def dominant_cluster_features(
    centroid: list[float],
    feature_columns: list[str],
    top_n: int = 10,
) -> list[dict[str, Any]]:
    """Return strongest centroid features by absolute standardized magnitude."""
    rows = [
        {
            "feature": feature,
            "centroid_value": float(value),
            "absolute_centroid_value": abs(float(value)),
        }
        for feature, value in zip(feature_columns, centroid)
    ]

    return sorted(
        rows,
        key=lambda row: row["absolute_centroid_value"],
        reverse=True,
    )[:top_n]


def cluster_result_to_dict(result: ClusterResult) -> dict[str, Any]:
    """Convert cluster result to dictionary."""
    return {
        "cluster_count": result.cluster_count,
        "feature_count": result.feature_count,
        "assignments": result.assignments,
        "clusters": result.clusters,
        "outliers": result.outliers,
    }


def euclidean_distance(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Euclidean distance."""
    if not values_a:
        return 0.0

    return sqrt(
        sum(
            (float(a) - float(b)) ** 2
            for a, b in zip(values_a, values_b)
        )
    )


def mean_vector(vectors: list[list[float]]) -> list[float]:
    """Calculate vector mean."""
    if not vectors:
        return []

    width = len(vectors[0])

    return [
        sum(vector[index] for vector in vectors) / len(vectors)
        for index in range(width)
    ]


def clean_profile_name(value: Any) -> str:
    """Normalize profile display names before exporting cluster JSON."""
    if value is None:
        return "Unknown"

    text = str(value).strip()

    replacements = {
        "AlbertEinstein": "Albert Einstein",
        "LeonhardEuler": "Leonhard Euler",
        "James ClerkMaxwell": "James Clerk Maxwell",
        "Friedrich WilhelmNietzsche": "Friedrich Wilhelm Nietzsche",
        "Nelson RolihlahlaMandela": "Nelson Rolihlahla Mandela",
        "RenéDescartes": "René Descartes",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    return " ".join(text.split())