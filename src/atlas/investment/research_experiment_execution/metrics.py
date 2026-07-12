"""Research experiment performance metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def calculate_metrics(
    returns: pd.Series,
) -> dict:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    trade_count = int(
        len(values)
    )

    if trade_count == 0:
        return empty_metrics()

    mean_return = float(
        values.mean()
    )

    median_return = float(
        values.median()
    )

    win_rate = float(
        values.gt(0).mean()
    )

    losses = values[
        values.lt(0)
    ]

    wins = values[
        values.gt(0)
    ]

    average_win = float(
        wins.mean()
    ) if not wins.empty else 0.0

    average_loss = float(
        losses.mean()
    ) if not losses.empty else 0.0

    expectancy = (
        win_rate
        * average_win
        + (
            1.0 - win_rate
        )
        * average_loss
    )

    standard_deviation = float(
        values.std(
            ddof=1
        )
    ) if trade_count > 1 else 0.0

    sharpe_ratio = (
        mean_return
        / standard_deviation
        * math.sqrt(
            trade_count
        )
        if standard_deviation > 0
        else 0.0
    )

    equity_curve = (
        1.0 + values
    ).cumprod()

    running_peak = (
        equity_curve.cummax()
    )

    drawdown = (
        equity_curve
        / running_peak
        - 1.0
    )

    max_drawdown = float(
        drawdown.min()
    ) if not drawdown.empty else 0.0

    total_return = float(
        equity_curve.iloc[-1]
        - 1.0
    )

    return_to_drawdown = (
        total_return
        / abs(
            max_drawdown
        )
        if max_drawdown < 0
        else 0.0
    )

    return {
        "trade_count": trade_count,
        "mean_return": mean_return,
        "median_return": median_return,
        "win_rate": win_rate,
        "average_win": average_win,
        "average_loss": average_loss,
        "expectancy": expectancy,
        "sharpe_ratio": sharpe_ratio,
        "max_drawdown": max_drawdown,
        "total_return": total_return,
        "return_to_drawdown": (
            return_to_drawdown
        ),
    }


def empty_metrics() -> dict:
    return {
        "trade_count": 0,
        "mean_return": 0.0,
        "median_return": 0.0,
        "win_rate": 0.0,
        "average_win": 0.0,
        "average_loss": 0.0,
        "expectancy": 0.0,
        "sharpe_ratio": 0.0,
        "max_drawdown": 0.0,
        "total_return": 0.0,
        "return_to_drawdown": 0.0,
    }
