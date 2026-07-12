"""Longitudinal execution evidence storage."""

from __future__ import annotations

import pandas as pd

from atlas.investment.research_evidence_accumulator.identity import (
    text,
)


RUN_HISTORY_COLUMNS = [
    "run_id",
    "experiment_id",
    "research_program_id",
    "parent_engine_id",
    "run_status",
    "started_at",
    "completed_at",
    "observation_source_path",
    "baseline_observation_count",
    "declared_variant_count",
    "executed_variant_count",
    "fold_count",
    "uses_future_data",
    "overlapping_test_trades",
    "state_hash",
]


VARIANT_HISTORY_COLUMNS = [
    "run_id",
    "experiment_id",
    "research_program_id",
    "experiment_variant_id",
    "source_candidate_id",
    "gate_expression",
    "baseline_trade_count",
    "candidate_trade_count",
    "retention_ratio",
    "mean_return_advantage",
    "sharpe_advantage",
    "drawdown_improvement",
    "fold_count",
    "fold_win_rate",
    "acceptance_passed",
    "result_status",
]


def merge_run_history(
    existing: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    return merge_history(
        existing=existing,
        current=current,
        columns=RUN_HISTORY_COLUMNS,
        unique_columns=["run_id"],
    )


def merge_variant_history(
    existing: pd.DataFrame,
    current: pd.DataFrame,
) -> pd.DataFrame:
    return merge_history(
        existing=existing,
        current=current,
        columns=VARIANT_HISTORY_COLUMNS,
        unique_columns=[
            "run_id",
            "experiment_variant_id",
        ],
    )


def merge_history(
    *,
    existing: pd.DataFrame,
    current: pd.DataFrame,
    columns: list[str],
    unique_columns: list[str],
) -> pd.DataFrame:
    frames = []

    for frame in (
        existing,
        current,
    ):
        if frame is None or frame.empty:
            continue

        normalized = frame.copy()

        for column in columns:
            if column not in normalized.columns:
                normalized[column] = ""

        frames.append(
            normalized[columns]
        )

    if not frames:
        return pd.DataFrame(
            columns=columns
        )

    result = pd.concat(
        frames,
        ignore_index=True,
    )

    result = (
        result.drop_duplicates(
            subset=unique_columns,
            keep="last",
        )
        .reset_index(drop=True)
    )

    return result
