
"""Performance Engine v3 benchmark tracking."""

from __future__ import annotations

import pandas as pd


def benchmark_tracking(equity_curve: pd.DataFrame) -> pd.DataFrame:
    if equity_curve.empty or "equity" not in equity_curve.columns:
        return pd.DataFrame([{
            "benchmark": "cash",
            "portfolio_return": 0.0,
            "benchmark_return": 0.0,
            "excess_return": 0.0,
        }])

    df = equity_curve.copy()
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    df = df.dropna(subset=["equity"])

    if len(df) < 1:
        port_ret = 0.0
    else:
        start = float(df["equity"].iloc[0])
        end = float(df["equity"].iloc[-1])
        port_ret = (end - start) / start if start else 0.0

    return pd.DataFrame([
        {
            "benchmark": "cash",
            "portfolio_return": round(port_ret, 6),
            "benchmark_return": 0.0,
            "excess_return": round(port_ret, 6),
        }
    ])
