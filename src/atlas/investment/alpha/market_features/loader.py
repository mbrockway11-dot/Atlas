
"""Market data loader for Alpha Discovery."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


DEFAULT_ROOT = Path(r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine")


def load_price_data(root: str | Path = DEFAULT_ROOT) -> pd.DataFrame:
    """Load investment engine price_data.csv."""
    path = Path(root) / "output" / "price_data.csv"

    if not path.exists():
        return pd.DataFrame()

    return pd.read_csv(path)


def normalize_price_data(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize long-format price data."""
    if df.empty:
        return df

    out = df.copy()

    date_col = detect_col(out, ["date", "timestamp", "datetime", "time"])
    asset_col = detect_col(out, ["asset", "symbol", "ticker"])

    if not date_col or not asset_col:
        return pd.DataFrame()

    rename = {
        date_col: "date",
        asset_col: "asset",
    }

    out = out.rename(columns=rename)
    out["date"] = pd.to_datetime(out["date"], errors="coerce")

    for col in ["open", "high", "low", "close", "volume"]:
        if col in out.columns:
            out[col] = pd.to_numeric(out[col], errors="coerce")

    needed = ["date", "asset", "close"]
    out = out.dropna(subset=needed)
    out = out.sort_values(["asset", "date"]).reset_index(drop=True)

    return out


def detect_col(df: pd.DataFrame, names: list[str]) -> str:
    """Detect column by preferred names."""
    lowered = {col.lower(): col for col in df.columns}

    for name in names:
        if name in lowered:
            return lowered[name]

    for col in df.columns:
        lower = col.lower()
        if any(name in lower for name in names):
            return col

    return ""
