
"""Execution Simulator loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd


ORDER_INTENTS_CSV = Path("output/investment_execution/execution_order_intents.csv")


def load_order_intents(path: str | Path = ORDER_INTENTS_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()

    df = pd.read_csv(target)

    if "planned_weight" in df.columns:
        df["planned_weight"] = pd.to_numeric(df["planned_weight"], errors="coerce").fillna(0.0)

    return df
