
"""Performance attribution."""

from __future__ import annotations

import pandas as pd


def asset_attribution(portfolio: pd.DataFrame) -> list[dict]:
    if portfolio.empty:
        return []

    rows = []

    total_value = float(portfolio["paper_value"].sum()) if "paper_value" in portfolio.columns else 0.0

    for _, row in portfolio.iterrows():
        value = float(row.get("paper_value") or 0.0)
        rows.append({
            "asset": row.get("asset"),
            "side": row.get("side"),
            "weight": row.get("paper_weight"),
            "value": round(value, 2),
            "portfolio_share": round(value / total_value, 6) if total_value else 0.0,
            "cost_drag": row.get("cost_drag", 0.0),
        })

    return rows
