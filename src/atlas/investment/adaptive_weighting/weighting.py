
"""Adaptive Weighting v4 weighting logic.

Adaptive Weighting v4 consumes Alpha Ensemble v4 allocation hints first,
then applies registry, learning, and performance overlays.
"""

from __future__ import annotations

import pandas as pd


DEFAULT_WEIGHTS = {
    "BTC-USD": 0.35,
    "ETH-USD": 0.35,
    "SOL-USD": 0.0,
    "CASH": 0.30,
}


def ensemble_base_weights(ensemble_allocations: pd.DataFrame) -> dict[str, float]:
    if ensemble_allocations is None or ensemble_allocations.empty:
        return dict(DEFAULT_WEIGHTS)

    if "asset" not in ensemble_allocations.columns:
        return dict(DEFAULT_WEIGHTS)

    weight_col = None
    for candidate in ["ensemble_target_weight", "target_weight", "weight", "allocation"]:
        if candidate in ensemble_allocations.columns:
            weight_col = candidate
            break

    if not weight_col:
        return dict(DEFAULT_WEIGHTS)

    weights = {}

    for _, row in ensemble_allocations.iterrows():
        asset = str(row.get("asset"))
        weights[asset] = max(0.0, float(row.get(weight_col) or 0.0))

    return normalize_total(weights)


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


def normalize_total(weights: dict[str, float]) -> dict[str, float]:
    cleaned = {k: max(0.0, float(v)) for k, v in weights.items()}
    total = sum(cleaned.values())

    if total <= 0:
        return dict(DEFAULT_WEIGHTS)

    return {k: round(v / total, 6) for k, v in cleaned.items()}


def normalize_with_cash(weights: dict[str, float], max_gross: float = 0.70) -> dict[str, float]:
    risky = {k: max(0.0, float(v)) for k, v in weights.items() if k != "CASH"}
    total_risky = sum(risky.values())

    if total_risky <= 0:
        return {"CASH": 1.0}

    scaled = {k: round((v / total_risky) * max_gross, 6) for k, v in risky.items()}
    scaled["CASH"] = round(max(0.0, 1.0 - sum(scaled.values())), 6)

    return scaled


def build_adaptive_weights(inputs: dict) -> dict:
    base = ensemble_base_weights(inputs.get("ensemble_allocations"))
    multipliers = registry_multipliers(inputs.get("registry"))
    regime_mult = regime_multiplier(inputs.get("learning", {}) or {}, inputs.get("performance", {}) or {})

    adjusted = {}

    for asset, weight in base.items():
        if asset == "CASH":
            continue

        adjusted[asset] = float(weight) * float(multipliers.get(asset, 1.0)) * regime_mult

    # Regime confidence changes total portfolio exposure rather than
    # disappearing during normalization. A 0.75 multiplier therefore
    # reduces maximum risky exposure from 70% to 52.5%.
    effective_max_gross = max(
        0.0,
        min(0.70, 0.70 * float(regime_mult)),
    )

    final = normalize_with_cash(
        adjusted,
        max_gross=effective_max_gross,
    )

    rows = []

    for asset, weight in final.items():
        rows.append({
            "asset": asset,
            "base_weight": round(float(base.get(asset, 0.0)), 6),
            "registry_multiplier": round(float(multipliers.get(asset, 1.0)), 6),
            "regime_multiplier": round(float(regime_mult), 6),
            "adaptive_weight": round(float(weight), 6),
            "source": "adaptive_weighting_v4_alpha_ensemble",
        })

    return {
        "base_weights": base,
        "registry_multipliers": multipliers,
        "regime_multiplier": round(regime_mult, 6),
        "effective_max_gross": round(effective_max_gross, 6),
        "adaptive_weights": final,
        "rows": rows,
        "source": "alpha_ensemble_v4",
    }
