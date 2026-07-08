
"""Alpha ensemble loaders."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd


OUT_DIR = Path("output/investment_alpha")
PROMOTED_JSON = OUT_DIR / "promoted_alpha_strategies.json"
TRADES_CSV = OUT_DIR / "alpha_backtest_trades.csv"
RANKINGS_CSV = OUT_DIR / "alpha_rankings.csv"


def load_promoted_strategies(path: str | Path = PROMOTED_JSON) -> list[dict[str, Any]]:
    target = Path(path)
    if not target.exists():
        return []
    return json.loads(target.read_text(encoding="utf-8"))


def load_alpha_trades(path: str | Path = TRADES_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    df = pd.read_csv(target)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_rankings(path: str | Path = RANKINGS_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    return pd.read_csv(target)
