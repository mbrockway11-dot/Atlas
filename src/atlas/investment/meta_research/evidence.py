"""Meta Research Engine v1 evidence normalization."""

from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.meta_research.config import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
)


def build_research_evidence(
    trades: pd.DataFrame,
    market_history: pd.DataFrame,
) -> pd.DataFrame:
    """Join realized trades to contemporaneous market features."""
    normalized_trades = normalize_trades(
        trades
    )

    market = normalize_market_history(
        market_history
    )

    if normalized_trades.empty:
        return pd.DataFrame()

    if market.empty:
        return normalized_trades

    feature_columns = [
        column
        for column in (
            FEATURE_COLUMNS
            + CATEGORICAL_COLUMNS
        )
        if column in market.columns
        and column not in {
            "direction",
            "regime",
        }
    ]

    market_slice = market[
        [
            "timestamp",
            "asset",
            *feature_columns,
        ]
    ].copy()

    evidence = normalized_trades.merge(
        market_slice,
        on=[
            "timestamp",
            "asset",
        ],
        how="left",
        suffixes=(
            "",
            "_market",
        ),
    )

    for column in CATEGORICAL_COLUMNS:
        market_column = (
            f"{column}_market"
        )

        if (
            column not in evidence.columns
            and market_column
            in evidence.columns
        ):
            evidence[column] = evidence[
                market_column
            ]

    evidence["winning_trade"] = (
        evidence["strategy_return"] > 0
    )

    evidence["losing_trade"] = (
        evidence["strategy_return"] < 0
    )

    evidence["return_sign"] = np.where(
        evidence["strategy_return"] > 0,
        "WIN",
        np.where(
            evidence[
                "strategy_return"
            ] < 0,
            "LOSS",
            "FLAT",
        ),
    )

    evidence["calendar_year"] = (
        evidence["timestamp"].dt.year
    )

    evidence["calendar_quarter"] = (
        evidence["timestamp"]
        .dt.to_period("Q")
        .astype(str)
    )

    return evidence.sort_values(
        [
            "engine_id",
            "timestamp",
            "asset",
        ],
        kind="stable",
    ).reset_index(drop=True)


def normalize_trades(
    trades: pd.DataFrame,
) -> pd.DataFrame:
    if trades is None or trades.empty:
        return pd.DataFrame()

    required = {
        "engine_id",
        "asset",
        "strategy_return",
    }

    if not required.issubset(
        trades.columns
    ):
        return pd.DataFrame()

    frame = trades.copy()

    temporal = find_temporal_column(
        frame
    )

    if temporal is None:
        return pd.DataFrame()

    frame["timestamp"] = pd.to_datetime(
        frame[temporal],
        errors="coerce",
        utc=True,
    )

    frame["engine_id"] = (
        frame["engine_id"]
        .astype(str)
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    if "family" not in frame.columns:
        frame["family"] = "unknown"

    frame["family"] = (
        frame["family"]
        .fillna("unknown")
        .astype(str)
    )

    if "direction" not in frame.columns:
        frame["direction"] = "UNKNOWN"

    if "regime" not in frame.columns:
        frame["regime"] = "UNKNOWN"

    for column in [
        "strategy_return",
        "forward_return",
        "normalized_score",
        "confidence",
        "conviction",
        "holding_period",
    ]:
        if column not in frame.columns:
            frame[column] = np.nan

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "engine_id",
            "asset",
            "strategy_return",
        ]
    )

    return frame


def normalize_market_history(
    market: pd.DataFrame,
) -> pd.DataFrame:
    if market is None or market.empty:
        return pd.DataFrame()

    required = {
        "asset",
    }

    if not required.issubset(
        market.columns
    ):
        return pd.DataFrame()

    frame = market.copy()

    temporal = find_temporal_column(
        frame
    )

    if temporal is None:
        return pd.DataFrame()

    frame["timestamp"] = pd.to_datetime(
        frame[temporal],
        errors="coerce",
        utc=True,
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    for column in FEATURE_COLUMNS:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "asset",
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

    return frame


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
