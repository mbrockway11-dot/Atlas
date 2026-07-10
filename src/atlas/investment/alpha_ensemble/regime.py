
"""Alpha Ensemble v5 regime and rotation intelligence."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from atlas.common.io import safe_read_csv


HISTORY_CSV = Path(
    "output/investment_alpha_ensemble/"
    "alpha_ensemble_history.csv"
)


def build_ensemble_regime(
    scores: list[dict],
) -> dict:
    if not scores:
        return {
            "regime": "NO_DATA",
            "breadth": 0.0,
            "strong_asset_count": 0,
            "weak_asset_count": 0,
            "median_score": 0.0,
            "recommended_cash_weight": 1.0,
        }

    frame = pd.DataFrame(scores)

    score = pd.to_numeric(
        frame["ensemble_score"],
        errors="coerce",
    ).fillna(0.0)

    confidence = pd.to_numeric(
        frame["confidence"],
        errors="coerce",
    ).fillna(0.0)

    qualified = (
        (score >= 0.56)
        & (confidence >= 0.50)
    )

    strong = (
        (score >= 0.68)
        & (confidence >= 0.65)
    )

    weak = score < 0.42

    breadth = float(qualified.mean())
    strong_count = int(strong.sum())
    weak_count = int(weak.sum())
    median_score = float(score.median())

    if breadth >= 0.70 and strong_count >= 4:
        regime = "BROAD_RISK_ON"
        cash = 0.10
    elif breadth >= 0.50:
        regime = "SELECTIVE_RISK_ON"
        cash = 0.20
    elif strong_count >= 2:
        regime = "HIGH_DISPERSION_SELECTION"
        cash = 0.30
    elif weak_count >= len(frame) * 0.60:
        regime = "RISK_OFF"
        cash = 0.70
    else:
        regime = "MIXED"
        cash = 0.40

    return {
        "regime": regime,
        "breadth": round(breadth, 6),
        "strong_asset_count": strong_count,
        "qualified_asset_count": int(qualified.sum()),
        "weak_asset_count": weak_count,
        "median_score": round(median_score, 6),
        "recommended_cash_weight": cash,
        "asset_count": len(frame),
    }


def detect_rotations(
    scores: list[dict],
) -> list[dict]:
    current = pd.DataFrame(scores)

    if current.empty:
        return []

    history = safe_read_csv(HISTORY_CSV)

    if history.empty or "asset" not in history.columns:
        return [
            {
                "asset": row["asset"],
                "rotation": "NEW_OBSERVATION",
                "previous_rank": None,
                "current_rank": row.get(
                    "ensemble_rank"
                ),
                "rank_change": None,
            }
            for row in scores
        ]

    previous = history.copy()

    if "generated_at" in previous.columns:
        previous["generated_at"] = pd.to_datetime(
            previous["generated_at"],
            errors="coerce",
            utc=True,
        )
        latest_timestamp = previous[
            "generated_at"
        ].max()
        previous = previous[
            previous["generated_at"]
            == latest_timestamp
        ]

    previous = previous.drop_duplicates(
        subset=["asset"],
        keep="last",
    )

    previous_map = {
        str(row.get("asset")): row.to_dict()
        for _, row in previous.iterrows()
    }

    rotations = []

    for row in scores:
        asset = row["asset"]
        prior = previous_map.get(asset)

        if prior is None:
            label = "NEW_ENTRY"
            previous_rank = None
            rank_change = None
        else:
            previous_rank = to_number(
                prior.get("ensemble_rank")
            )
            current_rank = to_number(
                row.get("ensemble_rank")
            )

            rank_change = (
                previous_rank - current_rank
            )

            if rank_change >= 3:
                label = "ROTATING_IN"
            elif rank_change <= -3:
                label = "ROTATING_OUT"
            else:
                label = "STABLE"

        rotations.append({
            "asset": asset,
            "sector": row.get("sector"),
            "rotation": label,
            "previous_rank": previous_rank,
            "current_rank": row.get(
                "ensemble_rank"
            ),
            "rank_change": rank_change,
            "current_score": row.get(
                "ensemble_score"
            ),
            "current_confidence": row.get(
                "confidence"
            ),
        })

    return rotations


def to_number(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
