
"""Portfolio risk summary."""

from __future__ import annotations

import pandas as pd


def summarize_portfolio_risk(portfolio: pd.DataFrame) -> dict:
    if portfolio.empty:
        return {
            "success": False,
            "error": "No portfolio rows.",
        }

    risky = portfolio[portfolio["asset"] != "CASH"]
    cash = portfolio[portfolio["asset"] == "CASH"]

    total_risky = float(risky["target_weight"].sum()) if not risky.empty else 0.0
    cash_weight = float(cash["target_weight"].sum()) if not cash.empty else 0.0
    max_asset = float(risky["target_weight"].max()) if not risky.empty else 0.0
    asset_count = int(len(risky))

    diversification_score = min(asset_count / 5, 1.0) * (1.0 - max(0.0, max_asset - 0.25))

    return {
        "success": True,
        "asset_count": asset_count,
        "total_risky_weight": round(total_risky, 6),
        "cash_weight": round(cash_weight, 6),
        "max_asset_weight": round(max_asset, 6),
        "diversification_score": round(float(diversification_score), 6),
        "risk_label": risk_label(total_risky, max_asset),
    }


def risk_label(total_risky: float, max_asset: float) -> str:
    if total_risky <= 0.50:
        return "conservative"
    if total_risky <= 0.75 and max_asset <= 0.35:
        return "balanced"
    return "aggressive"
