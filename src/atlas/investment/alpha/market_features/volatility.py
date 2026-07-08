
"""Volatility market features."""

from __future__ import annotations

import pandas as pd


VOL_WINDOWS = [24, 72, 168, 288]


def add_volatility_features(df: pd.DataFrame) -> pd.DataFrame:
    """Add realized volatility and compression features."""
    if df.empty:
        return df

    out = df.copy()

    if "return_1" not in out.columns:
        out["return_1"] = out.groupby("asset")["close"].pct_change()

    for window in VOL_WINDOWS:
        out[f"realized_vol_{window}"] = (
            out.groupby("asset")["return_1"]
            .rolling(window)
            .std()
            .reset_index(level=0, drop=True)
        )

    out["vol_compression_72_vs_288"] = out["realized_vol_72"] / out["realized_vol_288"]
    out["vol_expansion_24_vs_72"] = out["realized_vol_24"] / out["realized_vol_72"]

    if {"high", "low", "close"}.issubset(out.columns):
        prev_close = out.groupby("asset")["close"].shift(1)
        true_range = pd.concat(
            [
                (out["high"] - out["low"]).abs(),
                (out["high"] - prev_close).abs(),
                (out["low"] - prev_close).abs(),
            ],
            axis=1,
        ).max(axis=1)

        out["true_range"] = true_range
        out["atr_72"] = (
            out.groupby("asset")["true_range"]
            .rolling(72)
            .mean()
            .reset_index(level=0, drop=True)
        )
        out["atr_pct_72"] = out["atr_72"] / out["close"]

    return out
