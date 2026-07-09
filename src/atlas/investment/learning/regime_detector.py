
"""Learning v2 regime detector."""

from __future__ import annotations

import pandas as pd


def detect_learning_regime(equity_curve: pd.DataFrame, snapshots: pd.DataFrame) -> dict:
    df = equity_curve.copy() if not equity_curve.empty else snapshots.copy()

    if df.empty or len(df) < 2:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.0,
            "source": "mtm_equity_curve",
        }

    equity_col = "equity" if "equity" in df.columns else "current_equity"

    if equity_col not in df.columns:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.0,
            "source": "mtm_equity_curve",
        }

    df[equity_col] = pd.to_numeric(df[equity_col], errors="coerce")
    df = df.dropna(subset=[equity_col])

    if len(df) < 2:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.0,
            "source": "mtm_equity_curve",
        }

    first = float(df[equity_col].iloc[0])
    last = float(df[equity_col].iloc[-1])
    change = (last - first) / first if first else 0.0

    recent = df[equity_col].tail(min(5, len(df)))
    volatility = float(recent.pct_change().dropna().std() or 0.0)

    if change > 0.02:
        regime = "improving"
    elif change < -0.02:
        regime = "deteriorating"
    else:
        regime = "flat"

    confidence = min(abs(change) * 10 + max(0.0, 0.05 - volatility), 1.0)

    return {
        "learning_regime": regime,
        "trend": "up" if change > 0 else "down" if change < 0 else "flat",
        "equity_change_pct": round(float(change), 6),
        "recent_volatility": round(float(volatility), 6),
        "confidence": round(float(confidence), 6),
        "source": "mtm_equity_curve",
    }
