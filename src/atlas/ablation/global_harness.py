"""Corpus-wide ablation harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from atlas.ablation.experiments import AblationExperiment, all_default_experiments
from atlas.ablation.harness import (
    AblationResult,
    run_ablation_experiment,
)
from atlas.corpus.similarity import SimilarityMetric


@dataclass(frozen=True)
class GlobalAblationResult:
    """Corpus-wide result for one ablation experiment."""

    experiment: AblationExperiment
    metric: str
    profile_count: int
    profile_results: list[AblationResult]
    summary: dict[str, Any]


def run_global_ablation_experiment(
    dataframe: pd.DataFrame,
    experiment: AblationExperiment,
    metric: SimilarityMetric = "euclidean",
    top_n: int = 10,
    min_std: float = 0.005,
) -> GlobalAblationResult:
    """Run one ablation experiment across every profile in the corpus."""
    profile_names = sorted(dataframe["name"].tolist())

    profile_results = [
        run_ablation_experiment(
            dataframe=dataframe,
            reference_profile=name,
            experiment=experiment,
            metric=metric,
            top_n=top_n,
            min_std=min_std,
        )
        for name in profile_names
    ]

    summary = summarize_profile_results(
        experiment=experiment,
        metric=metric,
        profile_results=profile_results,
    )

    return GlobalAblationResult(
        experiment=experiment,
        metric=metric,
        profile_count=len(profile_names),
        profile_results=profile_results,
        summary=summary,
    )


def run_default_global_ablation(
    dataframe: pd.DataFrame,
    metric: SimilarityMetric = "euclidean",
    top_n: int = 10,
    min_std: float = 0.005,
) -> list[GlobalAblationResult]:
    """Run all default ablation experiments across the corpus."""
    return [
        run_global_ablation_experiment(
            dataframe=dataframe,
            experiment=experiment,
            metric=metric,
            top_n=top_n,
            min_std=min_std,
        )
        for experiment in all_default_experiments()
    ]


def summarize_profile_results(
    *,
    experiment: AblationExperiment,
    metric: str,
    profile_results: list[AblationResult],
) -> dict[str, Any]:
    """Summarize one experiment across all profile runs."""
    if not profile_results:
        return {
            "experiment_name": experiment.name,
            "metric": metric,
            "profile_count": 0,
            "mean_rank_shift": 0.0,
            "mean_max_rank_shift": 0.0,
            "mean_changed_profiles": 0.0,
            "mean_absolute_similarity_delta": 0.0,
            "max_absolute_similarity_delta": 0.0,
            "mean_removed_column_count": 0.0,
            "mean_remaining_feature_count": 0.0,
            "importance_score": 0.0,
        }

    summaries = [
        result.summary
        for result in profile_results
    ]

    mean_rank_shift = mean(
        row["mean_rank_shift"]
        for row in summaries
    )
    mean_max_rank_shift = mean(
        row["max_rank_shift"]
        for row in summaries
    )
    mean_changed_profiles = mean(
        row["changed_profiles"]
        for row in summaries
    )
    mean_absolute_similarity_delta = mean(
        row["mean_absolute_similarity_delta"]
        for row in summaries
    )
    max_absolute_similarity_delta = max(
        row["max_absolute_similarity_delta"]
        for row in summaries
    )
    mean_removed_column_count = mean(
        row["removed_column_count"]
        for row in summaries
    )
    mean_remaining_feature_count = mean(
        row["remaining_feature_count"]
        for row in summaries
    )

    importance_score = (
        mean_rank_shift
        + mean_changed_profiles
        + (mean_absolute_similarity_delta * 100.0)
    ) / 3.0

    return {
        "experiment_name": experiment.name,
        "description": experiment.description,
        "metric": metric,
        "profile_count": len(profile_results),
        "mean_rank_shift": mean_rank_shift,
        "mean_max_rank_shift": mean_max_rank_shift,
        "mean_changed_profiles": mean_changed_profiles,
        "mean_absolute_similarity_delta": mean_absolute_similarity_delta,
        "max_absolute_similarity_delta": max_absolute_similarity_delta,
        "mean_removed_column_count": mean_removed_column_count,
        "mean_remaining_feature_count": mean_remaining_feature_count,
        "importance_score": importance_score,
    }


def mean(values) -> float:
    """Mean helper."""
    values = list(values)

    if not values:
        return 0.0

    return float(sum(values) / len(values))


def global_ablation_result_to_dict(
    result: GlobalAblationResult,
) -> dict[str, Any]:
    """Convert global ablation result to dictionary."""
    return {
        "experiment": {
            "name": result.experiment.name,
            "description": result.experiment.description,
            "remove_prefixes": list(result.experiment.remove_prefixes),
            "remove_suffixes": list(result.experiment.remove_suffixes),
            "remove_contains": list(result.experiment.remove_contains),
            "remove_columns": list(result.experiment.remove_columns),
        },
        "metric": result.metric,
        "profile_count": result.profile_count,
        "summary": result.summary,
        "profile_results": [
            profile_result.summary
            for profile_result in result.profile_results
        ],
    }