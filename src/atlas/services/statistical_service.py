"""Statistical intelligence service utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.research.statistical import (
    build_statistical_intelligence_report,
    cluster_summary,
    cohort_separation,
    kmeans_clusters,
    principal_components,
    silhouette_scores,
    statistical_report_to_json,
)
from atlas.services.population_service import load_population_matrix
from atlas.services.validation_service import get_cohort_index, get_profile_feature_matrix

DEFAULT_COHORT_INDEX = Path("research/profile_intake/cohort_index.csv")


def get_statistical_population_matrix() -> pd.DataFrame:
    """Return current row-level population matrix."""
    return load_population_matrix()


def get_statistical_profile_features(matrix: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return profile-level feature matrix for statistical analysis."""
    if matrix is None:
        matrix = get_statistical_population_matrix()
    return get_profile_feature_matrix(matrix)


def get_principal_components(
    profile_features: pd.DataFrame,
    *,
    n_components: int = 3,
) -> dict[str, Any]:
    """Return PCA-style principal components."""
    return principal_components(profile_features, n_components=n_components)


def get_kmeans_clusters(
    profile_features: pd.DataFrame,
    *,
    k: int = 5,
) -> pd.DataFrame:
    """Return deterministic k-means cluster assignments."""
    return kmeans_clusters(profile_features, k=k)


def get_cluster_summary(assignments: pd.DataFrame) -> pd.DataFrame:
    """Return cluster summary."""
    return cluster_summary(assignments)


def get_silhouette_scores(
    profile_features: pd.DataFrame,
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    """Return silhouette scores."""
    return silhouette_scores(profile_features, assignments)


def get_cohort_separation(
    profile_features: pd.DataFrame,
    cohort_path: str | Path | None = DEFAULT_COHORT_INDEX,
) -> dict[str, Any]:
    """Return cohort separation metrics."""
    cohort_index = get_cohort_index(cohort_path)
    return cohort_separation(profile_features, cohort_index)


def get_statistical_intelligence_report(
    profile_features: pd.DataFrame,
    *,
    cohort_path: str | Path | None = DEFAULT_COHORT_INDEX,
    k: int = 5,
    n_components: int = 3,
) -> dict[str, Any]:
    """Return complete statistical intelligence report."""
    cohort_index = get_cohort_index(cohort_path)
    return build_statistical_intelligence_report(
        profile_features,
        cohort_index=cohort_index,
        k=k,
        n_components=n_components,
    )


def statistical_json(report: dict[str, Any]) -> str:
    """Serialize statistical intelligence report."""
    return statistical_report_to_json(report)