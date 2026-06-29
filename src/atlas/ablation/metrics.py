"""Ablation impact metrics."""

from __future__ import annotations

import pandas as pd


def compute_rank_shift(
    baseline: pd.DataFrame,
    ablated: pd.DataFrame,
) -> dict:
    """Compute ranking shift between baseline and ablated nearest-neighbor lists."""
    baseline_ranks = {
        row["name"]: index
        for index, row in enumerate(
            baseline.to_dict("records"),
            start=1,
        )
    }

    ablated_ranks = {
        row["name"]: index
        for index, row in enumerate(
            ablated.to_dict("records"),
            start=1,
        )
    }

    common_names = sorted(
        set(baseline_ranks)
        & set(ablated_ranks)
    )

    shifts = []

    for name in common_names:
        baseline_rank = baseline_ranks[name]
        ablated_rank = ablated_ranks[name]
        shift = abs(baseline_rank - ablated_rank)

        shifts.append(
            {
                "name": name,
                "baseline_rank": baseline_rank,
                "ablated_rank": ablated_rank,
                "rank_shift": shift,
            }
        )

    if not shifts:
        return {
            "mean_rank_shift": 0.0,
            "max_rank_shift": 0,
            "changed_profiles": 0,
            "rank_shifts": [],
        }

    return {
        "mean_rank_shift": sum(row["rank_shift"] for row in shifts) / len(shifts),
        "max_rank_shift": max(row["rank_shift"] for row in shifts),
        "changed_profiles": sum(1 for row in shifts if row["rank_shift"] > 0),
        "rank_shifts": sorted(
            shifts,
            key=lambda row: row["rank_shift"],
            reverse=True,
        ),
    }


def compute_similarity_delta(
    baseline: pd.DataFrame,
    ablated: pd.DataFrame,
) -> dict:
    """Compute similarity changes for common profiles."""
    baseline_scores = {
        row["name"]: float(row["similarity"])
        for row in baseline.to_dict("records")
    }

    ablated_scores = {
        row["name"]: float(row["similarity"])
        for row in ablated.to_dict("records")
    }

    common_names = sorted(
        set(baseline_scores)
        & set(ablated_scores)
    )

    deltas = []

    for name in common_names:
        baseline_similarity = baseline_scores[name]
        ablated_similarity = ablated_scores[name]
        delta = ablated_similarity - baseline_similarity

        deltas.append(
            {
                "name": name,
                "baseline_similarity": baseline_similarity,
                "ablated_similarity": ablated_similarity,
                "similarity_delta": delta,
                "absolute_similarity_delta": abs(delta),
            }
        )

    if not deltas:
        return {
            "mean_absolute_similarity_delta": 0.0,
            "max_absolute_similarity_delta": 0.0,
            "similarity_deltas": [],
        }

    return {
        "mean_absolute_similarity_delta": (
            sum(row["absolute_similarity_delta"] for row in deltas) / len(deltas)
        ),
        "max_absolute_similarity_delta": max(
            row["absolute_similarity_delta"]
            for row in deltas
        ),
        "similarity_deltas": sorted(
            deltas,
            key=lambda row: row["absolute_similarity_delta"],
            reverse=True,
        ),
    }