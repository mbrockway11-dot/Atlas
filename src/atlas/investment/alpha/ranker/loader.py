
"""Cross-sectional alpha ranker loaders.

Consumes Market Features v2 and Alpha Ensemble v4 outputs while safely
handling absent or empty CSV artifacts.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


MARKET_FEATURES_CSV = Path(
    "output/investment_alpha/market_features.csv"
)

ENSEMBLE_SIGNALS_CSV = Path(
    "output/investment_alpha_ensemble/alpha_ensemble_signals.csv"
)


MARKET_FEATURE_COLUMNS = [
    "timestamp",
    "date",
    "asset",
    "close",
    "return_1d",
    "return_7d",
    "return_30d",
    "momentum_30d",
    "momentum_90d",
    "volatility_30d",
    "trend_state",
    "cross_sectional_score",
    "cross_sectional_rank",
    "cross_sectional_percentile",
    "source",
]


ENSEMBLE_SIGNAL_COLUMNS = [
    "timestamp",
    "date",
    "asset",
    "signal_source",
    "signal_direction",
    "signal_score",
    "conviction",
    "ensemble_score",
    "ensemble_action",
    "source",
]


def load_asset_features(
    path: str | Path = MARKET_FEATURES_CSV,
) -> pd.DataFrame:
    """Load Market Features v2 latest approved-universe features."""
    frame = safe_read_csv(
        path,
        columns=MARKET_FEATURE_COLUMNS,
    )

    if frame.empty:
        return frame

    frame = normalize_temporal_columns(frame)

    if "asset" in frame.columns:
        frame["asset"] = frame["asset"].astype(str)

    for column in [
        "close",
        "return_1d",
        "return_7d",
        "return_30d",
        "momentum_30d",
        "momentum_90d",
        "volatility_30d",
        "cross_sectional_score",
        "cross_sectional_rank",
        "cross_sectional_percentile",
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    if "asset" in frame.columns:
        frame = frame.dropna(subset=["asset"])
        frame = frame.drop_duplicates(
            subset=["asset"],
            keep="last",
        )

    return frame.reset_index(drop=True)


def load_ensemble_signals(
    path: str | Path = ENSEMBLE_SIGNALS_CSV,
) -> pd.DataFrame:
    """Load Alpha Ensemble v4 signal rows."""
    frame = safe_read_csv(
        path,
        columns=ENSEMBLE_SIGNAL_COLUMNS,
    )

    if frame.empty:
        return frame

    frame = normalize_temporal_columns(frame)

    if "asset" in frame.columns:
        frame["asset"] = frame["asset"].astype(str)

    for column in [
        "signal_score",
        "conviction",
        "ensemble_score",
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    return frame.reset_index(drop=True)


def normalize_temporal_columns(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Provide canonical timestamp plus legacy date compatibility."""
    result = frame.copy()

    temporal_column = None

    for candidate in [
        "timestamp",
        "date",
        "datetime",
        "time",
    ]:
        if candidate in result.columns:
            temporal_column = candidate
            break

    if temporal_column is None:
        return result

    result["timestamp"] = pd.to_datetime(
        result[temporal_column],
        errors="coerce",
        utc=True,
    )

    # Preserve compatibility with ranker logic that still references date.
    result["date"] = result["timestamp"]

    return result


def safe_read_csv(
    path: str | Path,
    *,
    columns: list[str],
) -> pd.DataFrame:
    """Read a CSV without failing on missing, blank, or malformed files."""
    target = Path(path)

    if (
        not target.exists()
        or not target.is_file()
        or target.stat().st_size == 0
    ):
        return pd.DataFrame(columns=columns)

    try:
        frame = pd.read_csv(target)
    except (EmptyDataError, ParserError, UnicodeDecodeError):
        return pd.DataFrame(columns=columns)

    if frame is None or len(frame.columns) == 0:
        return pd.DataFrame(columns=columns)

    return frame
