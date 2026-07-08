
"""Portfolio mark-to-market."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


PRICE_DATA = Path("output/investment_alpha/market_asset_features.csv")


def latest_prices() -> dict[str, float]:
    if not PRICE_DATA.exists():
        return {}

    df = pd.read_csv(PRICE_DATA)

    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")

    price_col = None
    for candidate in ["close", "price", "asset_close"]:
        if candidate in df.columns:
            price_col = candidate
            break

    if price_col is None:
        return {}

    latest = df.sort_values("date").groupby("asset").tail(1)

    return {
        str(row["asset"]): float(row[price_col])
        for _, row in latest.iterrows()
        if pd.notna(row.get(price_col))
    }


def mark_portfolio_to_market(portfolio: pd.DataFrame) -> pd.DataFrame:
    if portfolio.empty:
        return portfolio

    prices = latest_prices()
    out = portfolio.copy()

    out["latest_price"] = out["asset"].map(prices).fillna(1.0)
    out.loc[out["asset"] == "CASH", "latest_price"] = 1.0

    return out
