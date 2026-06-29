"""Statistical intelligence tools for Atlas profile populations.

This module builds on the Population Validation Lab. It does not add new
symbolic features. Instead, it measures whether existing profile-level features
show separable, low-dimensional, cluster-like structure.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd

from atlas.research.validation import normalize_profile_features


def _feature_columns(profile_features: pd.DataFrame) -> list[str]:
    return [column for column in profile_features.columns if column != "name"]


def _numeric_matrix(profile_features: pd.DataFrame) -> tuple[list[str], list[str], np.ndarray]:
    if profile_features.empty or "name" not in profile_features.columns:
        return [], [], np.empty((0, 0), dtype=float)

    normalized = normalize_profile_features(profile_features)
    columns = _feature_columns(normalized)
    names = normalized["name"].astype(str).tolist()

    if not columns:
        return names, [], np.empty((len(names), 0), dtype=float)

    matrix = normalized[columns].to_numpy(dtype=float)
    matrix = np.nan_to_num(matrix, nan=0.0, posinf=0.0, neginf=0.0)
    return names, columns, matrix


def principal_components(
    profile_features: pd.DataFrame,
    n_components: int = 3,
) -> dict[str, Any]:
    """Compute deterministic PCA-style components using numpy SVD."""
    names, columns, matrix = _numeric_matrix(profile_features)

    if matrix.size == 0 or len(names) < 2 or not columns:
        return {
            "available": False,
            "reason": "At least two profiles and one numeric feature are required.",
            "coordinates": [],
            "explained_variance_ratio": [],
            "top_loadings": {},
        }

    max_components = max(1, min(int(n_components), matrix.shape[0] - 1, matrix.shape[1]))
    centered = matrix - matrix.mean(axis=0)

    try:
        _, singular_values, vh = np.linalg.svd(centered, full_matrices=False)
    except np.linalg.LinAlgError:
        return {
            "available": False,
            "reason": "SVD failed for the supplied feature matrix.",
            "coordinates": [],
            "explained_variance_ratio": [],
            "top_loadings": {},
        }

    components = vh[:max_components]
    coordinates = centered @ components.T

    eigenvalues = (singular_values ** 2) / max(matrix.shape[0] - 1, 1)
    total = float(eigenvalues.sum())
    explained = [float(value / total) if total else 0.0 for value in eigenvalues[:max_components]]

    coordinate_rows = []
    for row_index, name in enumerate(names):
        row = {"name": name}
        for component_index in range(max_components):
            row[f"pc{component_index + 1}"] = float(coordinates[row_index, component_index])
        coordinate_rows.append(row)

    top_loadings: dict[str, list[dict[str, Any]]] = {}
    for component_index in range(max_components):
        loading_rows = []
        for feature, value in zip(columns, components[component_index], strict=False):
            loading_rows.append(
                {
                    "feature": feature,
                    "loading": float(value),
                    "absolute_loading": float(abs(value)),
                }
            )
        loading_rows.sort(key=lambda item: (-item["absolute_loading"], item["feature"]))
        top_loadings[f"pc{component_index + 1}"] = loading_rows[:20]

    return {
        "available": True,
        "reason": None,
        "coordinates": coordinate_rows,
        "explained_variance_ratio": explained,
        "top_loadings": top_loadings,
    }


def kmeans_clusters(
    profile_features: pd.DataFrame,
    k: int = 5,
    iterations: int = 100,
) -> pd.DataFrame:
    """Assign deterministic k-means clusters with farthest-point initialization."""
    names, _, matrix = _numeric_matrix(profile_features)

    if matrix.size == 0 or len(names) == 0:
        return pd.DataFrame(columns=["name", "cluster", "distance_to_centroid"])

    k = max(1, min(int(k), len(names)))

    centroid_indices = [0]
    while len(centroid_indices) < k:
        existing = matrix[centroid_indices]
        distances = np.min(
            np.linalg.norm(matrix[:, None, :] - existing[None, :, :], axis=2),
            axis=1,
        )
        for used in centroid_indices:
            distances[used] = -1.0
        centroid_indices.append(int(np.argmax(distances)))

    centroids = matrix[centroid_indices].copy()
    labels = np.zeros(len(names), dtype=int)

    for _ in range(max(1, int(iterations))):
        distances = np.linalg.norm(matrix[:, None, :] - centroids[None, :, :], axis=2)
        next_labels = np.argmin(distances, axis=1)

        if np.array_equal(next_labels, labels):
            labels = next_labels
            break

        labels = next_labels
        for cluster_id in range(k):
            members = matrix[labels == cluster_id]
            if len(members):
                centroids[cluster_id] = members.mean(axis=0)

    final_distances = np.linalg.norm(matrix - centroids[labels], axis=1)

    return pd.DataFrame(
        {
            "name": names,
            "cluster": labels.astype(int),
            "distance_to_centroid": final_distances.astype(float),
        }
    ).sort_values(by=["cluster", "distance_to_centroid", "name"]).reset_index(drop=True)


def cluster_summary(assignments: pd.DataFrame) -> pd.DataFrame:
    """Summarize deterministic cluster assignments."""
    if assignments.empty:
        return pd.DataFrame(columns=["cluster", "profile_count", "mean_distance_to_centroid"])

    return (
        assignments.groupby("cluster", as_index=False)
        .agg(
            profile_count=("name", "count"),
            mean_distance_to_centroid=("distance_to_centroid", "mean"),
        )
        .sort_values(by=["cluster"])
        .reset_index(drop=True)
    )


def silhouette_scores(
    profile_features: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-profile silhouette scores from cluster assignments."""
    names, _, matrix = _numeric_matrix(profile_features)

    if matrix.size == 0 or assignments.empty:
        return pd.DataFrame(columns=["name", "cluster", "silhouette"])

    label_map = dict(zip(assignments["name"], assignments["cluster"], strict=False))
    labels = np.array([label_map.get(name, -1) for name in names], dtype=int)
    unique_labels = sorted(label for label in set(labels.tolist()) if label >= 0)

    if len(unique_labels) < 2:
        return pd.DataFrame(
            {"name": names, "cluster": labels, "silhouette": [0.0 for _ in names]}
        )

    distances = np.linalg.norm(matrix[:, None, :] - matrix[None, :, :], axis=2)
    rows = []

    for index, name in enumerate(names):
        own_label = labels[index]
        if own_label < 0:
            silhouette = 0.0
        else:
            own_indices = np.where(labels == own_label)[0]
            own_indices = own_indices[own_indices != index]
            a_value = float(distances[index, own_indices].mean()) if len(own_indices) else 0.0

            b_candidates = []
            for other_label in unique_labels:
                if other_label == own_label:
                    continue
                other_indices = np.where(labels == other_label)[0]
                if len(other_indices):
                    b_candidates.append(float(distances[index, other_indices].mean()))

            b_value = min(b_candidates) if b_candidates else 0.0
            denominator = max(a_value, b_value)
            silhouette = float((b_value - a_value) / denominator) if denominator else 0.0

        rows.append({"name": name, "cluster": int(own_label), "silhouette": silhouette})

    return pd.DataFrame(rows).sort_values(
        by=["silhouette", "name"],
        ascending=[True, True],
    ).reset_index(drop=True)


def cohort_separation(
    profile_features: pd.DataFrame,
    cohort_index: pd.DataFrame | None,
) -> dict[str, Any]:
    """Measure whether provided cohorts are internally tighter than externally."""
    if cohort_index is None or cohort_index.empty:
        return {
            "available": False,
            "reason": "No cohort index supplied.",
            "cohorts": [],
            "overall_internal_distance": None,
            "overall_external_distance": None,
            "separation_ratio": None,
        }

    names, _, matrix = _numeric_matrix(profile_features)
    if matrix.size == 0 or len(names) < 2:
        return {
            "available": False,
            "reason": "At least two profiles and one numeric feature are required.",
            "cohorts": [],
            "overall_internal_distance": None,
            "overall_external_distance": None,
            "separation_ratio": None,
        }

    cohort_map = dict(
        zip(cohort_index["name"].astype(str), cohort_index["cohort"].astype(str), strict=False)
    )
    labels = np.array([cohort_map.get(name, "") for name in names], dtype=object)
    valid = labels != ""

    if valid.sum() < 2:
        return {
            "available": False,
            "reason": "Not enough profiles have cohort labels.",
            "cohorts": [],
            "overall_internal_distance": None,
            "overall_external_distance": None,
            "separation_ratio": None,
        }

    distances = np.linalg.norm(matrix[:, None, :] - matrix[None, :, :], axis=2)
    cohort_rows = []
    internal_values = []
    external_values = []

    for cohort in sorted(set(labels[valid].tolist())):
        cohort_indices = np.where(labels == cohort)[0]
        outside_indices = np.where((labels != cohort) & valid)[0]

        internal = None
        if len(cohort_indices) > 1:
            internal_matrix = distances[np.ix_(cohort_indices, cohort_indices)]
            upper = internal_matrix[np.triu_indices_from(internal_matrix, k=1)]
            internal = float(upper.mean()) if len(upper) else None
            if internal is not None:
                internal_values.append(internal)

        external = None
        if len(cohort_indices) and len(outside_indices):
            external = float(distances[np.ix_(cohort_indices, outside_indices)].mean())
            external_values.append(external)

        ratio = None
        if internal is not None and external is not None and external != 0:
            ratio = float(internal / external)

        cohort_rows.append(
            {
                "cohort": cohort,
                "profile_count": int(len(cohort_indices)),
                "internal_distance": internal,
                "external_distance": external,
                "internal_external_ratio": ratio,
            }
        )

    overall_internal = float(np.mean(internal_values)) if internal_values else None
    overall_external = float(np.mean(external_values)) if external_values else None
    separation_ratio = (
        float(overall_internal / overall_external)
        if overall_internal is not None and overall_external not in (None, 0.0)
        else None
    )

    return {
        "available": True,
        "reason": None,
        "cohorts": cohort_rows,
        "overall_internal_distance": overall_internal,
        "overall_external_distance": overall_external,
        "separation_ratio": separation_ratio,
    }


def build_statistical_intelligence_report(
    profile_features: pd.DataFrame,
    cohort_index: pd.DataFrame | None = None,
    k: int = 5,
    n_components: int = 3,
) -> dict[str, Any]:
    """Build the first Atlas statistical intelligence report."""
    pca = principal_components(profile_features, n_components=n_components)
    clusters = kmeans_clusters(profile_features, k=k)
    silhouettes = silhouette_scores(profile_features, clusters)

    mean_silhouette = None
    if not silhouettes.empty:
        mean_silhouette = float(silhouettes["silhouette"].mean())

    return {
        "profile_count": int(len(profile_features)) if not profile_features.empty else 0,
        "feature_count": int(len(_feature_columns(profile_features))) if not profile_features.empty else 0,
        "principal_components": pca,
        "clusters": clusters.to_dict(orient="records"),
        "cluster_summary": cluster_summary(clusters).to_dict(orient="records"),
        "silhouette_scores": silhouettes.to_dict(orient="records"),
        "mean_silhouette": mean_silhouette,
        "cohort_separation": cohort_separation(profile_features, cohort_index),
    }


def statistical_report_to_json(report: dict[str, Any]) -> str:
    """Serialize a statistical intelligence report."""
    return json.dumps(report, indent=2, sort_keys=True)