
"""Adaptive Weighting v5 regime-preserving weighting logic.

Alpha Ensemble v5.1 owns the portfolio-level risky/cash boundary.
Adaptive Weighting may modify relative weights inside the risky sleeve,
but must preserve the ensemble's explicit cash recommendation exactly.
"""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


DEFAULT_WEIGHTS = {
    "BTC-USD": 0.35,
    "ETH-USD": 0.35,
    "CASH": 0.30,
}

TOLERANCE = 0.000001


def ensemble_base_weights(
    ensemble_allocations: pd.DataFrame,
) -> dict[str, float]:
    """Load normalized Alpha Ensemble allocation hints."""
    if (
        ensemble_allocations is None
        or ensemble_allocations.empty
        or "asset" not in ensemble_allocations.columns
    ):
        return dict(DEFAULT_WEIGHTS)

    weight_column = next(
        (
            column
            for column in [
                "ensemble_target_weight",
                "target_weight",
                "weight",
                "allocation",
            ]
            if column in ensemble_allocations.columns
        ),
        None,
    )

    if weight_column is None:
        return dict(DEFAULT_WEIGHTS)

    weights: dict[str, float] = {}

    for _, row in ensemble_allocations.iterrows():
        asset = str(row.get("asset", "")).strip()

        if not asset:
            continue

        weights[asset] = max(
            0.0,
            finite_number(
                row.get(weight_column)
            ),
        )

    return normalize_total(weights)


def registry_multipliers(
    registry: pd.DataFrame,
) -> dict[str, float]:
    if registry is None or registry.empty:
        return {}

    multipliers: dict[str, float] = {}

    for _, row in registry.iterrows():
        asset = str(row.get("asset", "")).strip()

        if not asset:
            continue

        multiplier = finite_number(
            row.get("weight_multiplier"),
            default=1.0,
        )
        confidence = finite_number(
            row.get("asset_confidence"),
            default=0.5,
        )

        confidence_adjustment = (
            0.75 + confidence * 0.50
        )

        multipliers[asset] = round(
            max(
                0.0,
                multiplier * confidence_adjustment,
            ),
            6,
        )

    return multipliers


def learning_overlay_multiplier(
    learning: dict,
    performance: dict,
) -> float:
    """Return an intra-sleeve conviction multiplier.

    This multiplier may change relative risky-asset allocation, but v5
    never allows it to alter the Alpha Ensemble risky/cash boundary.
    """
    learning_regime = (
        learning.get("learning_regime", {}) or {}
    )

    regime = str(
        learning_regime.get(
            "learning_regime",
            "unknown",
        )
    )

    confidence = finite_number(
        learning.get("learning_confidence"),
        default=0.0,
    )

    pnl = finite_number(
        (
            performance.get("pnl", {}) or {}
        ).get("pnl_pct"),
        default=0.0,
    )

    if regime == "improving":
        return min(
            1.20,
            1.00 + confidence * 0.20,
        )

    if regime == "deteriorating":
        return max(
            0.40,
            1.00 - confidence * 0.50,
        )

    if regime == "insufficient_history":
        return 0.75

    if pnl < -0.03:
        return 0.80

    return 1.00


def normalize_total(
    weights: dict[str, float],
) -> dict[str, float]:
    cleaned = {
        str(asset): max(
            0.0,
            finite_number(weight),
        )
        for asset, weight in weights.items()
    }

    total = sum(cleaned.values())

    if total <= 0:
        return dict(DEFAULT_WEIGHTS)

    normalized = {
        asset: weight / total
        for asset, weight in cleaned.items()
    }

    return reconcile_total(normalized)


def preserve_regime_boundary(
    *,
    base_weights: dict[str, float],
    adjusted_risky: dict[str, float],
) -> dict[str, float]:
    """Normalize risky assets inside the original ensemble risky budget."""
    ensemble_cash = max(
        0.0,
        min(
            1.0,
            finite_number(
                base_weights.get("CASH"),
                default=0.0,
            ),
        ),
    )

    ensemble_risky_budget = max(
        0.0,
        1.0 - ensemble_cash,
    )

    risky = {
        asset: max(
            0.0,
            finite_number(weight),
        )
        for asset, weight in adjusted_risky.items()
        if asset.upper() != "CASH"
    }

    risky_total = sum(risky.values())

    if ensemble_risky_budget <= TOLERANCE:
        return {"CASH": 1.0}

    if risky_total <= TOLERANCE:
        base_risky = {
            asset: max(
                0.0,
                finite_number(weight),
            )
            for asset, weight in base_weights.items()
            if asset.upper() != "CASH"
        }

        base_total = sum(base_risky.values())

        if base_total <= TOLERANCE:
            return {"CASH": 1.0}

        final = {
            asset: (
                weight
                / base_total
                * ensemble_risky_budget
            )
            for asset, weight in base_risky.items()
        }
    else:
        final = {
            asset: (
                weight
                / risky_total
                * ensemble_risky_budget
            )
            for asset, weight in risky.items()
        }

    final["CASH"] = ensemble_cash

    return reconcile_total(final)


def build_adaptive_weights(
    inputs: dict,
) -> dict[str, Any]:
    base = ensemble_base_weights(
        inputs.get("ensemble_allocations")
    )

    multipliers = registry_multipliers(
        inputs.get("registry")
    )

    learning_multiplier = (
        learning_overlay_multiplier(
            inputs.get("learning", {}) or {},
            inputs.get("performance", {}) or {},
        )
    )

    adjusted_risky: dict[str, float] = {}

    for asset, base_weight in base.items():
        if asset.upper() == "CASH":
            continue

        registry_multiplier = finite_number(
            multipliers.get(asset),
            default=1.0,
        )

        adjusted_risky[asset] = (
            finite_number(base_weight)
            * registry_multiplier
            * learning_multiplier
        )

    final = preserve_regime_boundary(
        base_weights=base,
        adjusted_risky=adjusted_risky,
    )

    base_cash = finite_number(
        base.get("CASH"),
        default=0.0,
    )
    final_cash = finite_number(
        final.get("CASH"),
        default=0.0,
    )

    base_risky = sum(
        weight
        for asset, weight in base.items()
        if asset.upper() != "CASH"
    )

    final_risky = sum(
        weight
        for asset, weight in final.items()
        if asset.upper() != "CASH"
    )

    regime_preserved = (
        abs(base_cash - final_cash) <= TOLERANCE
        and abs(base_risky - final_risky) <= TOLERANCE
    )

    rows = []

    for asset, weight in final.items():
        rows.append({
            "asset": asset,
            "base_weight": round(
                finite_number(
                    base.get(asset)
                ),
                6,
            ),
            "registry_multiplier": round(
                finite_number(
                    multipliers.get(asset),
                    default=1.0,
                ),
                6,
            ),
            "learning_multiplier": round(
                learning_multiplier,
                6,
            ),
            "regime_multiplier": round(
                learning_multiplier,
                6,
            ),
            "adaptive_weight": round(
                weight,
                6,
            ),
            "ensemble_cash_weight": round(
                base_cash,
                6,
            ),
            "ensemble_risky_weight": round(
                base_risky,
                6,
            ),
            "regime_preserved": (
                regime_preserved
            ),
            "source": (
                "adaptive_weighting_v5_"
                "regime_preservation"
            ),
        })

    issues = []

    if not regime_preserved:
        issues.append({
            "issue": "REGIME_BOUNDARY_CHANGED",
            "ensemble_cash_weight": round(
                base_cash,
                6,
            ),
            "adaptive_cash_weight": round(
                final_cash,
                6,
            ),
            "ensemble_risky_weight": round(
                base_risky,
                6,
            ),
            "adaptive_risky_weight": round(
                final_risky,
                6,
            ),
        })

    total_weight = sum(final.values())

    if abs(total_weight - 1.0) > TOLERANCE:
        issues.append({
            "issue": "TOTAL_WEIGHT_MISMATCH",
            "total_weight": round(
                total_weight,
                6,
            ),
        })

    return {
        "success": len(issues) == 0,
        "base_weights": base,
        "registry_multipliers": multipliers,
        "learning_multiplier": round(
            learning_multiplier,
            6,
        ),
        "regime_multiplier": round(
            learning_multiplier,
            6,
        ),
        "ensemble_risky_weight": round(
            base_risky,
            6,
        ),
        "ensemble_cash_weight": round(
            base_cash,
            6,
        ),
        "adaptive_risky_weight": round(
            final_risky,
            6,
        ),
        "adaptive_cash_weight": round(
            final_cash,
            6,
        ),
        "effective_max_gross": round(
            final_risky,
            6,
        ),
        "regime_preserved": (
            regime_preserved
        ),
        "adaptive_weights": final,
        "rows": rows,
        "issues": issues,
        "source": "alpha_ensemble_v5_1",
    }


def reconcile_total(
    weights: dict[str, float],
) -> dict[str, float]:
    """Round weights and place floating-point drift into cash."""
    rounded = {
        asset: round(
            max(
                0.0,
                finite_number(weight),
            ),
            6,
        )
        for asset, weight in weights.items()
    }

    total = sum(rounded.values())
    difference = round(
        1.0 - total,
        6,
    )

    if "CASH" in rounded:
        rounded["CASH"] = round(
            max(
                0.0,
                rounded["CASH"] + difference,
            ),
            6,
        )
    elif abs(difference) > 0:
        rounded["CASH"] = difference

    return rounded


def finite_number(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )
