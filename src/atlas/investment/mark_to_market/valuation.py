
"""Position valuation."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def value_positions(cost_basis: pd.DataFrame, prices: dict[str, float]) -> pd.DataFrame:
    if cost_basis.empty:
        return pd.DataFrame()

    out = cost_basis.copy()

    out["current_price"] = out["asset"].map(prices).fillna(out["current_price"])
    out["market_value"] = out["quantity"] * out["current_price"]
    out["portfolio_weight"] = out["market_value"] / INITIAL_EQUITY

    return out
