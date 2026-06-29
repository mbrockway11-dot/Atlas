"""Corpus feature diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.corpus.loader import load_corpus_csv


METADATA_PREFIXES = (
    "quality_",
    "diagnostic_",
)

METADATA_COLUMNS = {
    "name",
    "identity_vector_version",
    "normalization_mode",
    "primary_archetype",
    "primary_archetype_label",
    "secondary_archetype",
    "secondary_archetype_label",
}


@dataclass(frozen=True)
class CorpusFeatureDiagnostics:
    """Feature diagnostic report."""

    profile_count: int
    feature_count: int
    near_constant_features: list[dict[str, Any]]
    highest_variance_features: list[dict[str, Any]]
    lowest_variance_features: list[dict[str, Any]]
    highly_correlated_pairs: list[dict[str, Any]]
    summary: dict[str, Any]


def numeric_feature_columns(
    dataframe: pd.DataFrame,
    include_metadata: bool = False,
) -> list[str]:
    """Return numeric corpus feature columns."""
    numeric_columns = list(dataframe.select_dtypes(include=["number"]).columns)

    if include_metadata:
        return numeric_columns

    return [
        column
        for column in numeric_columns
        if column not in METADATA_COLUMNS
        and not column.startswith(METADATA_PREFIXES)
    ]


def build_feature_diagnostics(
    dataframe: pd.DataFrame,
    near_constant_threshold: float = 0.005,
    correlation_threshold: float = 0.95,
    top_n: int = 25,
) -> CorpusFeatureDiagnostics:
    """Build variance and redundancy diagnostics for corpus features."""
    feature_columns = numeric_feature_columns(dataframe)
    features = dataframe[feature_columns].copy()

    std = features.std(ddof=0).fillna(0.0)
    variance = features.var(ddof=0).fillna(0.0)
    means = features.mean().fillna(0.0)
    minimums = features.min().fillna(0.0)
    maximums = features.max().fillna(0.0)
    ranges = (maximums - minimums).fillna(0.0)

    feature_rows = [
        {
            "feature": feature,
            "mean": float(means[feature]),
            "std": float(std[feature]),
            "variance": float(variance[feature]),
            "min": float(minimums[feature]),
            "max": float(maximums[feature]),
            "range": float(ranges[feature]),
        }
        for feature in feature_columns
    ]

    by_variance_desc = sorted(
        feature_rows,
        key=lambda row: row["variance"],
        reverse=True,
    )

    by_variance_asc = sorted(
        feature_rows,
        key=lambda row: row["variance"],
    )

    near_constant_features = [
        row
        for row in by_variance_asc
        if row["std"] <= near_constant_threshold
    ]

    highly_correlated_pairs = find_highly_correlated_pairs(
        features,
        threshold=correlation_threshold,
    )

    summary = {
        "profile_count": int(len(dataframe)),
        "feature_count": int(len(feature_columns)),
        "near_constant_count": int(len(near_constant_features)),
        "highly_correlated_pair_count": int(len(highly_correlated_pairs)),
        "mean_feature_std": float(std.mean()) if len(std) else 0.0,
        "median_feature_std": float(std.median()) if len(std) else 0.0,
        "max_feature_std": float(std.max()) if len(std) else 0.0,
        "min_feature_std": float(std.min()) if len(std) else 0.0,
    }

    return CorpusFeatureDiagnostics(
        profile_count=int(len(dataframe)),
        feature_count=int(len(feature_columns)),
        near_constant_features=near_constant_features,
        highest_variance_features=by_variance_desc[:top_n],
        lowest_variance_features=by_variance_asc[:top_n],
        highly_correlated_pairs=highly_correlated_pairs[:top_n],
        summary=summary,
    )


def find_highly_correlated_pairs(
    features: pd.DataFrame,
    threshold: float = 0.95,
) -> list[dict[str, Any]]:
    """Find highly correlated feature pairs."""
    if features.empty:
        return []

    correlation = features.corr().fillna(0.0)
    columns = list(correlation.columns)

    pairs = []

    for index_a, feature_a in enumerate(columns):
        for index_b, feature_b in enumerate(columns):
            if index_b <= index_a:
                continue

            value = float(correlation.loc[feature_a, feature_b])

            if abs(value) >= threshold:
                pairs.append(
                    {
                        "feature_a": feature_a,
                        "feature_b": feature_b,
                        "correlation": value,
                        "absolute_correlation": abs(value),
                    }
                )

    return sorted(
        pairs,
        key=lambda row: row["absolute_correlation"],
        reverse=True,
    )


def diagnostics_to_dict(
    diagnostics: CorpusFeatureDiagnostics,
) -> dict[str, Any]:
    """Convert diagnostics to dictionary."""
    return {
        "profile_count": diagnostics.profile_count,
        "feature_count": diagnostics.feature_count,
        "summary": diagnostics.summary,
        "near_constant_features": diagnostics.near_constant_features,
        "highest_variance_features": diagnostics.highest_variance_features,
        "lowest_variance_features": diagnostics.lowest_variance_features,
        "highly_correlated_pairs": diagnostics.highly_correlated_pairs,
    }


def build_feature_diagnostics_from_csv(
    path: str | Path = "research/corpus/vectors.csv",
) -> CorpusFeatureDiagnostics:
    """Load corpus CSV and build feature diagnostics."""
    dataframe = load_corpus_csv(path)
    return build_feature_diagnostics(dataframe)