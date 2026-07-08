
"""Paper portfolio PnL."""

from __future__ import annotations

import pandas as pd


INITIAL_EQUITY = 100000.0


def calculate_pnl(portfolio: pd.DataFrame, initial_equity: float = INITIAL_EQUITY) -> dict:
    if portfolio.empty:
        return {
            "initial_equity": initial_equity,
            "current_equity": initial_equity,
            "pnl": 0.0,
            "pnl_pct": 0.0,
        }

    current_equity = float(portfolio["paper_value"].sum())
    pnl = current_equity - initial_equity
    pnl_pct = pnl / initial_equity if initial_equity else 0.0

    return {
        "initial_equity": round(float(initial_equity), 2),
        "current_equity": round(float(current_equity), 2),
        "pnl": round(float(pnl), 2),
        "pnl_pct": round(float(pnl_pct), 6),
    }
