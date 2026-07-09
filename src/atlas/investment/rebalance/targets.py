
"""Target portfolio construction for Rebalance Engine v3."""

from __future__ import annotations

import pandas as pd


DEFAULT_ASSETS = ["BTC-USD", "ETH-USD", "SOL-USD"]


def current_weights(mtm_positions: pd.DataFrame) -> dict[str, float]:
    if mtm_positions.empty:
        return {}

    weights = {}

    for _, row in mtm_positions.iterrows():
        asset = str(row.get("asset"))
        weight = float(row.get("portfolio_weight") or 0.0)
        weights[asset] = weight

    return weights


def target_weights(target_portfolio: pd.DataFrame, fallback_current: dict[str, float]) -> dict[str, float]:
    if target_portfolio.empty:
        return dict(fallback_current)

    asset_col = "asset" if "asset" in target_portfolio.columns else None

    weight_col = None
    for candidate in ["target_weight", "paper_weight", "weight", "allocation", "target_exposure"]:
        if candidate in target_portfolio.columns:
            weight_col = candidate
            break

    if not asset_col or not weight_col:
        return dict(fallback_current)

    out = {}

    for _, row in target_portfolio.iterrows():
        asset = str(row.get(asset_col))
        weight = float(row.get(weight_col) or 0.0)
        if asset != "CASH":
            out[asset] = weight

    return normalize_risky(out)


def normalize_risky(weights: dict[str, float]) -> dict[str, float]:
    total = sum(max(0.0, float(v)) for v in weights.values())

    if total <= 0:
        return {}

    return {k: round(max(0.0, float(v)) / total, 6) for k, v in weights.items()}
