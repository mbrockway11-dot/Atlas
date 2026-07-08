
"""General robustness checks."""

from __future__ import annotations

from typing import Any

import pandas as pd


def robustness_validation(trades: pd.DataFrame) -> dict[str, Any]:
    if trades.empty:
        return {"success": False, "robustness_score": 0.0}

    asset_counts = trades["asset"].value_counts(dropna=False).to_dict() if "asset" in trades.columns else {}
    total = sum(asset_counts.values())
    concentration = max(asset_counts.values()) / total if total else 1.0

    s = pd.to_numeric(trades["return"], errors="coerce").dropna()
    win_rate = float((s > 0).mean()) if not s.empty else 0.0
    avg_return = float(s.mean()) if not s.empty else 0.0
    sample_score = min(len(s) / 100, 1.0)
    concentration_score = max(0.0, 1.0 - max(0.0, concentration - 0.5) * 2)

    robustness_score = (
        sample_score * 0.35
        + concentration_score * 0.25
        + min(max(win_rate, 0.0), 1.0) * 0.20
        + (1.0 if avg_return > 0 else 0.0) * 0.20
    )

    return {
        "success": True,
        "trade_count": int(len(s)),
        "asset_counts": {str(k): int(v) for k, v in asset_counts.items()},
        "asset_concentration": round(float(concentration), 6),
        "sample_score": round(float(sample_score), 6),
        "concentration_score": round(float(concentration_score), 6),
        "robustness_score": round(float(robustness_score), 6),
    }
