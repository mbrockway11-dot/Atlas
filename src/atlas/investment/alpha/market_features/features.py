
"""Market Features v2 feature engineering."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


RETURN_WINDOWS = [1, 3, 7, 14, 30, 90]
VOLATILITY_WINDOWS = [7, 14, 30, 90]
MOMENTUM_WINDOWS = [7, 14, 30, 90]
AVERAGE_WINDOWS = [7, 14, 30, 50, 100, 200]


def build_feature_frame(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return empty_feature_frame()

    frames = []

    for asset, group in prices.groupby("asset", sort=True):
        asset_frame = build_asset_history(
            group.copy(),
            asset=str(asset),
        )

        if not asset_frame.empty:
            frames.append(asset_frame)

    if not frames:
        return empty_feature_frame()

    combined = pd.concat(frames, ignore_index=True)

    return combined.sort_values(
        ["timestamp", "asset"],
        kind="stable",
    ).reset_index(drop=True)


def build_asset_history(
    frame: pd.DataFrame,
    *,
    asset: str,
) -> pd.DataFrame:
    frame = frame.sort_values(
        "timestamp",
        kind="stable",
    ).copy()

    close = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )
    high = pd.to_numeric(
        frame["high"],
        errors="coerce",
    )
    low = pd.to_numeric(
        frame["low"],
        errors="coerce",
    )
    volume = pd.to_numeric(
        frame["volume"],
        errors="coerce",
    ).fillna(0.0)

    frame["asset"] = asset
    frame["return_1d"] = close.pct_change(
        fill_method=None
    )

    for window in RETURN_WINDOWS:
        frame[f"return_{window}d"] = close.pct_change(
            periods=window,
            fill_method=None,
        )

    for window in VOLATILITY_WINDOWS:
        frame[f"volatility_{window}d"] = (
            frame["return_1d"]
            .rolling(window, min_periods=max(3, window // 2))
            .std(ddof=0)
            * math.sqrt(365.0)
        )

    for window in MOMENTUM_WINDOWS:
        frame[f"momentum_{window}d"] = (
            close / close.shift(window) - 1.0
        )

    for window in AVERAGE_WINDOWS:
        moving_average = close.rolling(
            window,
            min_periods=max(3, window // 2),
        ).mean()

        frame[f"sma_{window}d"] = moving_average
        frame[f"distance_sma_{window}d"] = (
            close / moving_average - 1.0
        )

    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    frame["atr_14d"] = true_range.rolling(
        14,
        min_periods=7,
    ).mean()

    frame["atr_pct_14d"] = np.where(
        close != 0,
        frame["atr_14d"] / close,
        np.nan,
    )

    frame["volume_average_30d"] = volume.rolling(
        30,
        min_periods=10,
    ).mean()

    frame["volume_ratio_30d"] = np.where(
        frame["volume_average_30d"] > 0,
        volume / frame["volume_average_30d"],
        np.nan,
    )

    dollar_volume = pd.to_numeric(
        frame["dollar_volume"],
        errors="coerce",
    ).fillna(0.0)

    frame["dollar_volume_average_30d"] = (
        dollar_volume.rolling(
            30,
            min_periods=10,
        ).mean()
    )

    frame["dollar_volume_median_30d"] = (
        dollar_volume.rolling(
            30,
            min_periods=10,
        ).median()
    )

    rolling_high = close.rolling(
        90,
        min_periods=30,
    ).max()

    frame["drawdown_from_90d_high"] = np.where(
        rolling_high > 0,
        close / rolling_high - 1.0,
        np.nan,
    )

    frame["trend_state"] = build_trend_state(frame)
    frame["volatility_state"] = build_volatility_state(frame)
    frame["liquidity_state"] = build_liquidity_state(frame)
    frame["source"] = "market_features_v2_market_universe"

    return frame


def build_trend_state(frame: pd.DataFrame) -> pd.Series:
    momentum = pd.to_numeric(
        frame.get("momentum_30d"),
        errors="coerce",
    )
    distance = pd.to_numeric(
        frame.get("distance_sma_50d"),
        errors="coerce",
    )

    conditions = [
        (momentum > 0.05) & (distance > 0.0),
        (momentum < -0.05) & (distance < 0.0),
    ]

    choices = [
        "UPTREND",
        "DOWNTREND",
    ]

    return pd.Series(
        np.select(
            conditions,
            choices,
            default="NEUTRAL",
        ),
        index=frame.index,
    )


def build_volatility_state(
    frame: pd.DataFrame,
) -> pd.Series:
    volatility = pd.to_numeric(
        frame.get("volatility_30d"),
        errors="coerce",
    )

    median = volatility.expanding(
        min_periods=30,
    ).median()

    conditions = [
        volatility > median * 1.35,
        volatility < median * 0.75,
    ]

    return pd.Series(
        np.select(
            conditions,
            ["HIGH", "LOW"],
            default="NORMAL",
        ),
        index=frame.index,
    )


def build_liquidity_state(
    frame: pd.DataFrame,
) -> pd.Series:
    ratio = pd.to_numeric(
        frame.get("volume_ratio_30d"),
        errors="coerce",
    )

    conditions = [
        ratio >= 1.50,
        ratio <= 0.60,
    ]

    return pd.Series(
        np.select(
            conditions,
            ["EXPANDING", "CONTRACTING"],
            default="NORMAL",
        ),
        index=frame.index,
    )


def build_latest_asset_features(
    history: pd.DataFrame,
) -> pd.DataFrame:
    if history is None or history.empty:
        return empty_latest_frame()

    latest = (
        history.sort_values(
            ["asset", "timestamp"],
            kind="stable",
        )
        .groupby("asset", as_index=False)
        .tail(1)
        .copy()
    )

    latest = add_cross_sectional_features(latest)

    return latest.sort_values(
        [
            "cross_sectional_rank",
            "asset",
        ],
        kind="stable",
    ).reset_index(drop=True)


def add_cross_sectional_features(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return frame

    result = frame.copy()

    rank_inputs = [
        "momentum_30d",
        "momentum_90d",
        "return_14d",
        "return_30d",
    ]

    available = [
        column
        for column in rank_inputs
        if column in result.columns
    ]

    percentile_columns = []

    for column in available:
        percentile_column = f"{column}_percentile"
        result[percentile_column] = (
            pd.to_numeric(
                result[column],
                errors="coerce",
            )
            .rank(
                pct=True,
                method="average",
            )
            .fillna(0.5)
        )
        percentile_columns.append(percentile_column)

    volatility = pd.to_numeric(
        result.get("volatility_30d"),
        errors="coerce",
    )

    volatility_percentile = volatility.rank(
        pct=True,
        method="average",
    ).fillna(0.5)

    if percentile_columns:
        momentum_component = result[
            percentile_columns
        ].mean(axis=1)
    else:
        momentum_component = pd.Series(
            0.5,
            index=result.index,
        )

    result["cross_sectional_score"] = (
        momentum_component * 0.80
        + (1.0 - volatility_percentile) * 0.20
    ).clip(0.0, 1.0)

    result["cross_sectional_rank"] = (
        result["cross_sectional_score"]
        .rank(
            ascending=False,
            method="first",
        )
        .astype(int)
    )

    asset_count = max(1, len(result))

    result["cross_sectional_percentile"] = (
        1.0
        - (
            result["cross_sectional_rank"] - 1
        )
        / asset_count
    )

    return result


def build_market_aggregate(
    latest: pd.DataFrame,
) -> dict:
    if latest is None or latest.empty:
        return {
            "asset_count": 0,
            "positive_1d_count": 0,
            "positive_7d_count": 0,
            "positive_30d_count": 0,
            "uptrend_count": 0,
            "downtrend_count": 0,
            "breadth_1d": 0.0,
            "breadth_7d": 0.0,
            "breadth_30d": 0.0,
            "median_return_1d": 0.0,
            "median_return_7d": 0.0,
            "median_return_30d": 0.0,
            "median_volatility_30d": 0.0,
            "market_regime": "NO_DATA",
        }

    count = len(latest)

    return_1d = numeric(latest, "return_1d")
    return_7d = numeric(latest, "return_7d")
    return_30d = numeric(latest, "return_30d")

    positive_1d = int((return_1d > 0).sum())
    positive_7d = int((return_7d > 0).sum())
    positive_30d = int((return_30d > 0).sum())

    breadth_1d = positive_1d / count
    breadth_7d = positive_7d / count
    breadth_30d = positive_30d / count

    uptrend_count = int(
        (latest["trend_state"] == "UPTREND").sum()
    )
    downtrend_count = int(
        (latest["trend_state"] == "DOWNTREND").sum()
    )

    market_regime = classify_market_regime(
        breadth_30d=breadth_30d,
        median_return_30d=safe_median(return_30d),
        uptrend_ratio=uptrend_count / count,
        downtrend_ratio=downtrend_count / count,
    )

    return {
        "asset_count": count,
        "positive_1d_count": positive_1d,
        "positive_7d_count": positive_7d,
        "positive_30d_count": positive_30d,
        "uptrend_count": uptrend_count,
        "downtrend_count": downtrend_count,
        "breadth_1d": round(breadth_1d, 6),
        "breadth_7d": round(breadth_7d, 6),
        "breadth_30d": round(breadth_30d, 6),
        "median_return_1d": round(
            safe_median(return_1d),
            6,
        ),
        "median_return_7d": round(
            safe_median(return_7d),
            6,
        ),
        "median_return_30d": round(
            safe_median(return_30d),
            6,
        ),
        "median_volatility_30d": round(
            safe_median(
                numeric(latest, "volatility_30d")
            ),
            6,
        ),
        "market_regime": market_regime,
    }


def classify_market_regime(
    *,
    breadth_30d: float,
    median_return_30d: float,
    uptrend_ratio: float,
    downtrend_ratio: float,
) -> str:
    if (
        breadth_30d >= 0.70
        and median_return_30d > 0.05
        and uptrend_ratio >= 0.60
    ):
        return "BROAD_RISK_ON"

    if (
        breadth_30d <= 0.30
        and median_return_30d < -0.05
        and downtrend_ratio >= 0.60
    ):
        return "BROAD_RISK_OFF"

    if breadth_30d >= 0.60:
        return "SELECTIVE_RISK_ON"

    if breadth_30d <= 0.40:
        return "SELECTIVE_RISK_OFF"

    return "MIXED"


def numeric(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    if column not in frame.columns:
        return pd.Series(
            0.0,
            index=frame.index,
            dtype=float,
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    )


def safe_median(series: pd.Series) -> float:
    clean = series.dropna()

    if clean.empty:
        return 0.0

    return float(clean.median())


def empty_feature_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "timestamp",
            "asset",
            "close",
            "return_1d",
            "return_7d",
            "return_30d",
            "volatility_30d",
            "momentum_30d",
            "trend_state",
            "volatility_state",
            "liquidity_state",
            "source",
        ]
    )


def empty_latest_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "timestamp",
            "asset",
            "close",
            "return_1d",
            "return_7d",
            "return_30d",
            "volatility_30d",
            "momentum_30d",
            "trend_state",
            "volatility_state",
            "liquidity_state",
            "cross_sectional_score",
            "cross_sectional_rank",
            "cross_sectional_percentile",
            "source",
        ]
    )
