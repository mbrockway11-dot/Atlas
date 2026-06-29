"""Corpus similarity utilities."""

from __future__ import annotations

from math import sqrt

import pandas as pd


def find_nearest_profiles(
    dataframe: pd.DataFrame,
    profile_name: str,
    top_n: int = 10,
) -> pd.DataFrame:
    """Find nearest profiles by cosine similarity over numeric columns."""
    if "name" not in dataframe.columns:
        raise ValueError("Corpus dataframe must contain a 'name' column.")

    matches = dataframe[dataframe["name"] == profile_name]

    if matches.empty:
        raise ValueError(f"Profile not found in corpus: {profile_name}")

    numeric_columns = [
        column
        for column in dataframe.select_dtypes(include=["number"]).columns
        if not column.startswith("metadata_")
    ]

    target = matches.iloc[0]

    rows = []

    for _, row in dataframe.iterrows():
        name = row["name"]

        if name == profile_name:
            continue

        similarity = cosine_similarity(
            [target[column] for column in numeric_columns],
            [row[column] for column in numeric_columns],
        )

        rows.append(
            {
                "name": name,
                "similarity": similarity,
            }
        )

    return pd.DataFrame(rows).sort_values(
        "similarity",
        ascending=False,
    ).head(top_n)


def cosine_similarity(values_a: list[float], values_b: list[float]) -> float:
    """Cosine similarity for numeric lists."""
    dot = sum(float(a) * float(b) for a, b in zip(values_a, values_b))
    norm_a = sqrt(sum(float(a) ** 2 for a in values_a))
    norm_b = sqrt(sum(float(b) ** 2 for b in values_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return dot / (norm_a * norm_b)