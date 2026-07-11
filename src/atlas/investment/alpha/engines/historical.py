"""Historical execution for Atlas Alpha Engine Framework v1."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.investment.alpha.backtester.schema import (
    filter_approved_assets,
    normalize_market_frame,
)
from atlas.investment.alpha.engines.schema import (
    empty_signal_frame,
    normalize_signal_output,
)


HISTORICAL_FEATURES_PATH = Path(
    "output/investment_alpha/market_feature_history.csv"
)

APPROVED_UNIVERSE_PATH = Path(
    "output/investment_market_universe/approved_universe.csv"
)


def load_historical_market_features(
    *,
    history_path: str | Path = HISTORICAL_FEATURES_PATH,
    approved_universe_path: str | Path = APPROVED_UNIVERSE_PATH,
) -> pd.DataFrame:
    """Load and enrich historical Market Features v2 rows."""
    history_path = Path(history_path)
    approved_universe_path = Path(
        approved_universe_path
    )

    if (
        not history_path.exists()
        or not history_path.is_file()
        or history_path.stat().st_size == 0
    ):
        return pd.DataFrame()

    market = pd.read_csv(history_path)
    market = normalize_market_frame(market)

    if (
        approved_universe_path.exists()
        and approved_universe_path.is_file()
        and approved_universe_path.stat().st_size > 0
    ):
        approved = pd.read_csv(
            approved_universe_path
        )
    else:
        approved = pd.DataFrame()

    market = filter_approved_assets(
        market,
        approved,
    )

    market = add_historical_cross_sectional_features(
        market
    )

    return market.reset_index(drop=True)


def add_historical_cross_sectional_features(
    market: pd.DataFrame,
) -> pd.DataFrame:
    """Build deterministic cross-sectional metrics per timestamp."""
    if market is None or market.empty:
        return pd.DataFrame()

    result = market.copy()

    momentum_30 = numeric_series(
        result,
        "momentum_30d",
    )
    momentum_90 = numeric_series(
        result,
        "momentum_90d",
    )
    return_14 = numeric_series(
        result,
        "return_14d",
    )
    return_30 = numeric_series(
        result,
        "return_30d",
    )

    result["momentum_30d_percentile"] = (
        percentile_by_timestamp(
            result,
            momentum_30,
        )
    )

    result["momentum_90d_percentile"] = (
        percentile_by_timestamp(
            result,
            momentum_90,
        )
    )

    result["return_14d_percentile"] = (
        percentile_by_timestamp(
            result,
            return_14,
        )
    )

    result["return_30d_percentile"] = (
        percentile_by_timestamp(
            result,
            return_30,
        )
    )

    percentile_columns = [
        "momentum_30d_percentile",
        "momentum_90d_percentile",
        "return_14d_percentile",
        "return_30d_percentile",
    ]

    result["cross_sectional_score"] = (
        result[percentile_columns]
        .mean(
            axis=1,
            skipna=True,
        )
    )

    result["cross_sectional_rank"] = (
        result.groupby(
            "timestamp"
        )["cross_sectional_score"]
        .rank(
            method="first",
            ascending=False,
        )
    )

    asset_count = (
        result.groupby(
            "timestamp"
        )["asset"]
        .transform("count")
        .clip(lower=1)
    )

    result["cross_sectional_percentile"] = (
        1.0
        - (
            result["cross_sectional_rank"] - 1.0
        )
        / asset_count.clip(lower=1)
    )

    result["cross_sectional_percentile"] = (
        result["cross_sectional_percentile"]
        .clip(0.0, 1.0)
    )

    return result


def numeric_series(
    frame: pd.DataFrame,
    column: str,
) -> pd.Series:
    """Return a numeric series aligned to the input frame."""
    if column not in frame.columns:
        return pd.Series(
            float("nan"),
            index=frame.index,
            dtype=float,
        )

    return pd.to_numeric(
        frame[column],
        errors="coerce",
    )


def percentile_by_timestamp(
    frame: pd.DataFrame,
    values: pd.Series,
) -> pd.Series:
    """Compute cross-sectional percentile ranks by timestamp."""
    working = pd.DataFrame({
        "timestamp": frame["timestamp"],
        "value": values,
    })

    return (
        working.groupby(
            "timestamp"
        )["value"]
        .rank(
            method="average",
            pct=True,
            ascending=True,
        )
    )


def run_historical_engines(
    market: pd.DataFrame,
    engines,
) -> pd.DataFrame:
    """Run registered engines over historical Market Features."""
    if market is None or market.empty:
        return empty_signal_frame()

    frames: list[pd.DataFrame] = []

    for engine in engines:
        signals = engine.run(market)

        if not signals.empty:
            frames.append(signals)

    if not frames:
        return empty_signal_frame()

    return normalize_signal_output(
        pd.concat(
            frames,
            ignore_index=True,
        )
    )
