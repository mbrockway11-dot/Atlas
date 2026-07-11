"""Historical data normalization for walk-forward reconstruction."""

from __future__ import annotations

import numpy as np
import pandas as pd


def normalize_market_history(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize market features into deterministic historical rows."""
    if frame is None or frame.empty:
        return pd.DataFrame()

    result = frame.copy()

    temporal = find_temporal_column(
        result
    )

    if (
        temporal is None
        or "asset" not in result.columns
        or "close" not in result.columns
    ):
        return pd.DataFrame()

    result["timestamp"] = pd.to_datetime(
        result[temporal],
        errors="coerce",
        utc=True,
    )

    result["asset"] = (
        result["asset"]
        .astype(str)
    )

    numeric_columns = [
        "close",
        "return_1d",
        "return_7d",
        "return_14d",
        "return_30d",
        "return_90d",
        "momentum_14d",
        "momentum_30d",
        "momentum_90d",
        "volatility_7d",
        "volatility_30d",
        "cross_sectional_score",
        "cross_sectional_rank",
        "cross_sectional_percentile",
    ]

    for column in numeric_columns:
        if column in result.columns:
            result[column] = pd.to_numeric(
                result[column],
                errors="coerce",
            )

    result["close"] = pd.to_numeric(
        result["close"],
        errors="coerce",
    )

    result = result.dropna(
        subset=[
            "timestamp",
            "asset",
            "close",
        ]
    ).sort_values(
        [
            "timestamp",
            "asset",
        ],
        kind="stable",
    ).drop_duplicates(
        subset=[
            "timestamp",
            "asset",
        ],
        keep="last",
    )

    result["date"] = (
        result["timestamp"]
        .dt.normalize()
    )

    return result.reset_index(
        drop=True
    )


def normalize_engine_signals(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize historical engine signals."""
    if frame is None or frame.empty:
        return pd.DataFrame()

    result = frame.copy()

    temporal = find_temporal_column(
        result
    )

    required = {
        "asset",
        "engine_id",
    }

    if (
        temporal is None
        or not required.issubset(
            result.columns
        )
    ):
        return pd.DataFrame()

    result["timestamp"] = pd.to_datetime(
        result[temporal],
        errors="coerce",
        utc=True,
    )

    result["date"] = (
        result["timestamp"]
        .dt.normalize()
    )

    result["asset"] = (
        result["asset"]
        .astype(str)
    )

    result["engine_id"] = (
        result["engine_id"]
        .astype(str)
    )

    if "normalized_score" not in result.columns:
        result["normalized_score"] = 0.5

    result["normalized_score"] = pd.to_numeric(
        result["normalized_score"],
        errors="coerce",
    ).fillna(0.5).clip(
        0.0,
        1.0,
    )

    if "confidence" not in result.columns:
        result["confidence"] = 1.0

    result["confidence"] = pd.to_numeric(
        result["confidence"],
        errors="coerce",
    ).fillna(0.0).clip(
        0.0,
        1.0,
    )

    return result.dropna(
        subset=[
            "timestamp",
            "date",
            "asset",
            "engine_id",
        ]
    ).sort_values(
        [
            "date",
            "asset",
            "engine_id",
        ],
        kind="stable",
    ).reset_index(
        drop=True
    )


def build_price_matrix(
    market: pd.DataFrame,
) -> pd.DataFrame:
    """Build canonical daily closing-price matrix."""
    if market.empty:
        return pd.DataFrame()

    return market.pivot_table(
        index="date",
        columns="asset",
        values="close",
        aggfunc="last",
    ).sort_index()


def build_return_matrix(
    prices: pd.DataFrame,
) -> pd.DataFrame:
    if prices.empty:
        return pd.DataFrame()

    return prices.pct_change(
        fill_method=None
    ).replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    )


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
