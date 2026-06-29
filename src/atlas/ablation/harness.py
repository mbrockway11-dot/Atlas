"""Ablation experiment harness."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from atlas.ablation.experiments import AblationExperiment
from atlas.ablation.metrics import (
    compute_rank_shift,
    compute_similarity_delta,
)
from atlas.corpus.similarity import (
    SimilarityMetric,
    find_nearest_profiles,
)


@dataclass(frozen=True)
class AblationResult:
    """Result of one ablation experiment."""

    experiment: AblationExperiment
    reference_profile: str
    metric: str
    removed_columns: list[str]
    remaining_feature_count: int
    baseline_results: list[dict[str, Any]]
    ablated_results: list[dict[str, Any]]
    rank_shift: dict[str, Any]
    similarity_delta: dict[str, Any]
    summary: dict[str, Any]


def run_ablation_experiment(
    dataframe: pd.DataFrame,
    reference_profile: str,
    experiment: AblationExperiment,
    metric: SimilarityMetric = "euclidean",
    top_n: int = 10,
    min_std: float = 0.005,
) -> AblationResult:
    """Run one ablation experiment against a corpus dataframe."""
    baseline = find_nearest_profiles(
        dataframe=dataframe,
        profile_name=reference_profile,
        top_n=top_n,
        metric=metric,
        min_std=min_std,
    )

    ablated_dataframe, removed_columns = apply_ablation(
        dataframe=dataframe,
        experiment=experiment,
    )

    ablated = find_nearest_profiles(
        dataframe=ablated_dataframe,
        profile_name=reference_profile,
        top_n=top_n,
        metric=metric,
        min_std=min_std,
    )

    rank_shift = compute_rank_shift(
        baseline=baseline,
        ablated=ablated,
    )
    similarity_delta = compute_similarity_delta(
        baseline=baseline,
        ablated=ablated,
    )

    remaining_feature_count = (
        int(ablated["feature_count"].iloc[0])
        if not ablated.empty and "feature_count" in ablated.columns
        else 0
    )

    summary = {
        "experiment_name": experiment.name,
        "reference_profile": reference_profile,
        "metric": metric,
        "removed_column_count": len(removed_columns),
        "remaining_feature_count": remaining_feature_count,
        "mean_rank_shift": rank_shift["mean_rank_shift"],
        "max_rank_shift": rank_shift["max_rank_shift"],
        "changed_profiles": rank_shift["changed_profiles"],
        "mean_absolute_similarity_delta": similarity_delta[
            "mean_absolute_similarity_delta"
        ],
        "max_absolute_similarity_delta": similarity_delta[
            "max_absolute_similarity_delta"
        ],
    }

    return AblationResult(
        experiment=experiment,
        reference_profile=reference_profile,
        metric=metric,
        removed_columns=removed_columns,
        remaining_feature_count=remaining_feature_count,
        baseline_results=baseline.to_dict("records"),
        ablated_results=ablated.to_dict("records"),
        rank_shift=rank_shift,
        similarity_delta=similarity_delta,
        summary=summary,
    )


def apply_ablation(
    dataframe: pd.DataFrame,
    experiment: AblationExperiment,
) -> tuple[pd.DataFrame, list[str]]:
    """Remove columns from dataframe according to ablation experiment."""
    removed_columns = columns_for_experiment(
        dataframe=dataframe,
        experiment=experiment,
    )

    if not removed_columns:
        return dataframe.copy(), []

    return (
        dataframe.drop(columns=removed_columns),
        removed_columns,
    )


def columns_for_experiment(
    dataframe: pd.DataFrame,
    experiment: AblationExperiment,
) -> list[str]:
    """Find dataframe columns targeted by an experiment."""
    columns = []

    for column in dataframe.columns:
        if column in experiment.remove_columns:
            columns.append(column)
            continue

        if any(column.startswith(prefix) for prefix in experiment.remove_prefixes):
            columns.append(column)
            continue

        if any(column.endswith(suffix) for suffix in experiment.remove_suffixes):
            columns.append(column)
            continue

        if any(token in column for token in experiment.remove_contains):
            columns.append(column)
            continue

    protected = {
        "name",
        "identity_vector_version",
        "normalization_mode",
    }

    return [
        column
        for column in columns
        if column not in protected
    ]


def ablation_result_to_dict(
    result: AblationResult,
) -> dict[str, Any]:
    """Convert ablation result to JSON-safe dictionary."""
    return {
        "experiment": {
            "name": result.experiment.name,
            "description": result.experiment.description,
            "remove_prefixes": list(result.experiment.remove_prefixes),
            "remove_suffixes": list(result.experiment.remove_suffixes),
            "remove_contains": list(result.experiment.remove_contains),
            "remove_columns": list(result.experiment.remove_columns),
        },
        "reference_profile": result.reference_profile,
        "metric": result.metric,
        "removed_columns": result.removed_columns,
        "remaining_feature_count": result.remaining_feature_count,
        "baseline_results": result.baseline_results,
        "ablated_results": result.ablated_results,
        "rank_shift": result.rank_shift,
        "similarity_delta": result.similarity_delta,
        "summary": result.summary,
    }