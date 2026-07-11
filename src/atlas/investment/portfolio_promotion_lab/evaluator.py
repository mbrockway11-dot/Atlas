"""Historical portfolio evaluation for Portfolio Promotion Lab v1."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from atlas.investment.portfolio_promotion_lab.thresholds import (
    TRADING_DAYS_PER_YEAR,
    TRANSACTION_COST_BPS,
)


def normalize_portfolio(
    portfolio: pd.DataFrame,
) -> pd.Series:
    """Normalize portfolio rows into an asset-weight vector."""
    if (
        portfolio is None
        or portfolio.empty
        or not {
            "asset",
            "target_weight",
        }.issubset(portfolio.columns)
    ):
        return pd.Series(dtype=float)

    frame = portfolio.copy()

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    frame["target_weight"] = pd.to_numeric(
        frame["target_weight"],
        errors="coerce",
    ).fillna(0.0).clip(lower=0.0)

    weights = (
        frame.groupby(
            "asset",
            sort=True,
        )["target_weight"]
        .sum()
    )

    total = float(
        weights.sum()
    )

    if total <= 1e-12:
        return pd.Series(
            {
                "CASH": 1.0,
            }
        )

    return weights / total


def build_asset_return_matrix(
    history: pd.DataFrame,
) -> pd.DataFrame:
    """Build canonical daily asset returns from market history."""
    if (
        history is None
        or history.empty
        or "asset" not in history.columns
        or "close" not in history.columns
    ):
        return pd.DataFrame()

    temporal = find_temporal_column(
        history
    )

    if temporal is None:
        return pd.DataFrame()

    frame = history.copy()

    frame["timestamp"] = pd.to_datetime(
        frame[temporal],
        errors="coerce",
        utc=True,
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    frame["close"] = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "asset",
            "close",
        ]
    ).sort_values(
        [
            "asset",
            "timestamp",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=[
            "asset",
            "timestamp",
        ],
        keep="last",
    )

    prices = frame.pivot_table(
        index="timestamp",
        columns="asset",
        values="close",
        aggfunc="last",
    ).sort_index()

    returns = prices.pct_change(
        fill_method=None
    )

    return returns.replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )


def evaluate_portfolio_windows(
    *,
    portfolio_name: str,
    weights: pd.Series,
    returns: pd.DataFrame,
    windows: list[int],
    reference_weights: pd.Series | None = None,
) -> pd.DataFrame:
    """Evaluate a fixed current allocation over real trailing windows."""
    rows = []

    for window in windows:
        sample = returns.tail(
            window
        )

        metrics = evaluate_window(
            weights=weights,
            returns=sample,
            reference_weights=reference_weights,
        )

        rows.append({
            "portfolio": portfolio_name,
            "window_days": int(window),
            **metrics,
        })

    return pd.DataFrame(rows)


def evaluate_window(
    *,
    weights: pd.Series,
    returns: pd.DataFrame,
    reference_weights: pd.Series | None,
) -> dict:
    """Calculate deterministic portfolio performance metrics."""
    risky_assets = [
        asset
        for asset in weights.index
        if asset != "CASH"
    ]

    available = [
        asset
        for asset in risky_assets
        if asset in returns.columns
    ]

    if not available:
        return empty_metrics()

    asset_returns = (
        returns[available]
        .fillna(0.0)
    )

    risky_weights = (
        weights.reindex(
            available
        )
        .fillna(0.0)
    )

    daily_returns = asset_returns.mul(
        risky_weights,
        axis=1,
    ).sum(axis=1)

    daily_returns = pd.to_numeric(
        daily_returns,
        errors="coerce",
    ).dropna()

    if len(daily_returns) < 5:
        return empty_metrics()

    turnover = calculate_turnover(
        weights,
        reference_weights,
    )

    transaction_cost = (
        turnover
        * TRANSACTION_COST_BPS
        / 10_000.0
    )

    gross_curve = (
        1.0 + daily_returns
    ).cumprod()

    gross_return = float(
        gross_curve.iloc[-1] - 1.0
    )

    net_return = (
        gross_return
        - transaction_cost
    )

    period_years = (
        len(daily_returns)
        / TRADING_DAYS_PER_YEAR
    )

    annualized_return = (
        (
            max(
                1e-12,
                1.0 + net_return,
            )
            ** (
                1.0
                / period_years
            )
        )
        - 1.0
        if period_years > 0
        else 0.0
    )

    volatility = float(
        daily_returns.std(
            ddof=0
        )
        * math.sqrt(
            TRADING_DAYS_PER_YEAR
        )
    )

    mean_annualized = float(
        daily_returns.mean()
        * TRADING_DAYS_PER_YEAR
    )

    sharpe = (
        mean_annualized
        / volatility
        if volatility > 1e-12
        else 0.0
    )

    downside = daily_returns[
        daily_returns < 0
    ]

    downside_deviation = (
        float(
            downside.std(
                ddof=0
            )
            * math.sqrt(
                TRADING_DAYS_PER_YEAR
            )
        )
        if not downside.empty
        else 0.0
    )

    sortino = (
        mean_annualized
        / downside_deviation
        if downside_deviation > 1e-12
        else 0.0
    )

    running_maximum = gross_curve.cummax()

    drawdown = (
        gross_curve
        / running_maximum
        - 1.0
    )

    maximum_drawdown = float(
        drawdown.min()
    )

    calmar = (
        annualized_return
        / abs(
            maximum_drawdown
        )
        if maximum_drawdown < -1e-12
        else 0.0
    )

    win_rate = float(
        (
            daily_returns > 0
        ).mean()
    )

    concentration = float(
        (
            weights.drop(
                labels=["CASH"],
                errors="ignore",
            )
            ** 2
        ).sum()
    )

    effective_assets = (
        1.0 / concentration
        if concentration > 1e-12
        else 0.0
    )

    cash_weight = float(
        weights.get(
            "CASH",
            0.0,
        )
    )

    largest_asset_weight = float(
        weights.drop(
            labels=["CASH"],
            errors="ignore",
        ).max()
        if len(weights) > 1
        else 0.0
    )

    return {
        "observation_count": int(
            len(daily_returns)
        ),
        "gross_return": round(
            gross_return,
            8,
        ),
        "transaction_cost": round(
            transaction_cost,
            8,
        ),
        "net_return": round(
            net_return,
            8,
        ),
        "annualized_return": round(
            annualized_return,
            8,
        ),
        "annualized_volatility": round(
            volatility,
            8,
        ),
        "sharpe": round(
            sharpe,
            8,
        ),
        "sortino": round(
            sortino,
            8,
        ),
        "maximum_drawdown": round(
            maximum_drawdown,
            8,
        ),
        "calmar": round(
            calmar,
            8,
        ),
        "daily_win_rate": round(
            win_rate,
            8,
        ),
        "turnover": round(
            turnover,
            8,
        ),
        "concentration_hhi": round(
            concentration,
            8,
        ),
        "effective_asset_count": round(
            effective_assets,
            8,
        ),
        "cash_weight": round(
            cash_weight,
            8,
        ),
        "largest_asset_weight": round(
            largest_asset_weight,
            8,
        ),
    }


def calculate_turnover(
    weights: pd.Series,
    reference: pd.Series | None,
) -> float:
    """Calculate one-way portfolio turnover."""
    if reference is None or reference.empty:
        return float(
            weights.drop(
                labels=["CASH"],
                errors="ignore",
            ).sum()
        )

    assets = set(
        weights.index
    ) | set(
        reference.index
    )

    return 0.5 * sum(
        abs(
            float(
                weights.get(
                    asset,
                    0.0,
                )
            )
            - float(
                reference.get(
                    asset,
                    0.0,
                )
            )
        )
        for asset in assets
    )


def empty_metrics() -> dict:
    return {
        "observation_count": 0,
        "gross_return": 0.0,
        "transaction_cost": 0.0,
        "net_return": 0.0,
        "annualized_return": 0.0,
        "annualized_volatility": 0.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "maximum_drawdown": 0.0,
        "calmar": 0.0,
        "daily_win_rate": 0.0,
        "turnover": 0.0,
        "concentration_hhi": 0.0,
        "effective_asset_count": 0.0,
        "cash_weight": 1.0,
        "largest_asset_weight": 0.0,
    }


def find_temporal_column(
    frame: pd.DataFrame,
) -> str | None:
    for candidate in [
        "timestamp",
        "date",
        "datetime",
        "time",
    ]:
        if candidate in frame.columns:
            return candidate

    return None
