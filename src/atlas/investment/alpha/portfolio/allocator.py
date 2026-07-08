
"""Portfolio allocator."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.portfolio.constraints import (
    MAX_ASSET_WEIGHT,
    MAX_TOTAL_RISK_EXPOSURE,
    MIN_CASH_WEIGHT,
    clamp_weight,
)


def allocate_from_rankings(latest: pd.DataFrame) -> pd.DataFrame:
    """Allocate portfolio weights from latest alpha rankings."""
    if latest.empty:
        return pd.DataFrame()

    df = latest.copy()
    df["final_alpha_score"] = pd.to_numeric(df["final_alpha_score"], errors="coerce").fillna(0.0)
    df = df.sort_values("final_rank").head(5)

    positive = df[df["final_alpha_score"] > 0].copy()

    if positive.empty:
        return pd.DataFrame([{"asset": "CASH", "target_weight": 1.0, "reason": "No positive alpha scores."}])

    score_sum = positive["final_alpha_score"].sum()
    investable = MAX_TOTAL_RISK_EXPOSURE - MIN_CASH_WEIGHT

    positive["raw_weight"] = positive["final_alpha_score"] / score_sum * investable
    positive["target_weight"] = positive["raw_weight"].apply(lambda x: clamp_weight(x, max_weight=MAX_ASSET_WEIGHT))

    used = positive["target_weight"].sum()
    cash = max(MIN_CASH_WEIGHT, 1.0 - used)

    rows = []

    for _, row in positive.iterrows():
        rows.append({
            "asset": row["asset"],
            "target_weight": round(float(row["target_weight"]), 6),
            "alpha_score": round(float(row["final_alpha_score"]), 8),
            "rank": row.get("final_rank"),
            "rank_label": row.get("final_rank_label"),
            "ensemble_confidence": row.get("ensemble_confidence", 0.0),
            "reason": "Allocated by cross-sectional alpha score with max-asset cap.",
        })

    rows.append({
        "asset": "CASH",
        "target_weight": round(float(cash), 6),
        "alpha_score": 0.0,
        "rank": None,
        "rank_label": "cash_buffer",
        "ensemble_confidence": 0.0,
        "reason": "Residual cash buffer and risk reserve.",
    })

    return pd.DataFrame(rows)
