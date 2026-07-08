
"""Cross-sectional alpha scoring."""

from __future__ import annotations

import pandas as pd


def add_cross_sectional_scores(asset_features: pd.DataFrame) -> pd.DataFrame:
    if asset_features.empty:
        return asset_features

    df = asset_features.copy()
    score_parts = []

    for col, weight in [
        ("return_24", 0.20),
        ("return_72", 0.30),
        ("return_288", 0.20),
        ("momentum_acceleration", 0.10),
        ("momentum_72_minus_288", 0.10),
    ]:
        if col in df.columns:
            rank_col = f"{col}_cs_rank"
            score_col = f"{col}_cs_score"
            df[rank_col] = df.groupby("date")[col].rank(pct=True)
            df[score_col] = df[rank_col] * weight
            score_parts.append(score_col)

    if "realized_vol_72" in df.columns:
        vol_rank = df.groupby("date")["realized_vol_72"].rank(pct=True)
        df["volatility_penalty"] = vol_rank * 0.15
    else:
        df["volatility_penalty"] = 0.0

    df["raw_alpha_score"] = df[score_parts].sum(axis=1) - df["volatility_penalty"] if score_parts else 0.0

    df["cross_sectional_rank"] = df.groupby("date")["raw_alpha_score"].rank(
        ascending=False,
        method="min",
    )

    df["cross_sectional_pct_rank"] = df.groupby("date")["raw_alpha_score"].rank(pct=True)
    df["alpha_rank_label"] = df["cross_sectional_rank"].apply(label_rank)

    return df


def label_rank(rank) -> str:
    try:
        r = int(rank)
    except Exception:
        return "unranked"

    if r == 1:
        return "top_asset"
    if r <= 3:
        return "top_cluster"
    return "lower_rank"
