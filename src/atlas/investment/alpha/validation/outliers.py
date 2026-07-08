
"""Outlier robustness validation."""

from __future__ import annotations

from typing import Any

import pandas as pd


def outlier_validation(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {"success": False, "outlier_score": 0.0}

    s = pd.to_numeric(trades["return"], errors="coerce").dropna()
    if s.empty:
        return {"success": False, "outlier_score": 0.0}

    base_mean = float(s.mean())

    tests = {}
    scores = []

    for pct in [0.01, 0.05, 0.10]:
        cutoff = s.quantile(1 - pct)
        trimmed = s[s <= cutoff]
        trimmed_mean = float(trimmed.mean()) if not trimmed.empty else 0.0
        retained = trimmed_mean / base_mean if base_mean else 0.0

        tests[f"remove_top_{int(pct * 100)}pct"] = {
            "cutoff": round(float(cutoff), 8),
            "remaining_count": int(trimmed.count()),
            "trimmed_mean": round(trimmed_mean, 8),
            "mean_retention_ratio": round(float(retained), 6),
        }

        scores.append(max(0.0, min(1.0, retained)))

    return {
        "success": True,
        "base_mean": round(base_mean, 8),
        "tests": tests,
        "outlier_score": round(float(sum(scores) / len(scores)), 6) if scores else 0.0,
    }
