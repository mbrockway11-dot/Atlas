
"""Momentum market features."""

from __future__ import annotations

import pandas as pd


RETURN_WINDOWS = [1, 4, 12, 24, 72, 96, 144, 192, 288]


def add_momentum_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add return, rank, and acceleration features."""
    if df.empty:
        return df

    out = df.copy()

    for window in RETURN_WINDOWS:
        col = f"return_{window}"
        out[col] = out.groupby("asset")["close"].pct_change(window)

    out["momentum_24_minus_72"] = out["return_24"] - out["return_72"]
    out["momentum_72_minus_288"] = out["return_72"] - out["return_288"]
    out["momentum_acceleration"] = out["return_24"] - out.groupby("asset")["return_24"].shift(24)

    for window in [24, 72, 288]:
        ret_col = f"return_{window}"
        rank_col = f"rank_return_{window}"
        pct_col = f"pct_rank_return_{window}"
        out[rank_col] = out.groupby("date")[ret_col].rank(ascending=False, method="min")
        out[pct_col] = out.groupby("date")[ret_col].rank(pct=True)

    return out
