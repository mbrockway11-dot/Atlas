
"""Learning regime detector."""

from __future__ import annotations

import pandas as pd


def detect_learning_regime(snapshots: pd.DataFrame) -> dict:
    if snapshots.empty or len(snapshots) < 2:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.0,
        }

    df = snapshots.copy()
    df["current_equity"] = pd.to_numeric(df["current_equity"], errors="coerce")
    df = df.dropna(subset=["current_equity"])

    if len(df) < 2:
        return {
            "learning_regime": "insufficient_history",
            "trend": "unknown",
            "confidence": 0.0,
        }

    first = float(df["current_equity"].iloc[0])
    last = float(df["current_equity"].iloc[-1])
    change = (last - first) / first if first else 0.0

    if change > 0.02:
        regime = "improving"
    elif change < -0.02:
        regime = "deteriorating"
    else:
        regime = "flat"

    return {
        "learning_regime": regime,
        "trend": "up" if change > 0 else "down" if change < 0 else "flat",
        "equity_change_pct": round(float(change), 6),
        "confidence": min(round(abs(float(change)) * 10, 6), 1.0),
    }
