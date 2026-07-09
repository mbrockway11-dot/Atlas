
"""Mark-to-Market v3 pricing."""

from __future__ import annotations

import pandas as pd


FALLBACK_PRICES = {
    "BTC-USD": 67672.9140625,
    "ETH-USD": 2065.40966796875,
    "SOL-USD": 150.0,
}


def latest_prices(price_data: pd.DataFrame) -> dict[str, float]:
    if price_data.empty:
        return dict(FALLBACK_PRICES)

    df = price_data.copy()

    if "asset" not in df.columns or "close" not in df.columns:
        return dict(FALLBACK_PRICES)

    prices = {}

    if "date" in df.columns:
        df = df.sort_values("date")

    for asset, group in df.groupby("asset"):
        close = pd.to_numeric(group["close"], errors="coerce").dropna()
        if not close.empty:
            prices[str(asset)] = float(close.iloc[-1])

    for asset, price in FALLBACK_PRICES.items():
        prices.setdefault(asset, price)

    return prices
