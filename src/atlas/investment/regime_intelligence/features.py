"""Historical market-state features for Regime Intelligence v1."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


STATE_COLUMNS = [
    "timestamp",
    "asset_count",
    "positive_1d_ratio",
    "positive_7d_ratio",
    "positive_30d_ratio",
    "uptrend_ratio",
    "downtrend_ratio",
    "median_return_1d",
    "median_return_7d",
    "median_return_30d",
    "median_momentum_30d",
    "median_momentum_90d",
    "median_volatility_7d",
    "median_volatility_30d",
    "volatility_ratio",
    "median_atr_pct_14d",
    "median_volume_ratio_30d",
    "median_drawdown_90d",
    "return_dispersion_1d",
    "return_dispersion_30d",
    "average_pairwise_correlation_30d",
    "cross_sectional_concentration",
]


def build_market_state_history(
    market: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate asset history into timestamp-level market states."""
    frame = normalize_market_history(
        market
    )

    if frame.empty:
        return pd.DataFrame(
            columns=STATE_COLUMNS
        )

    correlation_map = (
        rolling_market_correlation(frame)
    )

    rows: list[dict] = []

    for timestamp, group in frame.groupby(
        "timestamp",
        sort=True,
    ):
        return_1d = numeric_series(
            group,
            "return_1d",
        )

        return_7d = numeric_series(
            group,
            "return_7d",
        )

        return_30d = numeric_series(
            group,
            "return_30d",
        )

        momentum_30d = numeric_series(
            group,
            "momentum_30d",
        )

        momentum_90d = numeric_series(
            group,
            "momentum_90d",
        )

        volatility_7d = numeric_series(
            group,
            "volatility_7d",
        )

        volatility_30d = numeric_series(
            group,
            "volatility_30d",
        )

        atr_pct = numeric_series(
            group,
            "atr_pct_14d",
        )

        volume_ratio = numeric_series(
            group,
            "volume_ratio_30d",
        )

        drawdown = numeric_series(
            group,
            "drawdown_from_90d_high",
        )

        asset_count = int(
            group["asset"].nunique()
        )

        trend = (
            group.get(
                "trend_state",
                pd.Series(
                    index=group.index,
                    dtype=object,
                ),
            )
            .fillna("NEUTRAL")
            .astype(str)
            .str.upper()
        )

        concentration = (
            return_concentration(return_30d)
        )

        vol_ratio = safe_divide(
            median(volatility_7d),
            median(volatility_30d),
        )

        rows.append({
            "timestamp": timestamp,
            "asset_count": asset_count,
            "positive_1d_ratio": positive_ratio(
                return_1d
            ),
            "positive_7d_ratio": positive_ratio(
                return_7d
            ),
            "positive_30d_ratio": positive_ratio(
                return_30d
            ),
            "uptrend_ratio": float(
                trend.eq("UPTREND").mean()
            ),
            "downtrend_ratio": float(
                trend.eq("DOWNTREND").mean()
            ),
            "median_return_1d": median(
                return_1d
            ),
            "median_return_7d": median(
                return_7d
            ),
            "median_return_30d": median(
                return_30d
            ),
            "median_momentum_30d": median(
                momentum_30d
            ),
            "median_momentum_90d": median(
                momentum_90d
            ),
            "median_volatility_7d": median(
                volatility_7d
            ),
            "median_volatility_30d": median(
                volatility_30d
            ),
            "volatility_ratio": vol_ratio,
            "median_atr_pct_14d": median(
                atr_pct
            ),
            "median_volume_ratio_30d": median(
                volume_ratio
            ),
            "median_drawdown_90d": median(
                drawdown
            ),
            "return_dispersion_1d": dispersion(
                return_1d
            ),
            "return_dispersion_30d": dispersion(
                return_30d
            ),
            "average_pairwise_correlation_30d": (
                correlation_map.get(
                    timestamp,
                    0.0,
                )
            ),
            "cross_sectional_concentration": (
                concentration
            ),
        })

    result = pd.DataFrame(
        rows,
        columns=STATE_COLUMNS,
    )

    numeric = [
        column
        for column in STATE_COLUMNS
        if column != "timestamp"
    ]

    result[numeric] = result[numeric].round(
        8
    )

    return result


def normalize_market_history(
    market: pd.DataFrame,
) -> pd.DataFrame:
    if market is None or market.empty:
        return pd.DataFrame()

    frame = market.copy()

    temporal_column = None

    for candidate in [
        "timestamp",
        "date",
        "datetime",
        "time",
    ]:
        if candidate in frame.columns:
            temporal_column = candidate
            break

    if temporal_column is None:
        return pd.DataFrame()

    if (
        "asset" not in frame.columns
        or "close" not in frame.columns
    ):
        return pd.DataFrame()

    frame["timestamp"] = pd.to_datetime(
        frame[temporal_column],
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
    )

    return frame.sort_values(
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
    ).reset_index(drop=True)


def rolling_market_correlation(
    market: pd.DataFrame,
    *,
    window: int = 30,
) -> dict[pd.Timestamp, float]:
    """Calculate rolling average pairwise asset-return correlation."""
    pivot = market.pivot_table(
        index="timestamp",
        columns="asset",
        values="close",
        aggfunc="last",
    ).sort_index()

    returns = pivot.pct_change(
        fill_method=None
    )

    output: dict[pd.Timestamp, float] = {}

    for index in range(len(returns)):
        start = max(
            0,
            index - window + 1,
        )

        sample = returns.iloc[
            start:index + 1
        ]

        if len(sample) < 10:
            output[
                returns.index[index]
            ] = 0.0
            continue

        correlation = sample.corr(
            min_periods=5
        )

        if correlation.empty:
            output[
                returns.index[index]
            ] = 0.0
            continue

        values = correlation.to_numpy(
            dtype=float
        )

        upper = values[
            np.triu_indices_from(
                values,
                k=1,
            )
        ]

        upper = upper[
            np.isfinite(upper)
        ]

        output[
            returns.index[index]
        ] = (
            float(upper.mean())
            if len(upper)
            else 0.0
        )

    return output


def return_concentration(
    values: pd.Series,
) -> float:
    """Measure whether market return is concentrated in few assets."""
    values = (
        pd.to_numeric(
            values,
            errors="coerce",
        )
        .dropna()
        .abs()
    )

    total = float(values.sum())

    if total <= 0:
        return 0.0

    shares = values / total

    return float(
        (shares ** 2).sum()
    )


def numeric_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            dtype=float
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    ).dropna()


def positive_ratio(
    values: pd.Series,
) -> float:
    if values.empty:
        return 0.0

    return float(
        (values > 0).mean()
    )


def median(
    values: pd.Series,
) -> float:
    if values.empty:
        return 0.0

    result = float(
        values.median()
    )

    return (
        result
        if math.isfinite(result)
        else 0.0
    )


def dispersion(
    values: pd.Series,
) -> float:
    if values.empty:
        return 0.0

    result = float(
        values.std(
            ddof=0
        )
    )

    return (
        result
        if math.isfinite(result)
        else 0.0
    )


def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    if abs(denominator) <= 1e-12:
        return 0.0

    return float(
        numerator / denominator
    )
