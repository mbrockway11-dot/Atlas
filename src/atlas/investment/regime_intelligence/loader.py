"""Regime Intelligence v1 input loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.errors import (
    EmptyDataError,
    ParserError,
)


MARKET_HISTORY = Path(
    "output/investment_alpha/"
    "market_feature_history.csv"
)

MARKET_LATEST = Path(
    "output/investment_alpha/"
    "market_features.csv"
)

MARKET_AGGREGATE = Path(
    "output/investment_alpha/"
    "market_aggregate_features.csv"
)

APPROVED_UNIVERSE = Path(
    "output/investment_market_universe/"
    "approved_universe.csv"
)

ALPHA_ENGINE_SUMMARY = Path(
    "output/investment_alpha_engines/"
    "alpha_engine_summary.csv"
)


def load_regime_inputs() -> dict[str, pd.DataFrame]:
    """Load market-state inputs safely."""
    return {
        "market_history": safe_read_csv(
            MARKET_HISTORY
        ),
        "market_latest": safe_read_csv(
            MARKET_LATEST
        ),
        "market_aggregate": safe_read_csv(
            MARKET_AGGREGATE
        ),
        "approved_universe": safe_read_csv(
            APPROVED_UNIVERSE
        ),
        "alpha_engine_summary": safe_read_csv(
            ALPHA_ENGINE_SUMMARY
        ),
    }


def safe_read_csv(
    path: str | Path,
) -> pd.DataFrame:
    target = Path(path)

    if (
        not target.exists()
        or not target.is_file()
        or target.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(target)
    except (
        EmptyDataError,
        ParserError,
        UnicodeDecodeError,
    ):
        return pd.DataFrame()

