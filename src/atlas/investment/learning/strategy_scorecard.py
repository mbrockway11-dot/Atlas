
"""Learning v2 strategy/asset scorecard."""

from __future__ import annotations

import pandas as pd


def build_strategy_scorecard(attribution: pd.DataFrame, ledger: pd.DataFrame) -> list[dict]:
    if attribution.empty:
        return []

    df = attribution.copy()

    rows = []

    for asset, group in df.groupby("asset"):
        pnl = pd.to_numeric(group.get("unrealized_pnl", 0.0), errors="coerce").fillna(0.0)
        pnl_pct = pd.to_numeric(group.get("unrealized_pnl_pct", 0.0), errors="coerce").fillna(0.0)

        trade_count = 0
        if ledger is not None and not ledger.empty and "asset" in ledger.columns:
            trade_count = int((ledger["asset"] == asset).sum())

        avg_pnl = float(pnl.mean()) if len(pnl) else 0.0
        avg_pnl_pct = float(pnl_pct.mean()) if len(pnl_pct) else 0.0

        raw_score = 0.50 + avg_pnl_pct
        score = max(0.0, min(1.0, raw_score))

        rows.append({
            "asset": asset,
            "paper_trade_count": trade_count,
            "avg_unrealized_pnl": round(avg_pnl, 6),
            "avg_unrealized_pnl_pct": round(avg_pnl_pct, 6),
            "score": round(score, 6),
            "status": label_score(score),
        })

    return rows


def label_score(score: float) -> str:
    if score >= 0.65:
        return "outperforming"
    if score <= 0.35:
        return "underperforming"
    return "neutral"
