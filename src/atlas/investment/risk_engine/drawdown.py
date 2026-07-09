
"""Drawdown and PnL risk."""

from __future__ import annotations


def drawdown_risk(performance: dict) -> dict:
    pnl = performance.get("pnl", {}) or {}
    pnl_pct = float(pnl.get("pnl_pct") or 0.0)

    score = 0.0
    warnings = []

    if pnl_pct <= -0.10:
        score = 0.80
        warnings.append("Paper PnL below -10%.")
    elif pnl_pct <= -0.05:
        score = 0.50
        warnings.append("Paper PnL below -5%.")
    elif pnl_pct < 0:
        score = 0.10
        warnings.append("Paper PnL is slightly negative.")

    return {
        "risk_type": "drawdown",
        "risk_score": round(score, 6),
        "pnl_pct": round(pnl_pct, 6),
        "warnings": warnings,
    }
