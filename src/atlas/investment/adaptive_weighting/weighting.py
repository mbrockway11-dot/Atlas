
"""Adaptive Weighting v3 weighting logic."""

from __future__ import annotations

import pandas as pd


DEFAULT_WEIGHTS = {
    "BTC-USD": 0.377631,
    "ETH-USD": 0.322369,
    "SOL-USD": 0.0,
}


def base_weights(alpha_portfolio: pd.DataFrame) -> dict[str, float]:
    if alpha_portfolio is None or alpha_portfolio.empty:
        return dict(DEFAULT_WEIGHTS)

    asset_col = "asset" if "asset" in alpha_portfolio.columns else None

    weight_col = None
    for candidate in ["target_weight", "paper_weight", "weight", "allocation", "target_exposure"]:
        if candidate in alpha_portfolio.columns:
            weight_col = candidate
            break

    if not asset_col or not weight_col:
        return dict(DEFAULT_WEIGHTS)

    out = {}
    for _, row in alpha_portfolio.iterrows():
        asset = str(row.get(asset_col))
        if asset == "CASH":
            continue
        out[asset] = max(0.0, float(row.get(weight_col) or 0.0))

    return out if out else dict(DEFAULT_WEIGHTS)


def registry_multipliers(registry: pd.DataFrame) -> dict[str, float]:
    if registry is None or registry.empty:
        return {}

    out = {}

    for _, row in registry.iterrows():
        asset = str(row.get("asset"))
        multiplier = float(row.get("weight_multiplier") or 1.0)
        confidence = float(row.get("asset_confidence") or 0.5)

        confidence_adjustment = 0.75 + (confidence * 0.50)
        out[asset] = round(multiplier * confidence_adjustment, 6)

    return out


def regime_multiplier(learning: dict, performance: dict) -> float:
    regime = (learning.get("learning_regime", {}) or {}).get("learning_regime", "unknown")
    confidence = float(learning.get("learning_confidence") or 0.0)

    pnl = ((performance.get("pnl", {}) or {}).get("pnl_pct")) or 0.0
    pnl = float(pnl)

    if regime == "improving":
        return min(1.20, 1.00 + confidence * 0.20)

    if regime == "deteriorating":
        return max(0.40, 1.00 - confidence * 0.50)

    if regime == "insufficient_history":
        return 0.75

    if pnl < -0.03:
        return 0.80

    return 1.00


def normalize_with_cash(weights: dict[str, float], max_gross: float = 0.70) -> dict[str, float]:
    positive = {k: max(0.0, float(v)) for k, v in weights.items()}
    total = sum(positive.values())

    if total <= 0:
        return {**{k: 0.0 for k in positive}, "CASH": 1.0}

    scaled = {k: round((v / total) * max_gross, 6) for k, v in positive.items()}
    scaled["CASH"] = round(max(0.0, 1.0 - sum(scaled.values())), 6)

    return scaled


def build_adaptive_weights(inputs: dict) -> dict:
    base = base_weights(inputs.get("alpha_portfolio"))
    multipliers = registry_multipliers(inputs.get("registry"))
    regime_mult = regime_multiplier(inputs.get("learning", {}) or {}, inputs.get("performance", {}) or {})

    adjusted = {}

    for asset, weight in base.items():
        adjusted[asset] = float(weight) * float(multipliers.get(asset, 1.0)) * regime_mult

    final = normalize_with_cash(adjusted, max_gross=0.70)

    rows = []
    for asset, weight in final.items():
        rows.append({
            "asset": asset,
            "base_weight": round(float(base.get(asset, 0.0)), 6),
            "registry_multiplier": round(float(multipliers.get(asset, 1.0)), 6),
            "regime_multiplier": round(float(regime_mult), 6),
            "adaptive_weight": round(float(weight), 6),
            "source": "adaptive_weighting_v3",
        })

    return {
        "base_weights": base,
        "registry_multipliers": multipliers,
        "regime_multiplier": round(regime_mult, 6),
        "adaptive_weights": final,
        "rows": rows,
    }
