
"""Market Universe v1 market-data fetcher."""

from __future__ import annotations

from datetime import datetime, UTC
from typing import Any

import pandas as pd
import yfinance as yf


CANONICAL_COLUMNS = [
    "timestamp",
    "asset",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "dollar_volume",
    "provider",
    "interval",
    "fetched_at",
]


def fetch_market_history(
    assets: list[str],
    *,
    period: str = "2y",
    interval: str = "1d",
) -> tuple[pd.DataFrame, list[dict[str, Any]]]:
    frames: list[pd.DataFrame] = []
    errors: list[dict[str, Any]] = []
    fetched_at = datetime.now(UTC).isoformat()

    for asset in assets:
        try:
            raw = yf.download(
                asset,
                period=period,
                interval=interval,
                auto_adjust=False,
                progress=False,
                threads=False,
            )

            frame = normalize_download(
                raw,
                asset=asset,
                interval=interval,
                fetched_at=fetched_at,
            )

            if frame.empty:
                errors.append({
                    "asset": asset,
                    "error_type": "empty_download",
                    "message": "Provider returned no usable rows.",
                })
                continue

            frames.append(frame)

        except Exception as exc:
            errors.append({
                "asset": asset,
                "error_type": type(exc).__name__,
                "message": str(exc),
            })

    if not frames:
        return pd.DataFrame(columns=CANONICAL_COLUMNS), errors

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.sort_values(
        ["asset", "timestamp"],
        kind="stable",
    ).reset_index(drop=True)

    return combined[CANONICAL_COLUMNS], errors


def normalize_download(
    raw: pd.DataFrame,
    *,
    asset: str,
    interval: str,
    fetched_at: str,
) -> pd.DataFrame:
    """Normalize yfinance output into the canonical long format.

    yfinance 1.5.x returns MultiIndex price columns such as:
    ('Close', 'BTC-USD').

    Reset the date index first, then flatten and normalize every column,
    including the newly created Date column.
    """
    if raw is None or raw.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame = raw.copy().reset_index()

    normalized_columns = []

    for column in frame.columns:
        if isinstance(column, tuple):
            # Use the first non-empty MultiIndex level. For market data,
            # this is normally Date, Open, High, Low, Close, or Volume.
            parts = [
                str(part).strip()
                for part in column
                if str(part).strip()
                and str(part).strip().lower() != "nan"
            ]
            name = parts[0] if parts else ""
        else:
            name = str(column).strip()

        normalized_columns.append(
            name.lower().replace(" ", "_")
        )

    frame.columns = normalized_columns

    timestamp_col = None
    for candidate in [
        "date",
        "datetime",
        "timestamp",
        "index",
    ]:
        if candidate in frame.columns:
            timestamp_col = candidate
            break

    if timestamp_col is None:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame = frame.rename(
        columns={
            timestamp_col: "timestamp",
            "adj_close": "adjusted_close",
        }
    )

    # Duplicate column names can occasionally occur after flattening.
    frame = frame.loc[:, ~frame.columns.duplicated()].copy()

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
        subset=["timestamp", "close"]
    ).copy()

    if frame.empty:
        return pd.DataFrame(columns=CANONICAL_COLUMNS)

    frame["asset"] = asset
    # Yahoo crypto-pair Volume is already quote-currency turnover.
    # Multiplying by Close would double-count price and inflate liquidity.
    frame["dollar_volume"] = frame["volume"].fillna(0.0)
    frame["provider"] = "yfinance"
    frame["interval"] = interval
    frame["fetched_at"] = fetched_at

    return frame[CANONICAL_COLUMNS]

