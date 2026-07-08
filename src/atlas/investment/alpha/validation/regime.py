
"""Regime validation."""

from __future__ import annotations

from typing import Any

import pandas as pd


def regime_validation(trades: pd.DataFrame, regime_report: dict[str, Any] | None = None) -> dict[str, Any]:
    if trades.empty:
        return {"success": False, "regimes": {}, "regime_score": 0.0}

    # v1 uses trade fields if regime labels exist. Otherwise it returns neutral pending richer joins.
    labels = [c for c in ["trend_regime", "volatility_regime", "drawdown_regime"] if c in trades.columns]

    if not labels:
        return {
            "success": True,
            "regimes": {},
            "regime_score": 0.5,
            "note": "No regime labels on trade rows; neutral regime score assigned.",
        }

    out = {}
    scores = []

    for label in labels:
        out[label] = {}
        for key, group in trades.groupby(label, dropna=False):
            s = pd.to_numeric(group["return"], errors="coerce").dropna()
            if s.empty:
                continue
            summary = {
                "count": int(s.count()),
                "win_rate": round(float((s > 0).mean()), 6),
                "avg_return": round(float(s.mean()), 8),
                "median_return": round(float(s.median()), 8),
            }
            out[label][str(key)] = summary
            if summary["count"] >= 3:
                scores.append(1.0 if summary["avg_return"] > 0 else 0.0)

    score = sum(scores) / len(scores) if scores else 0.5

    return {
        "success": True,
        "regimes": out,
        "regime_score": round(float(score), 6),
    }
