
"""Market Direction Engine loaders."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


REGISTRY_CSV = Path("output/investment_strategy_registry/strategy_registry_signals.csv")


def load_strategy_registry(path: str | Path = REGISTRY_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()

    df = pd.read_csv(target)

    for col in ["confidence", "target_exposure", "rank"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)

    return df
