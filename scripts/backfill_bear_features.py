"""Backfill market features to 2021 so the engines can be tested through a bear.

The 5-year daily OHLCV already exists in the price repository
(data/market_prices/<asset>/1d.csv, 2021-07..2026-07), but the feature builder
reads the 2-year market_universe_prices.csv. This rebuilds that universe price
file from the full repository (a strict superset -- the original is backed up),
then regenerates the feature history over the whole span, including the
2021-2022 bear the earlier validation never saw.

    .venv/Scripts/python.exe scripts/backfill_bear_features.py
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.market_features.report import build_market_feature_report

REPO = Path("data/market_prices")
UNIVERSE_PRICES = Path("output/investment_market_universe/market_universe_prices.csv")
COLUMNS = [
    "timestamp", "asset", "open", "high", "low", "close",
    "volume", "dollar_volume", "provider", "interval", "fetched_at",
]


def main() -> int:
    frames = []
    for path in sorted(REPO.glob("*/1d.csv")):
        frame = pd.read_csv(path)
        frame["interval"] = frame.get("timeframe", "1d")
        frames.append(frame)
    if not frames:
        print("No repository 1d files found.")
        return 1

    prices = pd.concat(frames, ignore_index=True)
    for column in COLUMNS:
        if column not in prices.columns:
            prices[column] = pd.NA
    prices = prices[COLUMNS]
    span = (
        pd.to_datetime(prices["timestamp"], utc=True, errors="coerce")
        .dropna()
    )
    print(
        f"Rebuilt universe prices: {len(prices)} rows, "
        f"{span.min().date()}..{span.max().date()}, "
        f"{prices['asset'].nunique()} assets"
    )

    if UNIVERSE_PRICES.exists():
        backup = UNIVERSE_PRICES.with_suffix(".csv.2yr.bak")
        if not backup.exists():
            shutil.copy2(UNIVERSE_PRICES, backup)
            print(f"Backed up original -> {backup}")
    UNIVERSE_PRICES.parent.mkdir(parents=True, exist_ok=True)
    prices.to_csv(UNIVERSE_PRICES, index=False)

    print("\nRebuilding feature history over the full span...")
    report = build_market_feature_report()
    print(f"  success={report.get('success')}  history_rows={report.get('history_rows')}")

    hist = pd.read_csv("output/investment_alpha/market_feature_history.csv")
    hspan = pd.to_datetime(hist["timestamp"], utc=True, errors="coerce").dropna()
    print(
        f"  feature history now: {len(hist)} rows, "
        f"{hspan.min().date()}..{hspan.max().date()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
