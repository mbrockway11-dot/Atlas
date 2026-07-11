"""Walk-forward portfolio simulator."""

from __future__ import annotations

import math

import pandas as pd

from atlas.investment.portfolio_promotion_lab_v2.baseline import (
    reconstruct_baseline_portfolio,
)
from atlas.investment.portfolio_promotion_lab_v2.candidate import (
    reconstruct_candidate_portfolio,
)
from atlas.investment.portfolio_promotion_lab_v2.config import (
    ANNUALIZATION_DAYS,
    REBALANCE_FREQUENCY_DAYS,
    TRANSACTION_COST_BPS,
)


def build_rebalance_dates(
    market: pd.DataFrame,
) -> list[pd.Timestamp]:
    """Build deterministic rebalance calendar from available dates."""
    dates = sorted(
        market["date"]
        .dropna()
        .unique()
        .tolist()
    )

    if not dates:
        return []

    selected = []

    last_selected = None

    for raw_date in dates:
        date = pd.Timestamp(
            raw_date
        )

        if (
            last_selected is None
            or (
                date - last_selected
            ).days
            >= REBALANCE_FREQUENCY_DAYS
        ):
            selected.append(date)
            last_selected = date

    return selected


def run_walk_forward(
    *,
    market: pd.DataFrame,
    signals: pd.DataFrame,
    returns: pd.DataFrame,
    governance_map: dict[str, float],
) -> dict:
    """Reconstruct and simulate both portfolios through time."""
    rebalance_dates = build_rebalance_dates(
        market
    )

    baseline = simulate_portfolio(
        portfolio_name=(
            "alpha_portfolio_v3_1"
        ),
        rebalance_dates=rebalance_dates,
        market=market,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
        candidate=False,
    )

    candidate = simulate_portfolio(
        portfolio_name=(
            "portfolio_optimizer_v2"
        ),
        rebalance_dates=rebalance_dates,
        market=market,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
        candidate=True,
    )

    return {
        "baseline": baseline,
        "candidate": candidate,
        "rebalance_dates": (
            rebalance_dates
        ),
    }


def simulate_portfolio(
    *,
    portfolio_name: str,
    rebalance_dates: list[pd.Timestamp],
    market: pd.DataFrame,
    signals: pd.DataFrame,
    returns: pd.DataFrame,
    governance_map: dict[str, float],
    candidate: bool,
) -> dict:
    """Simulate one reconstructed portfolio."""
    equity = 1.0

    current_weights = pd.Series(
        {
            "CASH": 1.0,
        }
    )

    curve_rows = []
    rebalance_rows = []

    for index, rebalance_date in enumerate(
        rebalance_dates
    ):
        next_date = (
            rebalance_dates[
                index + 1
            ]
            if index + 1
            < len(rebalance_dates)
            else returns.index.max()
        )

        if candidate:
            target_weights = (
                reconstruct_candidate_portfolio(
                    rebalance_date=rebalance_date,
                    signals=signals,
                    returns=returns,
                    governance_map=(
                        governance_map
                    ),
                )
            )
        else:
            target_weights = (
                reconstruct_baseline_portfolio(
                    market,
                    rebalance_date=(
                        rebalance_date
                    ),
                )
            )

        turnover = calculate_turnover(
            current_weights,
            target_weights,
        )

        transaction_cost = (
            turnover
            * TRANSACTION_COST_BPS
            / 10_000.0
        )

        equity *= (
            1.0 - transaction_cost
        )

        rebalance_rows.append({
            "portfolio": portfolio_name,
            "rebalance_date": (
                rebalance_date
            ),
            "next_rebalance_date": (
                next_date
            ),
            "turnover": round(
                turnover,
                8,
            ),
            "transaction_cost": round(
                transaction_cost,
                8,
            ),
            "risky_weight": round(
                float(
                    target_weights.drop(
                        labels=["CASH"],
                        errors="ignore",
                    ).sum()
                ),
                8,
            ),
            "cash_weight": round(
                float(
                    target_weights.get(
                        "CASH",
                        0.0,
                    )
                ),
                8,
            ),
            "asset_count": int(
                len(
                    target_weights.drop(
                        labels=["CASH"],
                        errors="ignore",
                    )
                )
            ),
            "weights": serialize_weights(
                target_weights
            ),
        })

        holding_returns = returns.loc[
            (
                returns.index
                > rebalance_date
            )
            & (
                returns.index
                <= next_date
            )
        ]

        for date, asset_returns in (
            holding_returns.iterrows()
        ):
            daily_return = calculate_daily_return(
                asset_returns,
                target_weights,
            )

            equity *= (
                1.0 + daily_return
            )

            curve_rows.append({
                "portfolio": portfolio_name,
                "date": date,
                "daily_return": round(
                    daily_return,
                    10,
                ),
                "equity": round(
                    equity,
                    10,
                ),
            })

        current_weights = target_weights

    curve = pd.DataFrame(
        curve_rows
    )

    rebalances = pd.DataFrame(
        rebalance_rows
    )

    metrics = summarize_simulation(
        curve,
        rebalances,
    )

    return {
        "curve": curve,
        "rebalances": rebalances,
        "metrics": metrics,
    }


def calculate_daily_return(
    asset_returns: pd.Series,
    weights: pd.Series,
) -> float:
    total = 0.0

    for asset, weight in weights.items():
        if asset == "CASH":
            continue

        value = asset_returns.get(
            asset,
            0.0,
        )

        if pd.isna(value):
            value = 0.0

        total += (
            float(weight)
            * float(value)
        )

    return total


def calculate_turnover(
    current: pd.Series,
    target: pd.Series,
) -> float:
    assets = set(
        current.index
    ) | set(
        target.index
    )

    return 0.5 * sum(
        abs(
            float(
                current.get(
                    asset,
                    0.0,
                )
            )
            - float(
                target.get(
                    asset,
                    0.0,
                )
            )
        )
        for asset in assets
    )


def summarize_simulation(
    curve: pd.DataFrame,
    rebalances: pd.DataFrame,
) -> dict:
    if curve.empty:
        return empty_metrics()

    returns = pd.to_numeric(
        curve["daily_return"],
        errors="coerce",
    ).dropna()

    equity = pd.to_numeric(
        curve["equity"],
        errors="coerce",
    ).dropna()

    cumulative_return = float(
        equity.iloc[-1] - 1.0
    )

    years = (
        len(returns)
        / ANNUALIZATION_DAYS
    )

    annualized_return = (
        (
            max(
                1e-12,
                equity.iloc[-1],
            )
            ** (
                1.0 / years
            )
        )
        - 1.0
        if years > 0
        else 0.0
    )

    volatility = float(
        returns.std(
            ddof=0
        )
        * math.sqrt(
            ANNUALIZATION_DAYS
        )
    )

    mean_annualized = float(
        returns.mean()
        * ANNUALIZATION_DAYS
    )

    sharpe = (
        mean_annualized
        / volatility
        if volatility > 1e-12
        else 0.0
    )

    downside = returns[
        returns < 0
    ]

    downside_deviation = (
        float(
            downside.std(
                ddof=0
            )
            * math.sqrt(
                ANNUALIZATION_DAYS
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

    running_maximum = equity.cummax()

    drawdown = (
        equity / running_maximum
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

    return {
        "observation_count": int(
            len(returns)
        ),
        "rebalance_count": int(
            len(rebalances)
        ),
        "cumulative_return": round(
            cumulative_return,
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
            float(
                (
                    returns > 0
                ).mean()
            ),
            8,
        ),
        "average_turnover": round(
            float(
                rebalances[
                    "turnover"
                ].mean()
            )
            if not rebalances.empty
            else 0.0,
            8,
        ),
        "total_transaction_cost": round(
            float(
                rebalances[
                    "transaction_cost"
                ].sum()
            )
            if not rebalances.empty
            else 0.0,
            8,
        ),
        "average_cash_weight": round(
            float(
                rebalances[
                    "cash_weight"
                ].mean()
            )
            if not rebalances.empty
            else 1.0,
            8,
        ),
        "average_asset_count": round(
            float(
                rebalances[
                    "asset_count"
                ].mean()
            )
            if not rebalances.empty
            else 0.0,
            8,
        ),
    }


def serialize_weights(
    weights: pd.Series,
) -> str:
    return "|".join(
        f"{asset}:{float(weight):.8f}"
        for asset, weight in sorted(
            weights.items()
        )
    )


def empty_metrics() -> dict:
    return {
        "observation_count": 0,
        "rebalance_count": 0,
        "cumulative_return": 0.0,
        "annualized_return": 0.0,
        "annualized_volatility": 0.0,
        "sharpe": 0.0,
        "sortino": 0.0,
        "maximum_drawdown": 0.0,
        "calmar": 0.0,
        "daily_win_rate": 0.0,
        "average_turnover": 0.0,
        "total_transaction_cost": 0.0,
        "average_cash_weight": 1.0,
        "average_asset_count": 0.0,
    }
