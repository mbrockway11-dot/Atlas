
"""Mark-to-Market v3 equity curve."""

from __future__ import annotations

from datetime import datetime, UTC
from pathlib import Path

import pandas as pd


EQUITY_CURVE = Path("output/investment_mark_to_market/equity_curve.csv")


def append_equity_snapshot(equity: float, cash: float, market_value: float, pnl: float, pnl_pct: float) -> tuple[dict, pd.DataFrame]:
    timestamp = datetime.now(UTC).isoformat()

    old = read_old_curve()
    rolling_high = max([equity] + pd.to_numeric(old.get("equity", pd.Series(dtype=float)), errors="coerce").dropna().tolist()) if not old.empty else equity
    drawdown = (equity - rolling_high) / rolling_high if rolling_high else 0.0

    row = {
        "timestamp": timestamp,
        "equity": round(equity, 2),
        "cash": round(cash, 2),
        "market_value": round(market_value, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 6),
        "rolling_high": round(rolling_high, 2),
        "drawdown": round(drawdown, 6),
    }

    curve = pd.concat([old, pd.DataFrame([row])], ignore_index=True) if not old.empty else pd.DataFrame([row])
    return row, curve


def read_old_curve() -> pd.DataFrame:
    if not EQUITY_CURVE.exists() or EQUITY_CURVE.stat().st_size == 0:
        return pd.DataFrame()

    try:
        return pd.read_csv(EQUITY_CURVE)
    except Exception:
        return pd.DataFrame()
