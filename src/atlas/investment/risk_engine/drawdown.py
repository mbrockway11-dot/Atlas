
"""MTM drawdown risk."""

from __future__ import annotations

import pandas as pd


def drawdown_risk(performance: dict, mtm_report: dict, equity_curve: pd.DataFrame) -> dict:
    pnl = performance.get("pnl", {}) or {}
    mtm = mtm_report.get("equity_snapshot", {}) or {}

    pnl_pct = float(pnl.get("pnl_pct") or mtm.get("pnl_pct") or 0.0)
    drawdown = float(pnl.get("drawdown") or mtm.get("drawdown") or 0.0)

    score = 0.0
    warnings = []

    if drawdown <= -0.20:
        score += 0.80
        warnings.append("MTM drawdown below -20%.")
    elif drawdown <= -0.10:
        score += 0.50
        warnings.append("MTM drawdown below -10%.")
    elif drawdown <= -0.05:
        score += 0.25
        warnings.append("MTM drawdown below -5%.")

    if pnl_pct <= -0.10:
        score += 0.50
        warnings.append("MTM PnL below -10%.")
    elif pnl_pct < 0:
        score += 0.10
        warnings.append("MTM PnL is negative.")

    equity_rows = int(len(equity_curve)) if equity_curve is not None else 0
    if equity_rows < 5:
        score += 0.05
        warnings.append("MTM equity curve has fewer than 5 rows.")

    return {
        "risk_type": "drawdown",
        "risk_score": round(min(score, 1.0), 6),
        "pnl_pct": round(pnl_pct, 6),
        "drawdown": round(drawdown, 6),
        "equity_curve_rows": equity_rows,
        "source": "performance_v3_mtm",
        "warnings": warnings,
    }
