
"""Alpha strategy promotion rules."""

from __future__ import annotations

from typing import Any


MIN_CONFIDENCE = 0.75
MIN_ROLLING_STABILITY = 0.65
MAX_ASSET_CONCENTRATION = 0.70
MIN_NON_OVERLAP_TRADES = 100


def promote_alpha_strategies(validations: list[dict[str, Any]]) -> dict[str, Any]:
    """Promote only robust alpha strategies."""
    promoted = []
    rejected = []

    for item in validations:
        confidence = item.get("confidence", {}) or {}
        validation = item.get("validation", {}) or {}
        robust = validation.get("robustness", {}) or {}
        rolling = validation.get("rolling", {}) or {}
        regime = validation.get("regime", {}) or {}
        metrics = item.get("metrics", {}) or {}

        checks = {
            "confidence": confidence.get("alpha_confidence", 0) >= MIN_CONFIDENCE,
            "rolling_stability": rolling.get("stability_score", 0) >= MIN_ROLLING_STABILITY,
            "non_overlap_trades": robust.get("trade_count", 0) >= MIN_NON_OVERLAP_TRADES,
            "asset_concentration": robust.get("asset_concentration", 1.0) <= MAX_ASSET_CONCENTRATION,
            "positive_expectancy": (
                metrics.get("non_overlap_avg_return")
                or metrics.get("avg_return")
                or 0
            ) > 0,
            "regime_positive": regime_positive(regime),
        }

        item["promotion_checks"] = checks
        item["promoted"] = all(checks.values())

        if item["promoted"]:
            promoted.append(item)
        else:
            rejected.append(item)

    return {
        "success": True,
        "criteria": {
            "min_confidence": MIN_CONFIDENCE,
            "min_rolling_stability": MIN_ROLLING_STABILITY,
            "max_asset_concentration": MAX_ASSET_CONCENTRATION,
            "min_non_overlap_trades": MIN_NON_OVERLAP_TRADES,
            "requires_positive_expectancy": True,
            "requires_positive_core_regimes": True,
        },
        "promoted_count": len(promoted),
        "rejected_count": len(rejected),
        "promoted": promoted,
        "rejected": rejected,
        "summary": f"Promoted {len(promoted)} alpha strategy/strategies. Rejected {len(rejected)}.",
    }


def regime_positive(regime: dict[str, Any]) -> bool:
    """Require positive results in available core regimes."""
    regimes = regime.get("regimes", {}) or {}

    trend = regimes.get("trend_regime", {}) or {}
    vol = regimes.get("volatility_regime", {}) or {}

    required = []

    for key in ["bull", "sideways"]:
        if key in trend:
            required.append(trend[key].get("avg_return", 0) > 0)

    for key in ["high_volatility", "low_volatility"]:
        if key in vol:
            required.append(vol[key].get("avg_return", 0) > 0)

    if not required:
        return False

    return all(required)
