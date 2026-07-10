
"""Walk-forward evaluator."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.alpha.walkforward.metrics import non_overlapping_trades, summarize_returns


def evaluate_split(
    selected: list[dict[str, Any]],
    trades: pd.DataFrame,
    split: dict[str, Any],
    *,
    exposure: float = 0.10,
    drawdown_control: bool = False,
) -> dict[str, Any]:
    """Evaluate selected strategies on train and unseen test windows."""
    ids = [row["hypothesis_id"] for row in selected]

    train = trades[
        (trades["hypothesis_id"].isin(ids))
        & (trades["date"] >= split["train_start"])
        & (trades["date"] < split["train_end"])
    ].copy()

    test = trades[
        (trades["hypothesis_id"].isin(ids))
        & (trades["date"] >= split["test_start"])
        & (trades["date"] < split["test_end"])
    ].copy()

    train_non = non_overlapping_trades(train)
    test_non = non_overlapping_trades(test)

    return {
        "split_id": split["split_id"],
        "train_start": str(split["train_start"]),
        "train_end": str(split["train_end"]),
        "test_start": str(split["test_start"]),
        "test_end": str(split["test_end"]),
        "selected": selected,
        "raw_train_count": int(len(train)),
        "raw_test_count": int(len(test)),
        "non_overlap_train_count": int(len(train_non)),
        "non_overlap_test_count": int(len(test_non)),
        "train": summarize_returns(
            train_non["return"] if "return" in train_non.columns else pd.Series(dtype=float),
            exposure=exposure,
            drawdown_control=drawdown_control,
        ),
        "test": summarize_returns(
            test_non["return"] if "return" in test_non.columns else pd.Series(dtype=float),
            exposure=exposure,
            drawdown_control=drawdown_control,
        ),
    }
