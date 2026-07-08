
"""Alpha strategy validator."""

from __future__ import annotations

from typing import Any

import pandas as pd

from atlas.investment.alpha.validation.confidence import build_alpha_confidence
from atlas.investment.alpha.validation.outliers import outlier_validation
from atlas.investment.alpha.validation.regime import regime_validation
from atlas.investment.alpha.validation.robustness import robustness_validation
from atlas.investment.alpha.validation.rolling import rolling_window_validation


def validate_strategy(hypothesis_id: str, trades: pd.DataFrame, metrics: dict[str, Any] | None = None) -> dict[str, Any]:
    validation = {
        "rolling": rolling_window_validation(trades),
        "regime": regime_validation(trades),
        "outliers": outlier_validation(trades),
        "robustness": robustness_validation(trades),
    }

    confidence = build_alpha_confidence(validation)

    return {
        "success": True,
        "hypothesis_id": hypothesis_id,
        "metrics": metrics or {},
        "validation": validation,
        "confidence": confidence,
    }


def validate_alpha_strategies(trades: pd.DataFrame, rankings: pd.DataFrame, *, top_n: int = 25) -> list[dict[str, Any]]:
    if trades.empty or rankings.empty:
        return []

    rankings = rankings.sort_values("alpha_score", ascending=False).head(top_n)
    results = []

    for _, row in rankings.iterrows():
        hypothesis_id = row["hypothesis_id"]
        subset = trades[trades["hypothesis_id"] == hypothesis_id].copy()

        metrics = {
            key: row[key]
            for key in rankings.columns
            if key not in {"conditions", "asset_counts"}
        }

        results.append(validate_strategy(hypothesis_id, subset, metrics))

    return results
