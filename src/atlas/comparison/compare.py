"""Identity comparison engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from atlas.corpus.similarity import (
    SimilarityMetric,
    explain_profile_difference,
    find_nearest_profiles,
)


@dataclass(frozen=True)
class IdentityComparison:
    """Structured comparison between two corpus profiles."""

    profile_a: str
    profile_b: str
    metric: str
    similarity: float
    distance: float
    feature_count: int
    most_similar_features: list[dict[str, Any]]
    most_different_features: list[dict[str, Any]]
    planet_summary: dict[str, Any]
    interpretation_lines: list[str]


def compare_profiles(
    dataframe: pd.DataFrame,
    profile_a: str,
    profile_b: str,
    metric: SimilarityMetric = "euclidean",
    min_std: float = 0.005,
    top_n: int = 10,
) -> IdentityComparison:
    """Compare two profiles in the corpus."""
    nearest = find_nearest_profiles(
        dataframe=dataframe,
        profile_name=profile_a,
        top_n=len(dataframe),
        metric=metric,
        min_std=min_std,
    )

    match = nearest[nearest["name"] == profile_b]

    if match.empty:
        raise ValueError(f"Could not compare profiles: {profile_a} and {profile_b}")

    match_row = match.iloc[0]

    feature_explanation = explain_profile_difference(
        dataframe=dataframe,
        profile_a=profile_a,
        profile_b=profile_b,
        min_std=min_std,
        top_n=top_n,
    )

    planet_summary = build_planet_difference_summary(
        feature_explanation["most_different_features"],
    )

    interpretation_lines = build_comparison_interpretation(
        profile_a=profile_a,
        profile_b=profile_b,
        similarity=float(match_row["similarity"]),
        distance=float(match_row["distance"]),
        planet_summary=planet_summary,
        most_different_features=feature_explanation["most_different_features"],
    )

    return IdentityComparison(
        profile_a=profile_a,
        profile_b=profile_b,
        metric=metric,
        similarity=float(match_row["similarity"]),
        distance=float(match_row["distance"]),
        feature_count=int(match_row["feature_count"]),
        most_similar_features=feature_explanation["most_similar_features"],
        most_different_features=feature_explanation["most_different_features"],
        planet_summary=planet_summary,
        interpretation_lines=interpretation_lines,
    )


def build_planet_difference_summary(
    different_features: list[dict[str, Any]],
) -> dict[str, Any]:
    """Summarize feature differences by planetary prefix."""
    planet_totals: dict[str, float] = {}
    planet_counts: dict[str, int] = {}

    for row in different_features:
        feature = row["feature"]
        planet = infer_planet_from_feature(feature)

        if planet is None:
            continue

        planet_totals.setdefault(planet, 0.0)
        planet_counts.setdefault(planet, 0)

        planet_totals[planet] += float(row["standardized_difference"])
        planet_counts[planet] += 1

    planet_rows = []

    for planet, total in planet_totals.items():
        count = planet_counts[planet]
        mean_difference = total / count if count else 0.0

        planet_rows.append(
            {
                "planet": planet,
                "feature_count": count,
                "total_difference": total,
                "mean_difference": mean_difference,
                "difference_level": classify_difference(mean_difference),
            }
        )

    ranked = sorted(
        planet_rows,
        key=lambda row: row["mean_difference"],
        reverse=True,
    )

    return {
        "ranked_planets": ranked,
        "most_divergent_planet": ranked[0]["planet"] if ranked else None,
        "least_divergent_planet": ranked[-1]["planet"] if ranked else None,
    }


def infer_planet_from_feature(feature: str) -> str | None:
    """Infer planet name from flattened corpus feature."""
    planets = {
        "saturn": "Saturn",
        "jupiter": "Jupiter",
        "mars": "Mars",
        "sun": "Sun",
        "venus": "Venus",
        "mercury": "Mercury",
        "moon": "Moon",
    }

    for prefix, planet in planets.items():
        if feature.startswith(f"{prefix}_"):
            return planet

    return None


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
    most_different_features: list[dict[str, Any]],
) -> list[str]:
    """Build deterministic interpretation lines for a comparison."""
    lines: list[str] = []

    lines.append(
        (
            f"{profile_a} and {profile_b} have a structural similarity of "
            f"{similarity:.4f} with a standardized distance of "
            f"{distance:.4f} using the selected corpus metric."
        )
    )

    most_divergent_planet = planet_summary.get("most_divergent_planet")

    if most_divergent_planet:
        lines.append(
            f"The greatest planet-level divergence occurs within "
            f"{most_divergent_planet}."
        )

    if most_different_features:
        feature = most_different_features[0]

        lines.append(
            f"The single strongest distinguishing feature is "
            f"{feature['feature']} "
            f"(Δz = {feature['standardized_difference']:.4f})."
        )

    if len(most_different_features) >= 3:
        top_features = ", ".join(
            feature["feature"]
            for feature in most_different_features[:3]
        )

        lines.append(
            f"The three largest structural separators are: {top_features}."
        )

    return lines


def identity_comparison_to_dict(
    comparison: IdentityComparison,
) -> dict[str, Any]:
    """Convert identity comparison to dictionary."""
    return {
        "profile_a": comparison.profile_a,
        "profile_b": comparison.profile_b,
        "metric": comparison.metric,
        "similarity": comparison.similarity,
        "distance": comparison.distance,
        "feature_count": comparison.feature_count,
        "most_similar_features": comparison.most_similar_features,
        "most_different_features": comparison.most_different_features,
        "planet_summary": comparison.planet_summary,
        "interpretation_lines": comparison.interpretation_lines,
    }