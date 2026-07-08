
"""Cross-sectional alpha ranker loaders."""

from __future__ import annotations

from pathlib import Path
import pandas as pd

OUT_DIR = Path("output/investment_alpha")
ASSET_FEATURES_CSV = OUT_DIR / "market_asset_features.csv"
ENSEMBLE_SIGNALS_CSV = OUT_DIR / "alpha_ensemble_signals.csv"


def load_asset_features(path: str | Path = ASSET_FEATURES_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    df = pd.read_csv(target)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df


def load_ensemble_signals(path: str | Path = ENSEMBLE_SIGNALS_CSV) -> pd.DataFrame:
    target = Path(path)
    if not target.exists():
        return pd.DataFrame()
    df = pd.read_csv(target)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
    return df
