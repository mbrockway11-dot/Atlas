"""Backtest adapter for historical Atlas alpha-engine signals."""

from __future__ import annotations

import math

import pandas as pd


TRADE_COLUMNS = [
    "engine_id",
    "engine_version",
    "family",
    "timestamp",
    "date",
    "exit_timestamp",
    "asset",
    "direction",
    "signal",
    "holding_period",
    "entry_close",
    "exit_close",
    "forward_return",
    "strategy_return",
    "normalized_score",
    "confidence",
    "conviction",
    "regime",
    "reason_codes",
]


def build_engine_trades(
    signals: pd.DataFrame,
    market: pd.DataFrame,
) -> pd.DataFrame:
    """Convert historical signals into direction-adjusted trades."""
    if (
        signals is None
        or signals.empty
        or market is None
        or market.empty
    ):
        return pd.DataFrame(
            columns=TRADE_COLUMNS
        )

    signal_frame = signals.copy()

    signal_frame["timestamp"] = pd.to_datetime(
        signal_frame["timestamp"],
        errors="coerce",
        utc=True,
    )

    signal_frame["asset"] = (
        signal_frame["asset"]
        .astype(str)
    )

    signal_frame = signal_frame.dropna(
        subset=[
            "timestamp",
            "asset",
        ]
    )

    prices = market[
        [
            "timestamp",
            "asset",
            "close",
        ]
    ].copy()

    prices["timestamp"] = pd.to_datetime(
        prices["timestamp"],
        errors="coerce",
        utc=True,
    )

    prices["asset"] = (
        prices["asset"]
        .astype(str)
    )

    prices["close"] = pd.to_numeric(
        prices["close"],
        errors="coerce",
    )

    prices = prices.dropna(
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
    )

    frames: list[pd.DataFrame] = []

    for hold in sorted(
        signal_frame["holding_period"]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    ):
        hold_signals = signal_frame[
            signal_frame["holding_period"].astype(int).eq(
                hold
            )
        ].copy()

        hold_prices = prices.copy()

        hold_prices["exit_timestamp"] = (
            hold_prices.groupby(
                "asset"
            )["timestamp"]
            .shift(-hold)
        )

        hold_prices["exit_close"] = (
            hold_prices.groupby(
                "asset"
            )["close"]
            .shift(-hold)
        )

        hold_prices["forward_return"] = (
            hold_prices["exit_close"]
            / hold_prices["close"]
            - 1.0
        )

        joined = hold_signals.merge(
            hold_prices[
                [
                    "timestamp",
                    "asset",
                    "close",
                    "exit_timestamp",
                    "exit_close",
                    "forward_return",
                ]
            ],
            on=[
                "timestamp",
                "asset",
            ],
            how="left",
        )

        joined = joined.rename(
            columns={
                "close": "entry_close",
            }
        )

        joined["strategy_return"] = (
            joined.apply(
                direction_adjusted_return,
                axis=1,
            )
        )

        frames.append(joined)

    if not frames:
        return pd.DataFrame(
            columns=TRADE_COLUMNS
        )

    trades = pd.concat(
        frames,
        ignore_index=True,
    )

    trades = trades[
        trades["direction"].isin(
            [
                "LONG",
                "SHORT",
            ]
        )
    ].copy()

    trades = trades.dropna(
        subset=[
            "entry_close",
            "exit_close",
            "forward_return",
            "strategy_return",
        ]
    )

    trades["date"] = trades["timestamp"]

    for column in TRADE_COLUMNS:
        if column not in trades.columns:
            trades[column] = None

    return trades[
        TRADE_COLUMNS
    ].sort_values(
        [
            "engine_id",
            "asset",
            "timestamp",
        ],
        kind="stable",
    ).reset_index(drop=True)


def direction_adjusted_return(
    row: pd.Series,
) -> float:
    """Apply signal direction to the observed forward return."""
    value = row.get("forward_return")

    try:
        result = float(value)
    except (TypeError, ValueError):
        return float("nan")

    if not math.isfinite(result):
        return float("nan")

    direction = str(
        row.get("direction", "")
    ).upper()

    if direction == "SHORT":
        return -result

    if direction == "LONG":
        return result

    return float("nan")


def non_overlapping_engine_trades(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    """Keep non-overlapping trades per engine and asset."""
    if trades is None or trades.empty:
        return pd.DataFrame(
            columns=TRADE_COLUMNS
        )

    working = trades.copy()

    working["timestamp"] = pd.to_datetime(
        working["timestamp"],
        errors="coerce",
        utc=True,
    )

    working = working.dropna(
        subset=[
            "timestamp",
            "engine_id",
            "asset",
        ]
    ).sort_values(
        [
            "engine_id",
            "asset",
            "timestamp",
        ],
        kind="stable",
    )

    accepted: list[pd.Series] = []

    for (
        engine_id,
        asset,
    ), group in working.groupby(
        [
            "engine_id",
            "asset",
        ],
        sort=True,
    ):
        next_allowed = None

        for _, row in group.iterrows():
            timestamp = row["timestamp"]

            exit_timestamp = pd.to_datetime(
                row.get("exit_timestamp"),
                errors="coerce",
                utc=True,
            )

            if (
                next_allowed is None
                or timestamp >= next_allowed
            ):
                accepted.append(row)

                next_allowed = (
                    exit_timestamp
                    if not pd.isna(exit_timestamp)
                    else timestamp
                )

    if not accepted:
        return pd.DataFrame(
            columns=TRADE_COLUMNS
        )

    return pd.DataFrame(
        accepted
    )[TRADE_COLUMNS].reset_index(
        drop=True
    )


def summarize_engine_performance(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    """Summarize observed historical engine performance."""
    columns = [
        "engine_id",
        "family",
        "trade_count",
        "asset_count",
        "win_rate",
        "mean_return",
        "median_return",
        "return_std",
        "profit_factor",
        "cumulative_return",
        "best_trade",
        "worst_trade",
    ]

    if trades is None or trades.empty:
        return pd.DataFrame(columns=columns)

    rows: list[dict] = []

    for engine_id, group in trades.groupby(
        "engine_id",
        sort=True,
    ):
        returns = pd.to_numeric(
            group["strategy_return"],
            errors="coerce",
        ).dropna()

        if returns.empty:
            continue

        positive = returns[
            returns > 0
        ].sum()

        negative = abs(
            returns[
                returns < 0
            ].sum()
        )

        profit_factor = (
            float(positive / negative)
            if negative > 0
            else None
        )

        cumulative = float(
            (1.0 + returns)
            .clip(lower=0.0)
            .prod()
            - 1.0
        )

        rows.append({
            "engine_id": engine_id,
            "family": str(
                group["family"].iloc[0]
            ),
            "trade_count": int(
                len(returns)
            ),
            "asset_count": int(
                group["asset"].nunique()
            ),
            "win_rate": round(
                float(
                    (returns > 0).mean()
                ),
                8,
            ),
            "mean_return": round(
                float(returns.mean()),
                8,
            ),
            "median_return": round(
                float(returns.median()),
                8,
            ),
            "return_std": round(
                float(
                    returns.std(
                        ddof=0
                    )
                ),
                8,
            ),
            "profit_factor": (
                round(
                    profit_factor,
                    8,
                )
                if profit_factor is not None
                else None
            ),
            "cumulative_return": round(
                cumulative,
                8,
            ),
            "best_trade": round(
                float(returns.max()),
                8,
            ),
            "worst_trade": round(
                float(returns.min()),
                8,
            ),
        })

    return pd.DataFrame(
        rows,
        columns=columns,
    )


