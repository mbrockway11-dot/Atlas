
"""Time-segmented price fetching."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import pandas as pd
import yfinance as yf


CANONICAL_COLUMNS = [
    "timestamp",
    "asset",
    "timeframe",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dollar_volume",
    "provider",
    "fetched_at",
]


def fetch_price_segment(
    asset: str,
    *,
    timeframe: str,
    interval: str,
    period: str,
) -> tuple[pd.DataFrame, dict[str, Any] | None]:
    fetched_at = datetime.now(UTC).isoformat()

    try:
        raw = yf.download(
            asset,
            period=period,
            interval=interval,
            auto_adjust=False,
            progress=False,
            threads=False,
        )

        normalized = normalize_download(
            raw,
            asset=asset,
            timeframe=timeframe,
            fetched_at=fetched_at,
        )

        if normalized.empty:
            return (
                pd.DataFrame(columns=CANONICAL_COLUMNS),
                {
                    "asset": asset,
                    "timeframe": timeframe,
                    "error_type": "empty_download",
                    "message": "Provider returned no usable rows.",
                },
            )

        return normalized, None

    except Exception as exc:
        return (
            pd.DataFrame(columns=CANONICAL_COLUMNS),
            {
                "asset": asset,
                "timeframe": timeframe,
                "error_type": type(exc).__name__,
                "message": str(exc),
            },
        )


def normalize_download(
    raw: pd.DataFrame,
    *,
    asset: str,
    timeframe: str,
    fetched_at: str,
) -> pd.DataFrame:
    if raw is None or raw.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame = raw.copy().reset_index()

    columns = []

    for column in frame.columns:
        if isinstance(column, tuple):
            parts = [
                str(part).strip()
                for part in column
                if str(part).strip()
                and str(part).strip().lower() != "nan"
            ]
            name = parts[0] if parts else ""
        else:
            name = str(column).strip()

        columns.append(
            name.lower().replace(" ", "_")
        )

    frame.columns = columns
    frame = frame.loc[
        :,
        ~frame.columns.duplicated(),
    ].copy()

    timestamp_column = None

    for candidate in [
        "datetime",
        "date",
        "timestamp",
        "index",
    ]:
        if candidate in frame.columns:
            timestamp_column = candidate
            break

    if timestamp_column is None:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame = frame.rename(
        columns={timestamp_column: "timestamp"}
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
    ]:
        if column not in frame.columns:
            frame[column] = pd.NA

        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        errors="coerce",
        utc=True,
    )

    frame = frame.dropna(
        subset=["timestamp", "close"],
    ).copy()

    if frame.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame["asset"] = asset
    frame["timeframe"] = timeframe

    # Yahoo crypto volume is quote-currency turnover.
    frame["dollar_volume"] = (
        frame["volume"].fillna(0.0)
    )

    frame["provider"] = "yfinance"
    frame["fetched_at"] = fetched_at

    return frame[CANONICAL_COLUMNS]
