"""Validation performance metrics."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from atlas.investment.hypothesis_validation.config import (
    TRANSACTION_COST_BPS,
)


def summarize_trade_returns(
    trades: pd.DataFrame,
) -> dict:
    """Summarize net non-overlapping strategy returns."""
    if (
        trades is None
        or trades.empty
        or "strategy_return"
        not in trades.columns
    ):
        return empty_metrics()

    gross = pd.to_numeric(
        trades["strategy_return"],
        errors="coerce",
    ).replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    ).dropna()

    if gross.empty:
        return empty_metrics()

    cost = (
        TRANSACTION_COST_BPS
        / 10_000.0
    )

    net = gross - cost

    positive = float(
        net[
            net > 0
        ].sum()
    )

    negative = abs(
        float(
            net[
                net < 0
            ].sum()
        )
    )

    profit_factor = (
        positive / negative
        if negative > 1e-12
        else (
            999.0
            if positive > 0
            else 0.0
        )
    )

    standard_deviation = float(
        net.std(
            ddof=0
        )
    )

    trade_sharpe = (
        float(
            net.mean()
        )
        / standard_deviation
        * math.sqrt(
            len(net)
        )
        if standard_deviation > 1e-12
        else 0.0
    )

    equity = (
        1.0 + net
    ).clip(
        lower=0.0
    ).cumprod()

    running_maximum = equity.cummax()

    drawdown = (
        equity
        / running_maximum
        - 1.0
    )

    maximum_drawdown = float(
        drawdown.min()
    )

    cumulative_return = float(
        equity.iloc[-1] - 1.0
    )

    return {
        "trade_count": int(
            len(net)
        ),
        "win_rate": round(
            float(
                (
                    net > 0
                ).mean()
            ),
            8,
        ),
        "mean_return": round(
            float(
                net.mean()
            ),
            8,
        ),
        "median_return": round(
            float(
                net.median()
            ),
            8,
        ),
        "return_std": round(
            standard_deviation,
            8,
        ),
        "profit_factor": round(
            finite(
                profit_factor
            ),
            8,
        ),
        "trade_sharpe": round(
            finite(
                trade_sharpe
            ),
            8,
        ),
        "cumulative_return": round(
            cumulative_return,
            8,
        ),
        "maximum_drawdown": round(
            maximum_drawdown,
            8,
        ),
        "best_trade": round(
            float(
                net.max()
            ),
            8,
        ),
        "worst_trade": round(
            float(
                net.min()
            ),
            8,
        ),
        "transaction_cost_bps": (
            TRANSACTION_COST_BPS
        ),
    }


def compare_metrics(
    baseline: dict,
    candidate: dict,
) -> dict:
    """Calculate candidate advantages over the original engine."""
    return {
        "mean_return_advantage": round(
            float(
                candidate[
                    "mean_return"
                ]
            )
            - float(
                baseline[
                    "mean_return"
                ]
            ),
            8,
        ),
        "profit_factor_advantage": round(
            float(
                candidate[
                    "profit_factor"
                ]
            )
            - float(
                baseline[
                    "profit_factor"
                ]
            ),
            8,
        ),
        "sharpe_advantage": round(
            float(
                candidate[
                    "trade_sharpe"
                ]
            )
            - float(
                baseline[
                    "trade_sharpe"
                ]
            ),
            8,
        ),
        "drawdown_improvement": round(
            abs(
                float(
                    baseline[
                        "maximum_drawdown"
                    ]
                )
            )
            - abs(
                float(
                    candidate[
                        "maximum_drawdown"
                    ]
                )
            ),
            8,
        ),
        "cumulative_return_advantage": round(
            float(
                candidate[
                    "cumulative_return"
                ]
            )
            - float(
                baseline[
                    "cumulative_return"
                ]
            ),
            8,
        ),
    }


def empty_metrics() -> dict:
    return {
        "trade_count": 0,
        "win_rate": 0.0,
        "mean_return": 0.0,
        "median_return": 0.0,
        "return_std": 0.0,
        "profit_factor": 0.0,
        "trade_sharpe": 0.0,
        "cumulative_return": 0.0,
        "maximum_drawdown": 0.0,
        "best_trade": 0.0,
        "worst_trade": 0.0,
        "transaction_cost_bps": (
            TRANSACTION_COST_BPS
        ),
    }


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )
