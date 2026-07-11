"""Observed performance metrics for Atlas Alpha Research Lab v1."""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd


METRIC_COLUMNS = [
    "engine_id",
    "family",
    "trade_count",
    "asset_count",
    "first_timestamp",
    "last_timestamp",
    "win_rate",
    "mean_return",
    "median_return",
    "return_std",
    "downside_deviation",
    "trade_sharpe",
    "trade_sortino",
    "profit_factor",
    "expectancy",
    "event_count",
    "event_mean_return",
    "event_cumulative_return",
    "max_drawdown",
    "recovery_factor",
    "best_trade",
    "worst_trade",
    "largest_asset_share",
    "positive_asset_ratio",
    "positive_year_ratio",
    "positive_regime_ratio",
]


def build_engine_metrics(
    trades: pd.DataFrame,
    *,
    transaction_cost_bps: float = 10.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Build engine metrics and timestamp-level equal-notional curves."""
    if trades is None or trades.empty:
        return (
            pd.DataFrame(columns=METRIC_COLUMNS),
            empty_curve_frame(),
        )

    working = normalize_trades(
        trades,
        transaction_cost_bps=transaction_cost_bps,
    )

    if working.empty:
        return (
            pd.DataFrame(columns=METRIC_COLUMNS),
            empty_curve_frame(),
        )

    metric_rows: list[dict[str, Any]] = []
    curve_frames: list[pd.DataFrame] = []

    for engine_id, group in working.groupby(
        "engine_id",
        sort=True,
    ):
        returns = group["net_return"].dropna()

        if returns.empty:
            continue

        event_returns = (
            group.groupby(
                "timestamp",
                sort=True,
            )["net_return"]
            .mean()
            .rename("event_return")
            .reset_index()
        )

        event_curve = build_event_curve(
            engine_id,
            event_returns,
        )

        curve_frames.append(event_curve)

        max_drawdown = safe_float(
            event_curve["drawdown"].min()
            if not event_curve.empty
            else 0.0
        )

        cumulative_return = safe_float(
            event_curve["equity"].iloc[-1] - 1.0
            if not event_curve.empty
            else 0.0
        )

        recovery_factor = (
            cumulative_return / abs(max_drawdown)
            if max_drawdown < 0
            else None
        )

        asset_metrics = grouped_segment_metrics(
            group,
            "asset",
        )
        year_metrics = grouped_segment_metrics(
            group.assign(
                year=group["timestamp"].dt.year
            ),
            "year",
        )
        regime_metrics = grouped_segment_metrics(
            group,
            "regime",
        )

        asset_counts = group[
            "asset"
        ].value_counts()

        largest_asset_share = (
            float(asset_counts.max() / len(group))
            if len(group)
            else 0.0
        )

        metric_rows.append({
            "engine_id": engine_id,
            "family": first_text(
                group,
                "family",
                default="unknown",
            ),
            "trade_count": int(len(returns)),
            "asset_count": int(
                group["asset"].nunique()
            ),
            "first_timestamp": str(
                group["timestamp"].min()
            ),
            "last_timestamp": str(
                group["timestamp"].max()
            ),
            "win_rate": round(
                float((returns > 0).mean()),
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
                safe_std(returns),
                8,
            ),
            "downside_deviation": round(
                downside_deviation(returns),
                8,
            ),
            "trade_sharpe": optional_round(
                trade_sharpe(returns)
            ),
            "trade_sortino": optional_round(
                trade_sortino(returns)
            ),
            "profit_factor": optional_round(
                profit_factor(returns)
            ),
            "expectancy": round(
                expectancy(returns),
                8,
            ),
            "event_count": int(
                len(event_curve)
            ),
            "event_mean_return": round(
                safe_float(
                    event_returns[
                        "event_return"
                    ].mean()
                ),
                8,
            ),
            "event_cumulative_return": round(
                cumulative_return,
                8,
            ),
            "max_drawdown": round(
                max_drawdown,
                8,
            ),
            "recovery_factor": optional_round(
                recovery_factor
            ),
            "best_trade": round(
                safe_float(returns.max()),
                8,
            ),
            "worst_trade": round(
                safe_float(returns.min()),
                8,
            ),
            "largest_asset_share": round(
                largest_asset_share,
                8,
            ),
            "positive_asset_ratio": round(
                positive_segment_ratio(
                    asset_metrics
                ),
                8,
            ),
            "positive_year_ratio": round(
                positive_segment_ratio(
                    year_metrics
                ),
                8,
            ),
            "positive_regime_ratio": round(
                positive_segment_ratio(
                    regime_metrics
                ),
                8,
            ),
        })

    metrics = pd.DataFrame(
        metric_rows,
        columns=METRIC_COLUMNS,
    )

    curves = (
        pd.concat(
            curve_frames,
            ignore_index=True,
        )
        if curve_frames
        else empty_curve_frame()
    )

    return metrics, curves


def normalize_trades(
    trades: pd.DataFrame,
    *,
    transaction_cost_bps: float,
) -> pd.DataFrame:
    """Normalize non-overlapping historical trade rows."""
    result = trades.copy()

    required = [
        "engine_id",
        "timestamp",
        "asset",
        "strategy_return",
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

    result["strategy_return"] = pd.to_numeric(
        result["strategy_return"],
        errors="coerce",
    )

    result["asset"] = result[
        "asset"
    ].astype(str)

    result["engine_id"] = result[
        "engine_id"
    ].astype(str)

    if "family" not in result.columns:
        result["family"] = "unknown"

    if "regime" not in result.columns:
        result["regime"] = "UNKNOWN"

    cost = float(
        transaction_cost_bps
    ) / 10_000.0

    result["net_return"] = (
        result["strategy_return"]
        - cost
    )

    return result.dropna(
        subset=[
            "engine_id",
            "timestamp",
            "asset",
            "net_return",
        ]
    ).sort_values(
        [
            "engine_id",
            "timestamp",
            "asset",
        ],
        kind="stable",
    ).reset_index(drop=True)


def build_event_curve(
    engine_id: str,
    event_returns: pd.DataFrame,
) -> pd.DataFrame:
    """Build an equal-notional timestamp-level engine curve."""
    if event_returns.empty:
        return empty_curve_frame()

    curve = event_returns.copy()

    curve["event_return"] = pd.to_numeric(
        curve["event_return"],
        errors="coerce",
    ).fillna(0.0)

    curve["equity"] = (
        1.0
        + curve["event_return"].clip(
            lower=-0.999999
        )
    ).cumprod()

    curve["running_peak"] = (
        curve["equity"].cummax()
    )

    curve["drawdown"] = (
        curve["equity"]
        / curve["running_peak"]
        - 1.0
    )

    curve.insert(
        0,
        "engine_id",
        str(engine_id),
    )

    return curve[
        [
            "engine_id",
            "timestamp",
            "event_return",
            "equity",
            "running_peak",
            "drawdown",
        ]
    ]


def grouped_segment_metrics(
    frame: pd.DataFrame,
    column: str,
) -> pd.DataFrame:
    """Summarize average net returns by a segment."""
    if (
        column not in frame.columns
        or frame.empty
    ):
        return pd.DataFrame(
            columns=[
                "segment",
                "trade_count",
                "mean_return",
            ]
        )

    return (
        frame.groupby(
            column,
            dropna=False,
            sort=True,
        )["net_return"]
        .agg(
            trade_count="count",
            mean_return="mean",
        )
        .reset_index()
        .rename(
            columns={
                column: "segment",
            }
        )
    )


def positive_segment_ratio(
    segments: pd.DataFrame,
) -> float:
    """Return the share of observed segments with positive mean return."""
    if segments is None or segments.empty:
        return 0.0

    values = pd.to_numeric(
        segments["mean_return"],
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    return float(
        (values > 0).mean()
    )


def expectancy(
    returns: pd.Series,
) -> float:
    """Observed expectancy per trade."""
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    if values.empty:
        return 0.0

    wins = values[
        values > 0
    ]
    losses = values[
        values <= 0
    ]

    win_rate = float(
        len(wins) / len(values)
    )

    average_win = (
        float(wins.mean())
        if not wins.empty
        else 0.0
    )

    average_loss = (
        abs(float(losses.mean()))
        if not losses.empty
        else 0.0
    )

    return (
        win_rate * average_win
        - (1.0 - win_rate) * average_loss
    )


def profit_factor(
    returns: pd.Series,
) -> float | None:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    gains = float(
        values[
            values > 0
        ].sum()
    )

    losses = abs(
        float(
            values[
                values < 0
            ].sum()
        )
    )

    if losses <= 0:
        return None

    return gains / losses


def trade_sharpe(
    returns: pd.Series,
) -> float | None:
    """Non-annualized Sharpe ratio across observed trades."""
    std = safe_std(returns)

    if std <= 0:
        return None

    return safe_float(
        returns.mean()
    ) / std


def downside_deviation(
    returns: pd.Series,
) -> float:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).dropna()

    downside = values[
        values < 0
    ]

    if downside.empty:
        return 0.0

    return float(
        np.sqrt(
            np.mean(
                np.square(downside)
            )
        )
    )


def trade_sortino(
    returns: pd.Series,
) -> float | None:
    """Non-annualized Sortino ratio across observed trades."""
    downside = downside_deviation(
        returns
    )

    if downside <= 0:
        return None

    return safe_float(
        returns.mean()
    ) / downside


def safe_std(
    values: pd.Series,
) -> float:
    result = float(
        pd.to_numeric(
            values,
            errors="coerce",
        )
        .dropna()
        .std(
            ddof=0
        )
    )

    return (
        result
        if math.isfinite(result)
        else 0.0
    )


def safe_float(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def optional_round(
    value,
    digits: int = 8,
):
    if value is None:
        return None

    result = safe_float(
        value,
        default=float("nan"),
    )

    if not math.isfinite(result):
        return None

    return round(
        result,
        digits,
    )


def first_text(
    frame: pd.DataFrame,
    column: str,
    *,
    default: str,
) -> str:
    if (
        column not in frame.columns
        or frame.empty
    ):
        return default

    values = (
        frame[column]
        .dropna()
        .astype(str)
    )

    return (
        values.iloc[0]
        if not values.empty
        else default
    )


def empty_curve_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "engine_id",
            "timestamp",
            "event_return",
            "equity",
            "running_peak",
            "drawdown",
        ]
    )
