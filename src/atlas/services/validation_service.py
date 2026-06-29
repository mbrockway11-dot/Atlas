"""Validation service utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.research.validation import (
    build_population_validation_report,
    build_profile_feature_matrix,
    correlated_feature_pairs,
    data_quality_checks,
    feature_variance,
    load_cohort_index,
    nearest_neighbors,
    numeric_columns,
    outlier_scores,
    report_to_json,
)
from atlas.services.population_service import load_population_matrix

DEFAULT_COHORT_INDEX = Path("research/profile_intake/cohort_index.csv")


def get_population_matrix() -> pd.DataFrame:
    """Return current row-level population matrix."""
    return load_population_matrix()


def get_profile_feature_matrix(matrix: pd.DataFrame | None = None) -> pd.DataFrame:
    """Return current profile-level feature matrix."""
    source = matrix if matrix is not None else get_population_matrix()
    return build_profile_feature_matrix(source)


def get_cohort_index(path: str | Path | None = DEFAULT_COHORT_INDEX) -> pd.DataFrame:
    """Load optional cohort index."""
    return load_cohort_index(path)


def get_population_validation_report(
    cohort_path: str | Path | None = DEFAULT_COHORT_INDEX,
    correlation_threshold: float = 0.95,
) -> dict[str, Any]:
    """Build validation report for current profile library."""
    matrix = get_population_matrix()
    cohorts = get_cohort_index(cohort_path)

    return build_population_validation_report(
        matrix,
        cohort_index=cohorts,
        correlation_threshold=correlation_threshold,
    )


def get_numeric_columns(matrix: pd.DataFrame) -> list[str]:
    """Return numeric validation columns."""
    return numeric_columns(matrix)


def get_data_quality(matrix: pd.DataFrame) -> dict[str, Any]:
    """Return data quality checks."""
    return data_quality_checks(matrix)


def get_feature_variance(matrix: pd.DataFrame) -> dict[str, Any]:
    """Return feature variance summary."""
    return feature_variance(matrix)


def get_nearest_neighbors(
    profile_features: pd.DataFrame,
    selected_profile: str,
    *,
    limit: int = 10,
    metric: str = "cosine",
) -> list[dict[str, Any]]:
    """Return nearest neighbors for selected profile."""
    return nearest_neighbors(
        profile_features,
        selected_profile,
        limit=limit,
        metric=metric,
    )


def get_outlier_scores(profile_features: pd.DataFrame) -> pd.DataFrame:
    """Return population outlier scores."""
    return outlier_scores(profile_features)


def get_correlated_feature_pairs(
    profile_features: pd.DataFrame,
    *,
    threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """Return highly correlated feature pairs."""
    return correlated_feature_pairs(profile_features, threshold=threshold)


def validation_report_json(report: dict[str, Any]) -> str:
    """Serialize report to JSON."""
    return report_to_json(report)