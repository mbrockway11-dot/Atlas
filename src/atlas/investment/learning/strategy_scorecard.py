
"""Strategy scorecard."""

from __future__ import annotations

import pandas as pd


def build_strategy_scorecard(ledger: pd.DataFrame) -> list[dict]:
    if ledger.empty:
        return []

    rows = []

    group_col = "asset" if "asset" in ledger.columns else None
    if group_col is None:
        return []

    for asset, group in ledger.groupby(group_col):
        cost = pd.to_numeric(group.get("total_cost_drag", 0.0), errors="coerce").fillna(0.0)

        rows.append({
            "asset": asset,
            "paper_trade_count": int(len(group)),
            "total_cost_drag": round(float(cost.sum()), 8),
            "avg_cost_drag": round(float(cost.mean()), 8) if len(cost) else 0.0,
            "score": round(float(max(0.0, 1.0 - cost.sum() * 100)), 6),
        })

    return rows
