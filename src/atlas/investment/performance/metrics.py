
"""Performance Engine v3 metrics."""

from __future__ import annotations

import math
import pandas as pd


def equity_metrics(equity_curve: pd.DataFrame) -> dict:
    if equity_curve.empty or "equity" not in equity_curve.columns:
        return empty_equity_metrics()

    df = equity_curve.copy()
    df["equity"] = pd.to_numeric(df["equity"], errors="coerce")
    df = df.dropna(subset=["equity"])

    if df.empty:
        return empty_equity_metrics()

    start = float(df["equity"].iloc[0])
    end = float(df["equity"].iloc[-1])
    pnl = end - start
    pnl_pct = pnl / start if start else 0.0

    returns = df["equity"].pct_change().dropna()
    volatility = float(returns.std()) if len(returns) else 0.0
    mean_return = float(returns.mean()) if len(returns) else 0.0

    sharpe = mean_return / volatility * math.sqrt(252) if volatility else 0.0

    downside = returns[returns < 0]
    downside_vol = float(downside.std()) if len(downside) else 0.0
    sortino = mean_return / downside_vol * math.sqrt(252) if downside_vol else 0.0

    rolling_high = df["equity"].cummax()
    drawdown = (df["equity"] - rolling_high) / rolling_high
    max_drawdown = float(drawdown.min()) if len(drawdown) else 0.0

    calmar = pnl_pct / abs(max_drawdown) if max_drawdown < 0 else 0.0

    return {
        "start_equity": round(start, 2),
        "current_equity": round(end, 2),
        "pnl": round(pnl, 2),
        "pnl_pct": round(pnl_pct, 6),
        "return_observations": int(len(returns)),
        "mean_return": round(mean_return, 8),
        "volatility": round(volatility, 8),
        "sharpe": round(sharpe, 6),
        "sortino": round(sortino, 6),
        "max_drawdown": round(max_drawdown, 6),
        "calmar": round(calmar, 6),
    }


def empty_equity_metrics() -> dict:
    return {
        "start_equity": 100000.0,
        "current_equity": 100000.0,
        "pnl": 0.0,
        "pnl_pct": 0.0,
        "return_observations": 0,
        "mean_return": 0.0,
        "volatility": 0.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "max_drawdown": 0.0,
        "calmar": 0.0,
    }


def trade_metrics(fills: pd.DataFrame) -> dict:
    if fills.empty:
        return {
            "trade_count": 0,
            "buy_count": 0,
            "sell_count": 0,
            "total_filled_weight": 0.0,
            "total_notional": 0.0,
            "avg_fill_weight": 0.0,
        }

    df = fills.copy()
    if "filled_weight" not in df.columns:
        df["filled_weight"] = 0.0
    if "notional_value" not in df.columns:
        df["notional_value"] = 0.0

    df["filled_weight"] = pd.to_numeric(df["filled_weight"], errors="coerce").fillna(0.0)
    df["notional_value"] = pd.to_numeric(df["notional_value"], errors="coerce").fillna(0.0)

    action = df.get("action", pd.Series(dtype=str)).astype(str).str.upper()

    return {
        "trade_count": int(len(df)),
        "buy_count": int((action == "BUY").sum()),
        "sell_count": int((action == "SELL").sum()),
        "total_filled_weight": round(float(df["filled_weight"].sum()), 6),
        "total_notional": round(float(df["notional_value"].sum()), 2),
        "avg_fill_weight": round(float(df["filled_weight"].mean()), 6) if len(df) else 0.0,
    }


def cost_metrics(fills: pd.DataFrame) -> dict:
    if fills.empty:
        return {
            "fee_drag": 0.0,
            "slippage_drag": 0.0,
            "total_cost_drag": 0.0,
            "cost_observations": 0,
        }

    df = fills.copy()

    for col in ["fee_drag", "slippage_drag", "total_cost_drag"]:
        if col not in df.columns:
            df[col] = 0.0

    fee = pd.to_numeric(df["fee_drag"], errors="coerce").fillna(0.0).sum()
    slip = pd.to_numeric(df["slippage_drag"], errors="coerce").fillna(0.0).sum()
    total = pd.to_numeric(df["total_cost_drag"], errors="coerce").fillna(0.0).sum()

    return {
        "fee_drag": round(float(fee), 8),
        "slippage_drag": round(float(slip), 8),
        "total_cost_drag": round(float(total), 8),
        "cost_observations": int(len(df)),
    }
