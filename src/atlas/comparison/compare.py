"""Identity comparison engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

import pandas as pd

from atlas.comparison.feature_registry import (
    FEATURE_REGISTRY_VERSION,
    feature_family,
    feature_is_registered,
    feature_weight,
    infer_planet_from_feature_name,
)
from atlas.corpus.similarity import (
    SimilarityMetric,
    distance_score,
    standardize_features,
)


FeatureMode = Literal["registered", "legacy"]


@dataclass(frozen=True)
class IdentityComparison:
    """Structured comparison between two corpus profiles."""

    profile_a: str
    profile_b: str
    metric: str
    similarity: float
    distance: float
    feature_count: int
    feature_mode: str
    feature_registry_version: str | None
    selected_features: list[str]
    most_similar_features: list[dict[str, Any]]
    most_different_features: list[dict[str, Any]]
    planet_summary: dict[str, Any]
    family_summary: dict[str, Any]
    interpretation_lines: list[str]


def compare_profiles(
    dataframe: pd.DataFrame,
    profile_a: str,
    profile_b: str,
    metric: SimilarityMetric = "euclidean",
    min_std: float = 0.005,
    top_n: int = 10,
    feature_mode: FeatureMode = "registered",
) -> IdentityComparison:
    """Compare two profiles using corpus-standardized semantic measurements."""

    if top_n < 1:
        raise ValueError("top_n must be at least 1.")

    row_a = _profile_row(dataframe, profile_a)
    row_b = _profile_row(dataframe, profile_b)

    feature_columns = comparison_feature_columns(
        dataframe=dataframe,
        min_std=min_std,
        feature_mode=feature_mode,
    )

    if not feature_columns:
        raise ValueError(
            "No usable comparison features were selected. "
            "Use feature_mode='legacy' to inspect the unregistered numeric set."
        )

    standardized = standardize_features(
        dataframe=dataframe,
        columns=feature_columns,
    )

    index_a = row_a.index[0]
    index_b = row_b.index[0]

    weighted_a = [
        float(standardized.loc[index_a, feature])
        * _active_feature_weight(feature, feature_mode)
        for feature in feature_columns
    ]

    weighted_b = [
        float(standardized.loc[index_b, feature])
        * _active_feature_weight(feature, feature_mode)
        for feature in feature_columns
    ]

    distance = distance_score(
        weighted_a,
        weighted_b,
        metric=metric,
    )

    similarity = _similarity_from_distance(
        weighted_a,
        weighted_b,
        metric=metric,
        distance=distance,
    )

    all_feature_rows = build_feature_difference_rows(
        dataframe=dataframe,
        standardized=standardized,
        index_a=index_a,
        index_b=index_b,
        feature_columns=feature_columns,
        feature_mode=feature_mode,
    )

    most_similar = sorted(
        all_feature_rows,
        key=lambda row: (
            row["weighted_standardized_difference"],
            row["feature"],
        ),
    )[:top_n]

    most_different = sorted(
        all_feature_rows,
        key=lambda row: (
            row["weighted_standardized_difference"],
            row["feature"],
        ),
        reverse=True,
    )[:top_n]

    planet_summary = build_planet_difference_summary(all_feature_rows)
    family_summary = build_feature_family_summary(all_feature_rows)

    interpretation_lines = build_comparison_interpretation(
        profile_a=profile_a,
        profile_b=profile_b,
        similarity=similarity,
        distance=distance,
        planet_summary=planet_summary,
        family_summary=family_summary,
        most_different_features=most_different,
    )

    return IdentityComparison(
        profile_a=profile_a,
        profile_b=profile_b,
        metric=metric,
        similarity=similarity,
        distance=distance,
        feature_count=len(feature_columns),
        feature_mode=feature_mode,
        feature_registry_version=(
            FEATURE_REGISTRY_VERSION
            if feature_mode == "registered"
            else None
        ),
        selected_features=list(feature_columns),
        most_similar_features=most_similar,
        most_different_features=most_different,
        planet_summary=planet_summary,
        family_summary=family_summary,
        interpretation_lines=interpretation_lines,
    )


def _profile_row(
    dataframe: pd.DataFrame,
    profile_name: str,
) -> pd.DataFrame:
    if "name" not in dataframe.columns:
        raise ValueError("Corpus dataframe must contain a 'name' column.")

    matches = dataframe[dataframe["name"] == profile_name]

    if matches.empty:
        raise ValueError(f"Profile not found in corpus: {profile_name}")

    return matches.iloc[[0]]


def comparison_feature_columns(
    dataframe: pd.DataFrame,
    min_std: float = 0.005,
    feature_mode: FeatureMode = "registered",
) -> list[str]:
    """Select comparison-safe numeric columns."""

    numeric_columns = list(
        dataframe.select_dtypes(include=["number"]).columns
    )

    candidates = [
        column
        for column in numeric_columns
        if column != "name"
    ]

    if feature_mode == "registered":
        candidates = [
            column
            for column in candidates
            if feature_is_registered(column)
        ]
    elif feature_mode != "legacy":
        raise ValueError(
            "feature_mode must be 'registered' or 'legacy'."
        )

    if not candidates:
        return []

    standard_deviations = (
        dataframe[candidates]
        .std(ddof=0)
        .fillna(0.0)
    )

    return sorted(
        column
        for column in candidates
        if float(standard_deviations[column]) > min_std
    )


def _active_feature_weight(
    feature: str,
    feature_mode: FeatureMode,
) -> float:
    if feature_mode == "legacy":
        return 1.0

    return feature_weight(feature)


def _similarity_from_distance(
    values_a: list[float],
    values_b: list[float],
    *,
    metric: SimilarityMetric,
    distance: float,
) -> float:
    if metric in {"euclidean", "manhattan"}:
        return 1.0 / (1.0 + float(distance))

    if metric in {"cosine", "pearson"}:
        return 1.0 - float(distance)

    raise ValueError(f"Unsupported similarity metric: {metric}")


def build_feature_difference_rows(
    *,
    dataframe: pd.DataFrame,
    standardized: pd.DataFrame,
    index_a: Any,
    index_b: Any,
    feature_columns: list[str],
    feature_mode: FeatureMode,
) -> list[dict[str, Any]]:
    """Build auditable feature-level difference rows."""

    rows: list[dict[str, Any]] = []

    for feature in feature_columns:
        raw_a = float(dataframe.loc[index_a, feature])
        raw_b = float(dataframe.loc[index_b, feature])
        z_a = float(standardized.loc[index_a, feature])
        z_b = float(standardized.loc[index_b, feature])

        weight = _active_feature_weight(feature, feature_mode)
        standardized_difference = abs(z_a - z_b)

        rows.append(
            {
                "feature": feature,
                "family": feature_family(feature),
                "planet": infer_planet_from_feature(feature),
                "weight": weight,
                "value_a": raw_a,
                "value_b": raw_b,
                "z_a": z_a,
                "z_b": z_b,
                "raw_difference": abs(raw_a - raw_b),
                "standardized_difference": standardized_difference,
                "weighted_standardized_difference": (
                    standardized_difference * weight
                ),
            }
        )

    return rows


def build_planet_difference_summary(
    different_features: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize all usable feature differences by planet."""

    planet_rows: dict[str, list[float]] = {}

    for row in different_features:
        planet = row.get("planet") or infer_planet_from_feature(
            str(row["feature"])
        )

        if planet is None:
            continue

        planet_rows.setdefault(planet, []).append(
            float(
                row.get(
                    "weighted_standardized_difference",
                    row["standardized_difference"],
                )
            )
        )

    ranked = []

    for planet, values in planet_rows.items():
        total = sum(values)
        count = len(values)
        mean_difference = total / count if count else 0.0

        ranked.append(
            {
                "planet": planet,
                "feature_count": count,
                "total_difference": total,
                "mean_difference": mean_difference,
                "difference_level": classify_difference(mean_difference),
            }
        )

    ranked.sort(
        key=lambda row: (
            row["mean_difference"],
            row["planet"],
        ),
        reverse=True,
    )

    return {
        "ranked_planets": ranked,
        "most_divergent_planet": (
            ranked[0]["planet"] if ranked else None
        ),
        "least_divergent_planet": (
            ranked[-1]["planet"] if ranked else None
        ),
    }


def build_feature_family_summary(
    feature_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize differences by semantic feature family."""

    grouped: dict[str, list[float]] = {}

    for row in feature_rows:
        family = row.get("family") or "unclassified"

        grouped.setdefault(family, []).append(
            float(row["weighted_standardized_difference"])
        )

    ranked = []

    for family, values in grouped.items():
        total = sum(values)
        count = len(values)

        ranked.append(
            {
                "family": family,
                "feature_count": count,
                "total_difference": total,
                "mean_difference": total / count if count else 0.0,
            }
        )

    ranked.sort(
        key=lambda row: (
            row["mean_difference"],
            row["family"],
        ),
        reverse=True,
    )

    return {
        "ranked_families": ranked,
        "most_divergent_family": (
            ranked[0]["family"] if ranked else None
        ),
        "least_divergent_family": (
            ranked[-1]["family"] if ranked else None
        ),
    }


def infer_planet_from_feature(feature: str) -> str | None:
    """Infer planet from supported flattened naming conventions."""

    return infer_planet_from_feature_name(feature)


def classify_difference(value: float) -> str:
    """Classify standardized difference strength."""

    if value >= 2.0:
        return "strong"

    if value >= 1.0:
        return "moderate"

    return "low"


def build_comparison_interpretation(
    *,
    profile_a: str,
    profile_b: str,
    similarity: float,
    distance: float,
    planet_summary: dict[str, Any],
    family_summary: dict[str, Any] | None = None,
    most_different_features: list[dict[str, Any]],
) -> list[str]:
    """Build deterministic, measurement-first comparison lines."""

    lines = [
        (
            f"{profile_a} and {profile_b} have a structural similarity of "
            f"{similarity:.4f} with a standardized distance of "
            f"{distance:.4f} using the selected corpus metric."
        )
    ]

    most_divergent_planet = planet_summary.get(
        "most_divergent_planet"
    )

    if most_divergent_planet:
        lines.append(
            "The greatest planet-level divergence occurs within "
            f"{most_divergent_planet}."
        )

    if family_summary:
        most_divergent_family = family_summary.get(
            "most_divergent_family"
        )

        if most_divergent_family:
            lines.append(
                "The greatest feature-family divergence occurs within "
                f"{most_divergent_family}."
            )

    if most_different_features:
        feature = most_different_features[0]

        lines.append(
            "The strongest distinguishing feature is "
            f"{feature['feature']} "
            "(weighted delta-z = "
            f"{feature['weighted_standardized_difference']:.4f})."
        )

    if len(most_different_features) >= 3:
        top_features = ", ".join(
            row["feature"]
            for row in most_different_features[:3]
        )

        lines.append(
            "The three largest structural separators are: "
            f"{top_features}."
        )

    return lines


def identity_comparison_to_dict(
    comparison: IdentityComparison,
) -> dict[str, Any]:
    """Convert an identity comparison to a serializable dictionary."""

    return {
        "profile_a": comparison.profile_a,
        "profile_b": comparison.profile_b,
        "metric": comparison.metric,
        "similarity": comparison.similarity,
        "distance": comparison.distance,
        "feature_count": comparison.feature_count,
        "feature_mode": comparison.feature_mode,
        "feature_registry_version": comparison.feature_registry_version,
        "selected_features": comparison.selected_features,
        "most_similar_features": comparison.most_similar_features,
        "most_different_features": comparison.most_different_features,
        "planet_summary": comparison.planet_summary,
        "family_summary": comparison.family_summary,
        "interpretation_lines": comparison.interpretation_lines,
    }
