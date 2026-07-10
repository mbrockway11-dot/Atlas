
"""Walk-forward metrics and portfolio risk controls."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd


def summarize_returns(
    returns: pd.Series,
    *,
    exposure: float = 0.10,
    drawdown_control: bool = False,
) -> dict[str, Any]:
    """Summarize returns with fixed fractional exposure and optional drawdown control."""
    raw = pd.to_numeric(returns, errors="coerce").dropna()

    if raw.empty:
        return empty_summary(exposure, drawdown_control)

    capped = raw.clip(lower=-0.95, upper=5.0)

    if drawdown_control:
        portfolio_returns = apply_drawdown_control(capped, base_exposure=exposure)
    else:
        portfolio_returns = capped * exposure

    wins = portfolio_returns[portfolio_returns > 0]
    losses = portfolio_returns[portfolio_returns <= 0]

    equity = (1 + portfolio_returns).cumprod()
    peak = equity.cummax()
    drawdown = equity / peak - 1

    gross_profit = float(wins.sum()) if not wins.empty else 0.0
    gross_loss = abs(float(losses.sum())) if not losses.empty else 0.0

    mean = float(portfolio_returns.mean())
    std = float(portfolio_returns.std()) if len(portfolio_returns) > 1 else 0.0

    return {
        "count": int(portfolio_returns.count()),
        "win_rate": round(float((portfolio_returns > 0).mean()), 6),
        "avg_return": round(mean, 8),
        "median_return": round(float(portfolio_returns.median()), 8),
        "profit_factor": round(gross_profit / gross_loss, 6) if gross_loss else None,
        "max_drawdown": round(float(drawdown.min()), 8) if not drawdown.empty else None,
        "sharpe_like": round(mean / std * math.sqrt(len(portfolio_returns)), 6) if std else None,
        "final_equity": round(float(equity.iloc[-1]), 8),
        "exposure": exposure,
        "drawdown_control": drawdown_control,
        "avg_raw_return_capped": round(float(capped.mean()), 8),
        "max_raw_return_capped": round(float(capped.max()), 8),
        "min_raw_return_capped": round(float(capped.min()), 8),
        "max_position_return": round(float(portfolio_returns.max()), 8),
        "min_position_return": round(float(portfolio_returns.min()), 8),
    }


def empty_summary(exposure: float, drawdown_control: bool) -> dict[str, Any]:
    return {
        "count": 0,
        "win_rate": None,
        "avg_return": None,
        "median_return": None,
        "profit_factor": None,
        "max_drawdown": None,
        "sharpe_like": None,
        "final_equity": None,
        "exposure": exposure,
        "drawdown_control": drawdown_control,
    }


def apply_drawdown_control(raw_returns: pd.Series, *, base_exposure: float = 0.10) -> pd.Series:
    """Scale exposure down as equity drawdown deepens."""
    equity = 1.0
    peak = 1.0
    controlled = []

    for raw in raw_returns:
        drawdown = equity / peak - 1

        if drawdown <= -0.50:
            exposure = base_exposure * 0.25
        elif drawdown <= -0.35:
            exposure = base_exposure * 0.50
        elif drawdown <= -0.20:
            exposure = base_exposure * 0.75
        else:
            exposure = base_exposure

        position_return = raw * exposure
        controlled.append(position_return)

        equity *= 1 + position_return
        peak = max(peak, equity)

    return pd.Series(controlled, index=raw_returns.index)


def non_overlapping_trades(trades: pd.DataFrame) -> pd.DataFrame:
    """Keep only non-overlapping trades per asset."""
    if trades.empty or not {"date", "asset", "hold_period"}.issubset(trades.columns):
        return trades

    rows = []
    tmp = trades.copy()
    tmp["date"] = pd.to_datetime(tmp["date"], errors="coerce")
    tmp = tmp.dropna(subset=["date"]).sort_values(["asset", "date"])

    for _, group in tmp.groupby("asset"):
        next_allowed = None

        for _, row in group.iterrows():
            date = row["date"]
            hold = int(row.get("hold_period") or 0)

            if next_allowed is None or date >= next_allowed:
                rows.append(row)
                next_allowed = date + pd.Timedelta(hours=hold)

    return pd.DataFrame(rows)


def stability_score(rows: list[dict[str, Any]]) -> float:
    """Return fraction of test windows with positive average return."""
    tested = [r for r in rows if (r.get("test", {}) or {}).get("count", 0) > 0]
    if not tested:
        return 0.0

    positive = [
        r for r in tested
        if ((r.get("test", {}) or {}).get("avg_return") or 0) > 0
    ]

    return round(len(positive) / len(tested), 6)
