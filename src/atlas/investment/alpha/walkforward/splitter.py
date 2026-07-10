
"""Walk-forward time splitters."""

from __future__ import annotations

import pandas as pd


def build_walkforward_splits(
    dates: pd.Series,
    *,
    train_days: int = 730,
    test_days: int = 180,
    step_days: int = 180,
) -> list[dict]:
    """Build rolling train/test windows."""
    d = pd.to_datetime(dates, errors="coerce").dropna().sort_values()

    if d.empty:
        return []

    start = d.min()
    end = d.max()
    splits = []

    train_start = start

    while True:
        train_end = train_start + pd.Timedelta(days=train_days)
        test_end = train_end + pd.Timedelta(days=test_days)

        if test_end > end:
            break

        splits.append(
            {
                "split_id": f"wf_{len(splits) + 1:03d}",
                "train_start": train_start,
                "train_end": train_end,
                "test_start": train_end,
                "test_end": test_end,
            }
        )

        train_start = train_start + pd.Timedelta(days=step_days)

    return splits
