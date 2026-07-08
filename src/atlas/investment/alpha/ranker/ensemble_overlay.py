
"""Overlay ensemble confirmation onto cross-sectional ranks."""

from __future__ import annotations

import pandas as pd


def overlay_ensemble_scores(ranked: pd.DataFrame, ensemble: pd.DataFrame) -> pd.DataFrame:
    if ranked.empty:
        return ranked

    out = ranked.copy()

    if ensemble.empty:
        out["ensemble_confidence"] = 0.0
        out["ensemble_confirmed"] = False
        out["final_alpha_score"] = out["raw_alpha_score"]
        return out

    cols = [
        col for col in [
            "date",
            "asset",
            "total_weight",
            "net_long_score",
            "ensemble_confidence",
            "confidence_label",
            "strategy_count",
        ]
        if col in ensemble.columns
    ]

    merged = out.merge(ensemble[cols], on=["date", "asset"], how="left")

    merged["total_weight"] = merged["total_weight"].fillna(0.0)
    merged["net_long_score"] = merged["net_long_score"].fillna(0.0)
    merged["ensemble_confidence"] = merged["ensemble_confidence"].fillna(0.0)
    merged["strategy_count"] = merged["strategy_count"].fillna(0)

    merged["ensemble_confirmed"] = merged["net_long_score"] > 0
    merged["ensemble_bonus"] = merged["ensemble_confidence"] * merged["net_long_score"] * 0.25
    merged["final_alpha_score"] = merged["raw_alpha_score"] + merged["ensemble_bonus"]

    merged["final_rank"] = merged.groupby("date")["final_alpha_score"].rank(
        ascending=False,
        method="min",
    )

    merged["final_rank_label"] = merged["final_rank"].apply(label_final_rank)
    return merged


def label_final_rank(rank) -> str:
    try:
        r = int(rank)
    except Exception:
        return "unranked"

    if r == 1:
        return "highest_conviction"
    if r <= 3:
        return "portfolio_candidate"
    return "watchlist"
