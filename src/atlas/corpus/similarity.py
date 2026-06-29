"""Corpus similarity utilities."""

from __future__ import annotations

from math import sqrt
from typing import Any, Literal

import pandas as pd


SimilarityMetric = Literal[
    "euclidean",
    "manhattan",
    "pearson",
    "cosine",
]


EXCLUDED_PREFIXES = (
    "quality_",
    "diagnostic_",
)

EXCLUDED_SUFFIXES = (
    "_source_count",
)

EXCLUDED_COLUMNS = {
    "name",
    "identity_vector_version",
    "normalization_mode",
    "primary_archetype",
    "primary_archetype_label",
    "secondary_archetype",
    "secondary_archetype_label",
}


def find_nearest_profiles(
    dataframe: pd.DataFrame,
    profile_name: str,
    top_n: int = 10,
    metric: SimilarityMetric = "euclidean",
    min_std: float = 0.005,
) -> pd.DataFrame:
    """Find nearest profiles using filtered, standardized numeric features."""
    if "name" not in dataframe.columns:
        raise ValueError("Corpus dataframe must contain a 'name' column.")

    matches = dataframe[dataframe["name"] == profile_name]

    if matches.empty:
        raise ValueError(f"Profile not found in corpus: {profile_name}")

    feature_columns = numeric_similarity_columns(
        dataframe=dataframe,
        min_std=min_std,
    )

    if not feature_columns:
        raise ValueError("No usable numeric similarity columns found.")

    standardized = standardize_features(
        dataframe=dataframe,
        columns=feature_columns,
    )

    target_index = matches.index[0]
    target_values = standardized.loc[target_index, feature_columns].tolist()

    rows = []

    for index, row in dataframe.iterrows():
        name = row["name"]

        if name == profile_name:
            continue

        candidate_values = standardized.loc[index, feature_columns].tolist()

        score = similarity_score(
            target_values,
            candidate_values,
            metric=metric,
        )

        distance = distance_score(
            target_values,
            candidate_values,
            metric=metric,
        )

        rows.append(
            {
                "name": name,
                "similarity": score,
                "distance": distance,
                "metric": metric,
                "feature_count": len(feature_columns),
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["similarity", "distance"],
        ascending=[False, True],
    ).head(top_n)


def explain_profile_difference(
    dataframe: pd.DataFrame,
    profile_a: str,
    profile_b: str,
    min_std: float = 0.005,
    top_n: int = 10,
) -> dict[str, Any]:
    """Explain feature-level similarity/difference between two profiles."""
    if "name" not in dataframe.columns:
        raise ValueError("Corpus dataframe must contain a 'name' column.")

    row_a = dataframe[dataframe["name"] == profile_a]
    row_b = dataframe[dataframe["name"] == profile_b]

    if row_a.empty:
        raise ValueError(f"Profile not found in corpus: {profile_a}")

    if row_b.empty:
        raise ValueError(f"Profile not found in corpus: {profile_b}")

    feature_columns = numeric_similarity_columns(
        dataframe=dataframe,
        min_std=min_std,
    )

    standardized = standardize_features(
        dataframe=dataframe,
        columns=feature_columns,
    )

    index_a = row_a.index[0]
    index_b = row_b.index[0]

    rows = []

    for feature in feature_columns:
        raw_a = float(dataframe.loc[index_a, feature])
        raw_b = float(dataframe.loc[index_b, feature])
        z_a = float(standardized.loc[index_a, feature])
        z_b = float(standardized.loc[index_b, feature])

        rows.append(
            {
                "feature": feature,
                "value_a": raw_a,
                "value_b": raw_b,
                "z_a": z_a,
                "z_b": z_b,
                "raw_difference": abs(raw_a - raw_b),
                "standardized_difference": abs(z_a - z_b),
            }
        )

    most_similar = sorted(
        rows,
        key=lambda row: row["standardized_difference"],
    )[:top_n]

    most_different = sorted(
        rows,
        key=lambda row: row["standardized_difference"],
        reverse=True,
    )[:top_n]

    return {
        "profile_a": profile_a,
        "profile_b": profile_b,
        "feature_count": len(feature_columns),
        "most_similar_features": most_similar,
        "most_different_features": most_different,
    }


def numeric_similarity_columns(
    dataframe: pd.DataFrame,
    min_std: float = 0.005,
) -> list[str]:
    """Return numeric columns usable for similarity."""
    numeric_columns = list(dataframe.select_dtypes(include=["number"]).columns)

    candidates = [
        column
        for column in numeric_columns
        if column not in EXCLUDED_COLUMNS
        and not column.startswith(EXCLUDED_PREFIXES)
        and not column.endswith(EXCLUDED_SUFFIXES)
    ]

    if not candidates:
        return []

    std = dataframe[candidates].std(ddof=0).fillna(0.0)

    return [
        column
        for column in candidates
        if float(std[column]) > min_std
    ]


def standardize_features(
    dataframe: pd.DataFrame,
    columns: list[str],
) -> pd.DataFrame:
    """Z-score standardize selected features."""
    standardized = dataframe.copy()

    means = dataframe[columns].mean()
    stds = dataframe[columns].std(ddof=0).replace(0.0, 1.0)

    standardized[columns] = (
        dataframe[columns] - means
    ) / stds

    return standardized.fillna(0.0)


def similarity_score(
    values_a: list[float],
    values_b: list[float],
    metric: SimilarityMetric = "euclidean",
) -> float:
    """Return normalized similarity where higher is more similar."""
    if metric == "cosine":
        return cosine_similarity(values_a, values_b)

    if metric == "pearson":
        return pearson_similarity(values_a, values_b)

    distance = distance_score(
        values_a,
        values_b,
        metric=metric,
    )

    return 1.0 / (1.0 + distance)


def distance_score(
    values_a: list[float],
    values_b: list[float],
    metric: SimilarityMetric = "euclidean",
) -> float:
    """Return distance where lower is more similar."""
    if metric == "euclidean":
        return euclidean_distance(values_a, values_b)

    if metric == "manhattan":
        return manhattan_distance(values_a, values_b)

    if metric == "cosine":
        return 1.0 - cosine_similarity(values_a, values_b)

    if metric == "pearson":
        return 1.0 - pearson_similarity(values_a, values_b)

    raise ValueError(f"Unsupported similarity metric: {metric}")


def euclidean_distance(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Mean-normalized Euclidean distance."""
    if not values_a:
        return 0.0

    squared = [
        (float(a) - float(b)) ** 2
        for a, b in zip(values_a, values_b)
    ]

    return sqrt(sum(squared) / len(squared))


def manhattan_distance(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Mean absolute distance."""
    if not values_a:
        return 0.0

    return sum(
        abs(float(a) - float(b))
        for a, b in zip(values_a, values_b)
    ) / len(values_a)


def cosine_similarity(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Cosine similarity."""
    dot = sum(float(a) * float(b) for a, b in zip(values_a, values_b))
    norm_a = sqrt(sum(float(a) ** 2 for a in values_a))
    norm_b = sqrt(sum(float(b) ** 2 for b in values_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)


def pearson_similarity(
    values_a: list[float],
    values_b: list[float],
) -> float:
    """Pearson correlation converted to 0-1 similarity."""
    if not values_a:
        return 0.0

    mean_a = sum(float(value) for value in values_a) / len(values_a)
    mean_b = sum(float(value) for value in values_b) / len(values_b)

    centered_a = [
        float(value) - mean_a
        for value in values_a
    ]
    centered_b = [
        float(value) - mean_b
        for value in values_b
    ]

    numerator = sum(
        a * b
        for a, b in zip(centered_a, centered_b)
    )

    denominator = sqrt(
        sum(a ** 2 for a in centered_a)
        * sum(b ** 2 for b in centered_b)
    )

    if denominator == 0.0:
        return 0.0

    correlation = numerator / denominator

    return (correlation + 1.0) / 2.0