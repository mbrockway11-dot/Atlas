
"""Alpha backtest metrics."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def calculate_metrics(trades: pd.DataFrame) -> dict[str, Any]:
    """Calculate standardized metrics."""
    if trades.empty or "return" not in trades.columns:
        return empty_metrics()

    returns = pd.to_numeric(trades["return"], errors="coerce").dropna()

    if returns.empty:
        return empty_metrics()

    wins = returns[returns > 0]
    losses = returns[returns <= 0]

    equity = (1 + returns).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1
    max_dd = float(drawdown.min()) if not drawdown.empty else 0.0

    mean = float(returns.mean())
    std = float(returns.std()) if len(returns) > 1 else 0.0
    downside = returns[returns < 0]
    downside_std = float(downside.std()) if len(downside) > 1 else 0.0

    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = abs(float(losses.sum())) if not losses.empty else 0.0

    profit_factor = gross_profit / gross_loss if gross_loss else None
    sharpe = mean / std * math.sqrt(len(returns)) if std else None
    sortino = mean / downside_std * math.sqrt(len(returns)) if downside_std else None

    final_equity = float(equity.iloc[-1])
    total_return = final_equity - 1
    recovery = total_return / abs(max_dd) if max_dd else None

    return {
        "trade_count": int(len(returns)),
        "win_rate": round(float((returns > 0).mean()), 6),
        "avg_return": round(mean, 8),
        "median_return": round(float(returns.median()), 8),
        "std_return": round(std, 8),
        "min_return": round(float(returns.min()), 8),
        "max_return": round(float(returns.max()), 8),
        "gross_profit": round(gross_profit, 8),
        "gross_loss": round(gross_loss, 8),
        "profit_factor": round(profit_factor, 6) if profit_factor is not None else None,
        "sharpe_like": round(sharpe, 6) if sharpe is not None else None,
        "sortino_like": round(sortino, 6) if sortino is not None else None,
        "final_equity": round(final_equity, 8),
        "total_return": round(total_return, 8),
        "max_drawdown": round(max_dd, 8),
        "recovery_factor": round(recovery, 6) if recovery is not None else None,
        "expectancy": round(mean, 8),
    }


def empty_metrics() -> dict[str, Any]:
    return {
        "trade_count": 0,
        "win_rate": None,
        "avg_return": None,
        "median_return": None,
        "std_return": None,
        "min_return": None,
        "max_return": None,
        "gross_profit": None,
        "gross_loss": None,
        "profit_factor": None,
        "sharpe_like": None,
        "sortino_like": None,
        "final_equity": None,
        "total_return": None,
        "max_drawdown": None,
        "recovery_factor": None,
        "expectancy": None,
    }
