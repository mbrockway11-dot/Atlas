
"""Alpha Backtests v2 schema normalization.

Market Features v2 uses ``timestamp`` as its canonical temporal field.
The legacy backtester used ``date``. This adapter preserves compatibility
without forcing the research pipeline back to the legacy schema.
"""

from __future__ import annotations

import pandas as pd


REQUIRED_MARKET_COLUMNS = {
    "timestamp",
    "asset",
    "close",
}


def normalize_market_frame(
    market: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize Market Features v2 history for the backtester."""
    if market is None or market.empty:
        return empty_market_frame()

    frame = market.copy()

    timestamp_column = find_timestamp_column(frame)

    if timestamp_column is None:
        raise ValueError(
            "Alpha Backtests v2 requires a timestamp or date column."
        )

    frame["timestamp"] = pd.to_datetime(
        frame[timestamp_column],
        errors="coerce",
        utc=True,
    )

    # Preserve the old name for any legacy strategy calculations that
    # still reference ``date``.
    frame["date"] = frame["timestamp"]

    if "asset" not in frame.columns:
        raise ValueError(
            "Alpha Backtests v2 requires an asset column."
        )

    if "close" not in frame.columns:
        raise ValueError(
            "Alpha Backtests v2 requires a close column."
        )

    frame["asset"] = frame["asset"].astype(str)
    frame["close"] = pd.to_numeric(
        frame["close"],
        errors="coerce",
    )

    for column in [
        "open",
        "high",
        "low",
        "volume",
        "dollar_volume",
        "return_1d",
        "return_3d",
        "return_7d",
        "return_14d",
        "return_30d",
        "return_90d",
        "momentum_7d",
        "momentum_14d",
        "momentum_30d",
        "momentum_90d",
        "volatility_7d",
        "volatility_14d",
        "volatility_30d",
        "volatility_90d",
        "cross_sectional_score",
        "cross_sectional_rank",
        "cross_sectional_percentile",
    ]:
        if column in frame.columns:
            frame[column] = pd.to_numeric(
                frame[column],
                errors="coerce",
            )

    frame = frame.dropna(
        subset=["timestamp", "asset", "close"],
    )

    frame = frame.sort_values(
        ["asset", "timestamp"],
        kind="stable",
    ).drop_duplicates(
        subset=["asset", "timestamp"],
        keep="last",
    )

    frame = add_legacy_aliases(frame)

    return frame.reset_index(drop=True)


def normalize_signal_frame(
    signals: pd.DataFrame,
) -> pd.DataFrame:
    """Normalize optional alpha signal/hypothesis rows."""
    if signals is None or signals.empty:
        return pd.DataFrame()

    frame = signals.copy()
    timestamp_column = find_timestamp_column(frame)

    if timestamp_column is not None:
        frame["timestamp"] = pd.to_datetime(
            frame[timestamp_column],
            errors="coerce",
            utc=True,
        )
        frame["date"] = frame["timestamp"]

    if "asset" in frame.columns:
        frame["asset"] = frame["asset"].astype(str)

    if "timestamp" in frame.columns:
        frame = frame.dropna(subset=["timestamp"])

    return frame.reset_index(drop=True)


def filter_approved_assets(
    market: pd.DataFrame,
    approved: pd.DataFrame | None,
) -> pd.DataFrame:
    """Restrict research rows to Market Universe-approved assets."""
    if market is None or market.empty:
        return empty_market_frame()

    if (
        approved is None
        or approved.empty
        or "asset" not in approved.columns
    ):
        return market.copy()

    approved_assets = set(
        approved["asset"]
        .dropna()
        .astype(str)
        .tolist()
    )

    return market[
        market["asset"].astype(str).isin(approved_assets)
    ].copy()


def add_legacy_aliases(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    """Expose common legacy names without changing canonical fields."""
    aliases = {
        "ret_1d": "return_1d",
        "ret_3d": "return_3d",
        "ret_7d": "return_7d",
        "ret_14d": "return_14d",
        "ret_30d": "return_30d",
        "ret_90d": "return_90d",
        "vol_7d": "volatility_7d",
        "vol_14d": "volatility_14d",
        "vol_30d": "volatility_30d",
        "vol_90d": "volatility_90d",
    }

    result = frame.copy()

    for legacy, canonical in aliases.items():
        if (
            legacy not in result.columns
            and canonical in result.columns
        ):
            result[legacy] = result[canonical]

    return result


def find_timestamp_column(
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


def empty_market_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "timestamp",
            "date",
            "asset",
            "close",
        ]
    )
