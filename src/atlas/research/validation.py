"""Population validation tools for Atlas research matrices.

This module answers whether the current research matrix has usable population
structure before adding new symbolic engines.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

IDENTITY_COLUMNS = {
    "name",
    "cipher",
    "planet",
    "kamea",
    "subtype_primary",
    "subtype_secondary",
}

EXPECTED_ROWS_PER_PROFILE = 21


def load_research_matrix(path: str | Path) -> pd.DataFrame:
    """Load a research matrix CSV."""
    matrix_path = Path(path)

    if not matrix_path.exists():
        raise FileNotFoundError(f"Research matrix not found: {matrix_path}")

    return pd.read_csv(matrix_path)


def load_cohort_index(path: str | Path | None) -> pd.DataFrame:
    """Load optional cohort mapping with columns: name, cohort."""
    if path is None:
        return pd.DataFrame(columns=["name", "cohort"])

    cohort_path = Path(path)

    if not cohort_path.exists():
        return pd.DataFrame(columns=["name", "cohort"])

    cohorts = pd.read_csv(cohort_path)

    required = {"name", "cohort"}
    missing = required.difference(cohorts.columns)
    if missing:
        raise ValueError(
            f"Cohort index must contain columns {sorted(required)}; "
            f"missing {sorted(missing)}"
        )

    return cohorts[["name", "cohort"]].drop_duplicates()


def numeric_columns(dataframe: pd.DataFrame) -> list[str]:
    """Return numeric research metric columns."""
    return [
        column
        for column in dataframe.columns
        if column not in IDENTITY_COLUMNS
        and pd.api.types.is_numeric_dtype(dataframe[column])
    ]


def corpus_summary(dataframe: pd.DataFrame) -> dict[str, Any]:
    """Build top-level corpus summary."""
    numeric = numeric_columns(dataframe)

    return {
        "row_count": int(len(dataframe)),
        "unique_profiles": int(dataframe["name"].nunique()) if "name" in dataframe else 0,
        "cipher_count": int(dataframe["cipher"].nunique()) if "cipher" in dataframe else 0,
        "planet_count": int(dataframe["planet"].nunique()) if "planet" in dataframe else 0,
        "kamea_count": int(dataframe["kamea"].nunique()) if "kamea" in dataframe else 0,
        "numeric_metric_count": int(len(numeric)),
        "numeric_metrics": numeric,
    }


def data_quality_checks(
    dataframe: pd.DataFrame,
    expected_rows_per_profile: int = EXPECTED_ROWS_PER_PROFILE,
) -> dict[str, Any]:
    """Audit missing values, duplicate rows, and missing realizations."""
    subset = [column for column in ["name", "cipher", "planet"] if column in dataframe.columns]

    duplicate_count = (
        int(dataframe.duplicated(subset=subset).sum())
        if subset
        else 0
    )

    rows_per_profile = (
        dataframe.groupby("name").size().sort_index().astype(int).to_dict()
        if "name" in dataframe
        else {}
    )

    incomplete_profiles = {
        name: int(count)
        for name, count in rows_per_profile.items()
        if count != expected_rows_per_profile
    }

    missing_values = {
        column: int(count)
        for column, count in dataframe.isna().sum().items()
        if int(count) > 0
    }

    return {
        "missing_values": missing_values,
        "duplicate_profile_cipher_planet_rows": duplicate_count,
        "rows_per_profile": rows_per_profile,
        "expected_rows_per_profile": int(expected_rows_per_profile),
        "profiles_missing_realizations": incomplete_profiles,
        "profile_count_with_missing_realizations": int(len(incomplete_profiles)),
    }


def feature_variance(
    dataframe: pd.DataFrame,
    low_variance_threshold: float = 1e-9,
) -> dict[str, Any]:
    """Summarize zero, low, and high variance numeric features."""
    numeric = numeric_columns(dataframe)

    if not numeric:
        return {
            "zero_variance_columns": [],
            "low_variance_columns": [],
            "highest_variance_columns": [],
        }

    variances = dataframe[numeric].var(numeric_only=True).fillna(0.0).sort_values()

    zero = [column for column, value in variances.items() if float(value) == 0.0]
    low = [
        column
        for column, value in variances.items()
        if 0.0 < float(value) <= low_variance_threshold
    ]
    high = [
        {"feature": column, "variance": float(value)}
        for column, value in variances.sort_values(ascending=False).head(25).items()
    ]

    return {
        "zero_variance_columns": zero,
        "low_variance_columns": low,
        "highest_variance_columns": high,
    }


def build_profile_feature_matrix(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Aggregate row-level research metrics into one row per profile."""
    if "name" not in dataframe.columns:
        return pd.DataFrame()

    numeric = numeric_columns(dataframe)
    if not numeric:
        return pd.DataFrame({"name": sorted(dataframe["name"].unique())})

    grouped = dataframe.groupby("name", sort=True)[numeric]
    aggregate = grouped.agg(["mean", "std", "min", "max"])
    aggregate.columns = [f"{metric}_{stat}" for metric, stat in aggregate.columns]
    aggregate = aggregate.fillna(0.0).reset_index()

    return aggregate


def normalize_profile_features(profile_features: pd.DataFrame) -> pd.DataFrame:
    """Z-normalize profile-level feature columns."""
    if profile_features.empty:
        return profile_features.copy()

    normalized = profile_features.copy()
    feature_columns = [column for column in normalized.columns if column != "name"]

    if not feature_columns:
        return normalized

    values = normalized[feature_columns].astype(float)
    means = values.mean(axis=0)
    stds = values.std(axis=0).replace(0.0, 1.0).fillna(1.0)
    normalized[feature_columns] = (values - means) / stds

    return normalized.fillna(0.0)


def nearest_neighbors(
    profile_features: pd.DataFrame,
    selected_profile: str,
    limit: int = 10,
    metric: str = "cosine",
) -> list[dict[str, Any]]:
    """Find nearest neighbors for a selected profile."""
    if profile_features.empty or "name" not in profile_features.columns:
        return []

    normalized = normalize_profile_features(profile_features)
    names = normalized["name"].tolist()

    if selected_profile not in names:
        return []

    feature_columns = [column for column in normalized.columns if column != "name"]
    if not feature_columns:
        return []

    matrix = normalized[feature_columns].to_numpy(dtype=float)
    selected_index = names.index(selected_profile)
    selected_vector = matrix[selected_index]

    rows = []
    for index, name in enumerate(names):
        if name == selected_profile:
            continue

        candidate = matrix[index]

        if metric == "euclidean":
            distance = float(np.linalg.norm(selected_vector - candidate))
            similarity = float(1.0 / (1.0 + distance))
        else:
            denominator = float(np.linalg.norm(selected_vector) * np.linalg.norm(candidate))
            similarity = float(np.dot(selected_vector, candidate) / denominator) if denominator else 0.0
            distance = float(1.0 - similarity)

        rows.append(
            {
                "name": name,
                "similarity": similarity,
                "distance": distance,
                "metric": metric,
            }
        )

    rows.sort(key=lambda item: (item["distance"], item["name"]))
    return rows[:limit]


def outlier_scores(profile_features: pd.DataFrame) -> pd.DataFrame:
    """Rank profiles by distance from the normalized population centroid."""
    if profile_features.empty or "name" not in profile_features.columns:
        return pd.DataFrame(columns=["name", "centroid_distance"])

    normalized = normalize_profile_features(profile_features)
    feature_columns = [column for column in normalized.columns if column != "name"]

    if not feature_columns:
        return pd.DataFrame(columns=["name", "centroid_distance"])

    matrix = normalized[feature_columns].to_numpy(dtype=float)
    centroid = matrix.mean(axis=0)
    distances = np.linalg.norm(matrix - centroid, axis=1)

    result = pd.DataFrame(
        {
            "name": normalized["name"],
            "centroid_distance": distances,
        }
    )

    return result.sort_values(
        by=["centroid_distance", "name"],
        ascending=[False, True],
    ).reset_index(drop=True)


def correlated_feature_pairs(
    profile_features: pd.DataFrame,
    threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """List highly correlated profile-level feature pairs."""
    feature_columns = [column for column in profile_features.columns if column != "name"]

    if len(feature_columns) < 2:
        return []

    corr = profile_features[feature_columns].corr(numeric_only=True).fillna(0.0)
    pairs = []

    for left_index, left in enumerate(feature_columns):
        for right in feature_columns[left_index + 1:]:
            value = float(corr.loc[left, right])
            if abs(value) >= threshold:
                pairs.append(
                    {
                        "feature_a": left,
                        "feature_b": right,
                        "correlation": value,
                        "absolute_correlation": abs(value),
                    }
                )

    pairs.sort(key=lambda item: (-item["absolute_correlation"], item["feature_a"], item["feature_b"]))
    return pairs


def cohort_support(
    profile_features: pd.DataFrame,
    cohort_index: pd.DataFrame | None = None,
) -> dict[str, Any]:
    """Summarize optional cohort support."""
    if cohort_index is None or cohort_index.empty:
        return {
            "available": False,
            "cohort_counts": {},
            "profiles_without_cohort": profile_features["name"].tolist() if "name" in profile_features else [],
        }

    merged = profile_features[["name"]].merge(cohort_index, on="name", how="left")
    counts = merged["cohort"].dropna().value_counts().sort_index().astype(int).to_dict()
    missing = merged.loc[merged["cohort"].isna(), "name"].tolist()

    return {
        "available": True,
        "cohort_counts": counts,
        "profiles_without_cohort": missing,
    }


def build_population_validation_report(
    matrix: pd.DataFrame,
    cohort_index: pd.DataFrame | None = None,
    correlation_threshold: float = 0.95,
) -> dict[str, Any]:
    """Build complete population validation report."""
    profile_features = build_profile_feature_matrix(matrix)
    outliers = outlier_scores(profile_features)

    return {
        "corpus_summary": corpus_summary(matrix),
        "data_quality": data_quality_checks(matrix),
        "feature_variance": feature_variance(matrix),
        "cohort_support": cohort_support(profile_features, cohort_index),
        "outliers": outliers.head(50).to_dict(orient="records"),
        "correlated_feature_pairs": correlated_feature_pairs(
            profile_features,
            threshold=correlation_threshold,
        ),
    }


def report_to_json(report: dict[str, Any]) -> str:
    """Serialize validation report to stable JSON."""
    return json.dumps(report, indent=2, sort_keys=True)