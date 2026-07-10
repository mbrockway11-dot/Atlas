
"""Market Features v2 input loading."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from atlas.common.io import safe_read_csv, safe_read_json


UNIVERSE_DIR = Path("output/investment_market_universe")

UNIVERSE_REPORT = UNIVERSE_DIR / "market_universe_report.json"
APPROVED_UNIVERSE = UNIVERSE_DIR / "approved_universe.csv"
UNIVERSE_PRICES = UNIVERSE_DIR / "market_universe_prices.csv"


PRICE_COLUMNS = [
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


def load_market_feature_inputs(
    legacy_root: Path | None = None,
) -> dict[str, Any]:
    """Load only Market Universe v1 outputs.

    legacy_root is retained for compatibility with the existing Core script,
    but Market Features v2 intentionally ignores the old Sigil Engine path.
    """
    del legacy_root

    report = safe_read_json(UNIVERSE_REPORT)
    approved = safe_read_csv(APPROVED_UNIVERSE)
    prices = safe_read_csv(UNIVERSE_PRICES)

    if prices is None or prices.empty:
        prices = pd.DataFrame(columns=PRICE_COLUMNS)

    return {
        "universe_report": report,
        "approved_universe": approved,
        "prices": normalize_prices(prices),
    }


def normalize_prices(prices: pd.DataFrame) -> pd.DataFrame:
    if prices is None or prices.empty:
        return pd.DataFrame(columns=PRICE_COLUMNS)

    frame = prices.copy()

    for column in PRICE_COLUMNS:
        if column not in frame.columns:
            frame[column] = pd.NA

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        errors="coerce",
        utc=True,
    )

    for column in [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "dollar_volume",
    ]:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame["asset"] = frame["asset"].astype(str)

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

    return frame.reset_index(drop=True)
