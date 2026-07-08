
"""Alpha ensemble strategy weighting."""

from __future__ import annotations

import math
from typing import Any


def strategy_weight(strategy: dict[str, Any]) -> float:
    """Compute validated strategy weight."""
    confidence = strategy.get("confidence", {}) or {}
    validation = strategy.get("validation", {}) or {}
    robustness = validation.get("robustness", {}) or {}
    rolling = validation.get("rolling", {}) or {}

    alpha_conf = float(confidence.get("alpha_confidence") or 0.0)
    trade_count = float(robustness.get("trade_count") or 0.0)
    concentration = float(robustness.get("asset_concentration") or 1.0)
    rolling_stability = float(rolling.get("stability_score") or 0.0)

    sample = math.log1p(trade_count)
    diversity = max(0.0, 1.0 - concentration)

    return alpha_conf * sample * diversity * rolling_stability


def build_strategy_weights(strategies: list[dict[str, Any]]) -> dict[str, Any]:
    """Build normalized strategy weights."""
    raw = []

    for strategy in strategies:
        hypothesis_id = strategy.get("hypothesis_id")
        weight = strategy_weight(strategy)
        raw.append(
            {
                "hypothesis_id": hypothesis_id,
                "raw_weight": weight,
                "alpha_confidence": (strategy.get("confidence", {}) or {}).get("alpha_confidence"),
                "rolling_stability": ((strategy.get("validation", {}) or {}).get("rolling", {}) or {}).get("stability_score"),
                "asset_concentration": ((strategy.get("validation", {}) or {}).get("robustness", {}) or {}).get("asset_concentration"),
                "trade_count": ((strategy.get("validation", {}) or {}).get("robustness", {}) or {}).get("trade_count"),
            }
        )

    total = sum(item["raw_weight"] for item in raw)

    for item in raw:
        item["weight"] = item["raw_weight"] / total if total else 0.0

    return {
        "success": True,
        "strategy_count": len(strategies),
        "total_raw_weight": total,
        "weights": sorted(raw, key=lambda x: x["weight"], reverse=True),
    }
