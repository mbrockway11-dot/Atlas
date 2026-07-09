
"""Rebalance Engine v4 target/current extraction."""

from __future__ import annotations

import pandas as pd


def extract_target_weights(alpha_portfolio: pd.DataFrame) -> dict[str, float]:
    if alpha_portfolio is None or alpha_portfolio.empty:
        return {"CASH": 1.0}

    weight_col = None
    for candidate in ["target_weight", "paper_weight", "weight", "allocation", "target_exposure"]:
        if candidate in alpha_portfolio.columns:
            weight_col = candidate
            break

    if not weight_col or "asset" not in alpha_portfolio.columns:
        return {"CASH": 1.0}

    targets = {}

    for _, row in alpha_portfolio.iterrows():
        asset = str(row.get("asset"))
        targets[asset] = max(0.0, round(float(row.get(weight_col) or 0.0), 6))

    total = sum(targets.values())

    if total > 1.000001:
        targets = {k: round(v / total, 6) for k, v in targets.items()}

    if "CASH" not in targets:
        risky = sum(v for k, v in targets.items() if k != "CASH")
        targets["CASH"] = round(max(0.0, 1.0 - risky), 6)

    return targets


def extract_current_weights(holdings: pd.DataFrame, portfolio_state: dict) -> dict[str, float]:
    if holdings is not None and not holdings.empty and "asset" in holdings.columns:
        weight_col = "weight" if "weight" in holdings.columns else None

        if weight_col:
            current = {}
            for _, row in holdings.iterrows():
                current[str(row.get("asset"))] = round(float(row.get(weight_col) or 0.0), 6)
            return current

    state = (portfolio_state.get("state", {}) or {})
    exposure = state.get("exposure", {}) or {}

    return {
        "RISKY": round(float(exposure.get("risky_weight") or 0.0), 6),
        "CASH": round(float(exposure.get("cash_weight") or 1.0), 6),
    }
