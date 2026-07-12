"""Atlas Research Scheduler run-history utilities."""

from __future__ import annotations

import pandas as pd


RUN_HISTORY_COLUMNS = [
    "scheduler_run_id",
    "generated_at",
    "state_hash",
    "total_jobs",
    "current_jobs",
    "ready_jobs",
    "blocked_jobs",
    "failed_jobs",
    "missing_jobs",
    "stale_jobs",
    "success",
]


def append_run_history(
    *,
    existing: pd.DataFrame,
    row: dict,
) -> pd.DataFrame:
    """Append one immutable scheduler evaluation."""
    frame = pd.concat(
        [
            existing
            if existing is not None
            else pd.DataFrame(),
            pd.DataFrame([
                row
            ]),
        ],
        ignore_index=True,
    )

    for column in RUN_HISTORY_COLUMNS:
        if column not in frame.columns:
            frame[column] = ""

    return frame[
        RUN_HISTORY_COLUMNS
    ].drop_duplicates(
        subset=["scheduler_run_id"],
        keep="first",
    ).reset_index(drop=True)
