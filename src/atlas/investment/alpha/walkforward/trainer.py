
"""Walk-forward trainer."""

from __future__ import annotations

from typing import Any

import pandas as pd


def select_train_strategies(
    rankings: pd.DataFrame,
    trades: pd.DataFrame,
    split: dict,
    *,
    top_n: int = 5,
    min_train_trades: int = 30,
) -> list[dict[str, Any]]:
    """Select best strategies using only train window performance."""
    train_start = split["train_start"]
    train_end = split["train_end"]

    rows = []

    for hypothesis_id, group in trades.groupby("hypothesis_id"):
        chunk = group[(group["date"] >= train_start) & (group["date"] < train_end)]
        returns = pd.to_numeric(chunk["return"], errors="coerce").dropna()

        if len(returns) < min_train_trades:
            continue

        avg = float(returns.mean())
        win = float((returns > 0).mean())

        asset_counts = chunk["asset"].value_counts(dropna=False).to_dict() if "asset" in chunk.columns else {}
        total = sum(asset_counts.values())
        concentration = max(asset_counts.values()) / total if total else 1.0

        score = avg * 10 + win + min(len(returns) / 100, 1.0) - max(0.0, concentration - 0.7) * 2

        rows.append(
            {
                "hypothesis_id": hypothesis_id,
                "train_trade_count": int(len(returns)),
                "train_avg_return": round(avg, 8),
                "train_win_rate": round(win, 6),
                "train_asset_concentration": round(float(concentration), 6),
                "train_score": round(float(score), 6),
            }
        )

    rows = sorted(rows, key=lambda x: x["train_score"], reverse=True)
    return rows[:top_n]
