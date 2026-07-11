"""Exposure-aware portfolio simulation for Alpha Research Lab."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


CURVE_COLUMNS = [
    "engine_id",
    "timestamp",
    "active_positions",
    "gross_exposure",
    "portfolio_return",
    "equity",
    "running_peak",
    "drawdown",
]


def build_engine_portfolio_curves(
    trades: pd.DataFrame,
    market: pd.DataFrame,
    *,
    transaction_cost_bps: float = 10.0,
    gross_exposure: float = 1.0,
) -> pd.DataFrame:
    """Build daily equal-weight MTM curves for each engine."""
    if (
        trades is None
        or trades.empty
        or market is None
        or market.empty
    ):
        return empty_curve_frame()

    normalized_trades = normalize_trades(trades)
    prices = normalize_prices(market)

    if normalized_trades.empty or prices.empty:
        return empty_curve_frame()

    frames: list[pd.DataFrame] = []

    for engine_id, engine_trades in (
        normalized_trades.groupby(
            "engine_id",
            sort=True,
        )
    ):
        curve = build_single_engine_curve(
            str(engine_id),
            engine_trades,
            prices,
            transaction_cost_bps=transaction_cost_bps,
            gross_exposure=gross_exposure,
        )

        if not curve.empty:
            frames.append(curve)

    if not frames:
        return empty_curve_frame()

    return pd.concat(
        frames,
        ignore_index=True,
    )[CURVE_COLUMNS]


def build_single_engine_curve(
    engine_id: str,
    trades: pd.DataFrame,
    prices: pd.DataFrame,
    *,
    transaction_cost_bps: float,
    gross_exposure: float,
) -> pd.DataFrame:
    """Build one engine's daily mark-to-market curve."""
    relevant_assets = set(
        trades["asset"].dropna().astype(str)
    )

    engine_prices = prices[
        prices["asset"].isin(
            relevant_assets
        )
    ].copy()

    if engine_prices.empty:
        return empty_curve_frame()

    engine_prices["asset_return"] = (
        engine_prices.groupby(
            "asset"
        )["close"]
        .pct_change(
            fill_method=None
        )
    )

    calendar = pd.DataFrame({
        "timestamp": sorted(
            engine_prices["timestamp"]
            .dropna()
            .unique()
        )
    })

    if calendar.empty:
        return empty_curve_frame()

    daily_rows: list[dict] = []
    cost_rate = (
        float(transaction_cost_bps)
        / 10_000.0
    )
    exposure = max(
        0.0,
        float(gross_exposure),
    )

    returns_by_timestamp = {
        timestamp: group.set_index(
            "asset"
        )["asset_return"].to_dict()
        for timestamp, group in engine_prices.groupby(
            "timestamp",
            sort=True,
        )
    }

    for timestamp in calendar["timestamp"]:
        # A signal observed at the entry timestamp becomes investable
        # after that close. Therefore, the strategy owns returns only
        # for timestamps strictly after entry and through the exit row.
        active = trades[
            (trades["timestamp"] < timestamp)
            & (trades["exit_timestamp"] >= timestamp)
        ]

        entries_today = int(
            (
                trades["timestamp"]
                == timestamp
            ).sum()
        )

        entry_cost = (
            cost_rate * exposure
            if entries_today > 0
            else 0.0
        )

        if active.empty:
            daily_rows.append({
                "engine_id": engine_id,
                "timestamp": timestamp,
                "active_positions": 0,
                "gross_exposure": 0.0,
                "portfolio_return": -entry_cost,
            })
            continue

        asset_returns = returns_by_timestamp.get(
            timestamp,
            {},
        )

        position_returns: list[float] = []

        for _, trade in active.iterrows():
            asset = str(trade["asset"])
            observed = asset_returns.get(asset)

            if observed is None or pd.isna(observed):
                continue

            direction = str(
                trade.get(
                    "direction",
                    "LONG",
                )
            ).upper()

            signed_return = float(observed)

            if direction == "SHORT":
                signed_return = -signed_return

            position_returns.append(
                signed_return
            )

        if position_returns:
            portfolio_return = (
                float(
                    np.mean(
                        position_returns
                    )
                )
                * exposure
            )
        else:
            portfolio_return = 0.0

        portfolio_return -= entry_cost

        daily_rows.append({
            "engine_id": engine_id,
            "timestamp": timestamp,
            "active_positions": int(
                len(active)
            ),
            "gross_exposure": (
                exposure
                if len(active) > 0
                else 0.0
            ),
            "portfolio_return": portfolio_return,
        })

    curve = pd.DataFrame(
        daily_rows
    )

    curve["portfolio_return"] = (
        pd.to_numeric(
            curve["portfolio_return"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(lower=-0.999999)
    )

    curve["equity"] = (
        1.0
        + curve["portfolio_return"]
    ).cumprod()

    curve["running_peak"] = (
        curve["equity"].cummax()
    )

    curve["drawdown"] = (
        curve["equity"]
        / curve["running_peak"]
        - 1.0
    )

    return curve[CURVE_COLUMNS]


def summarize_portfolio_curves(
    curves: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize exposure-aware portfolio performance."""
    columns = [
        "engine_id",
        "portfolio_days",
        "invested_days",
        "average_active_positions",
        "portfolio_cumulative_return",
        "portfolio_max_drawdown",
        "portfolio_daily_mean",
        "portfolio_daily_std",
        "portfolio_sharpe",
        "portfolio_recovery_factor",
    ]

    if curves is None or curves.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict] = []

    for engine_id, group in curves.groupby(
        "engine_id",
        sort=True,
    ):
        returns = pd.to_numeric(
            group["portfolio_return"],
            errors="coerce",
        ).fillna(0.0)

        equity = pd.to_numeric(
            group["equity"],
            errors="coerce",
        ).dropna()

        drawdown = pd.to_numeric(
            group["drawdown"],
            errors="coerce",
        ).dropna()

        cumulative = (
            float(equity.iloc[-1] - 1.0)
            if not equity.empty
            else 0.0
        )

        max_drawdown = (
            float(drawdown.min())
            if not drawdown.empty
            else 0.0
        )

        standard_deviation = float(
            returns.std(
                ddof=0
            )
        )

        sharpe = (
            float(
                returns.mean()
                / standard_deviation
                * math.sqrt(365.0)
            )
            if standard_deviation > 0
            else None
        )

        recovery = (
            cumulative / abs(max_drawdown)
            if max_drawdown < 0
            else None
        )

        rows.append({
            "engine_id": str(engine_id),
            "portfolio_days": int(
                len(group)
            ),
            "invested_days": int(
                (
                    group[
                        "active_positions"
                    ] > 0
                ).sum()
            ),
            "average_active_positions": round(
                float(
                    group[
                        "active_positions"
                    ].mean()
                ),
                8,
            ),
            "portfolio_cumulative_return": round(
                cumulative,
                8,
            ),
            "portfolio_max_drawdown": round(
                max_drawdown,
                8,
            ),
            "portfolio_daily_mean": round(
                float(returns.mean()),
                8,
            ),
            "portfolio_daily_std": round(
                standard_deviation,
                8,
            ),
            "portfolio_sharpe": (
                round(sharpe, 8)
                if sharpe is not None
                else None
            ),
            "portfolio_recovery_factor": (
                round(recovery, 8)
                if recovery is not None
                else None
            ),
        })

    return pd.DataFrame(
        rows,
        columns=columns,
    )


def normalize_trades(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    result = trades.copy()

    required = [
        "engine_id",
        "timestamp",
        "exit_timestamp",
        "asset",
        "direction",
    ]

    if any(
        column not in result.columns
        for column in required
    ):
        return pd.DataFrame()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        errors="coerce",
        utc=True,
    )

    result["exit_timestamp"] = pd.to_datetime(
        result["exit_timestamp"],
        errors="coerce",
        utc=True,
    )

    result["asset"] = result[
        "asset"
    ].astype(str)

    return result.dropna(
        subset=[
            "engine_id",
            "timestamp",
            "exit_timestamp",
            "asset",
        ]
    )


def normalize_prices(
    market: pd.DataFrame,
) -> pd.DataFrame:
    required = [
        "timestamp",
        "asset",
        "close",
    ]

    if any(
        column not in market.columns
        for column in required
    ):
        return pd.DataFrame()

    result = market[
        required
    ].copy()

    result["timestamp"] = pd.to_datetime(
        result["timestamp"],
        errors="coerce",
        utc=True,
    )

    result["asset"] = result[
        "asset"
    ].astype(str)

    result["close"] = pd.to_numeric(
        result["close"],
        errors="coerce",
    )

    return result.dropna(
        subset=required
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


def empty_curve_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=CURVE_COLUMNS
    )

