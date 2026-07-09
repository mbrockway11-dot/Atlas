
"""Learning Engine v3 scorecards."""

from __future__ import annotations

import pandas as pd


def build_asset_scorecard(attribution: pd.DataFrame, fills: pd.DataFrame) -> list[dict]:
    rows = []

    assets = set()

    if attribution is not None and not attribution.empty and "asset" in attribution.columns:
        assets |= set(attribution["asset"].astype(str).tolist())

    if fills is not None and not fills.empty and "asset" in fills.columns:
        assets |= set(fills["asset"].astype(str).tolist())

    for asset in sorted(a for a in assets if a and a != "nan"):
        attr = attribution[attribution["asset"].astype(str) == asset] if attribution is not None and not attribution.empty and "asset" in attribution.columns else pd.DataFrame()
        f = fills[fills["asset"].astype(str) == asset] if fills is not None and not fills.empty and "asset" in fills.columns else pd.DataFrame()

        market_value = safe_float(attr["market_value"].sum()) if not attr.empty and "market_value" in attr.columns else 0.0
        pnl = safe_float(attr["unrealized_pnl"].sum()) if not attr.empty and "unrealized_pnl" in attr.columns else 0.0
        trade_count = int(len(f))

        score = 0.50
        if market_value > 0:
            score += 0.10
        if pnl > 0:
            score += 0.20
        elif pnl < 0:
            score -= 0.20
        if trade_count > 0:
            score += 0.05

        score = max(0.0, min(1.0, score))

        rows.append({
            "asset": asset,
            "trade_count": trade_count,
            "market_value": round(market_value, 2),
            "unrealized_pnl": round(pnl, 2),
            "asset_confidence": round(score, 6),
            "recommendation": recommendation_from_score(score),
        })

    return rows


def recommendation_from_score(score: float) -> str:
    if score >= 0.75:
        return "promote"
    if score <= 0.35:
        return "reduce"
    return "maintain"


def safe_float(value) -> float:
    try:
        return float(value)
    except Exception:
        return 0.0
