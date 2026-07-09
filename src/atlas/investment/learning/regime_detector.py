
"""Learning Engine v3 regime detection."""

from __future__ import annotations

import pandas as pd


def detect_learning_regime(performance: dict, equity_curve: pd.DataFrame) -> dict:
    equity_metrics = performance.get("equity_metrics", {}) or {}

    pnl_pct = float(equity_metrics.get("pnl_pct") or 0.0)
    sharpe = float(equity_metrics.get("sharpe") or 0.0)
    max_dd = float(equity_metrics.get("max_drawdown") or 0.0)
    obs = int(equity_metrics.get("return_observations") or 0)

    if obs < 5:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.05,
            "reason": "Not enough MTM equity observations for statistical learning.",
            "source": "performance_v3",
        }

    if pnl_pct > 0 and sharpe > 0.5 and max_dd > -0.05:
        regime = "improving"
        trend = "positive"
        confidence = min(0.95, 0.50 + abs(sharpe) * 0.10)
    elif pnl_pct < 0 or max_dd <= -0.10:
        regime = "deteriorating"
        trend = "negative"
        confidence = min(0.95, 0.50 + abs(max_dd) * 3.0)
    else:
        regime = "flat"
        trend = "flat"
        confidence = 0.25

    return {
        "learning_regime": regime,
        "trend": trend,
        "confidence": round(confidence, 6),
        "pnl_pct": pnl_pct,
        "sharpe": sharpe,
        "max_drawdown": max_dd,
        "return_observations": obs,
        "source": "performance_v3",
    }
