
"""Latest price extraction."""

from __future__ import annotations

import pandas as pd


def latest_prices(features: pd.DataFrame) -> dict[str, float]:
    if features.empty:
        return {}

    df = features.copy()

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    price_col = None
    for c in ["close", "price", "asset_close"]:
        if c in df.columns:
            price_col = c
            break

    if price_col is None or "asset" not in df.columns:
        return {}

    latest = df.sort_values("date").groupby("asset").tail(1)

    return {
        str(row["asset"]): float(row[price_col])
        for _, row in latest.iterrows()
        if pd.notna(row.get(price_col))
    }
