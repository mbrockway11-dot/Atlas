
"""Unrealized PnL."""

from __future__ import annotations

import pandas as pd


def unrealized_pnl(valued: pd.DataFrame) -> pd.DataFrame:
    if valued.empty:
        return pd.DataFrame()

    out = valued.copy()
    out["unrealized_pnl"] = out["market_value"] - out["cost_basis"]
    out["unrealized_pnl_pct"] = out["unrealized_pnl"] / out["cost_basis"].replace(0, pd.NA)
    out["unrealized_pnl_pct"] = out["unrealized_pnl_pct"].fillna(0.0)

    return out
