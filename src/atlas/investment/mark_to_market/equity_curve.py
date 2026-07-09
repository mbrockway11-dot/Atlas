
"""Equity curve update."""

from __future__ import annotations

from datetime import datetime, UTC

import pandas as pd


INITIAL_EQUITY = 100000.0


def build_equity_snapshot(unrealized: pd.DataFrame, existing_curve: pd.DataFrame) -> dict:
    market_value = float(unrealized["market_value"].sum()) if not unrealized.empty else 0.0
    cash = max(0.0, INITIAL_EQUITY - float(unrealized["cost_basis"].sum())) if not unrealized.empty else INITIAL_EQUITY
    equity = market_value + cash

    if existing_curve.empty or "equity" not in existing_curve.columns:
        rolling_high = equity
    else:
        rolling_high = max(float(existing_curve["equity"].max()), equity)

    drawdown = (equity / rolling_high - 1.0) if rolling_high else 0.0

    return {
        "timestamp": datetime.now(UTC).isoformat(),
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "pnl": round(equity - INITIAL_EQUITY, 2),
        "pnl_pct": round((equity - INITIAL_EQUITY) / INITIAL_EQUITY, 6),
        "rolling_high": round(rolling_high, 2),
        "drawdown": round(drawdown, 6),
    }


def append_equity_curve(existing_curve: pd.DataFrame, snapshot: dict) -> pd.DataFrame:
    new = pd.DataFrame([snapshot])

    if existing_curve.empty:
        return new

    return pd.concat([existing_curve, new], ignore_index=True)
