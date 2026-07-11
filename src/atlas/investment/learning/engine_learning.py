"""Adaptive recommendations for Learning Engine v3.1."""

from __future__ import annotations

import pandas as pd


def build_engine_learning_recommendations(
    strategy_summary: pd.DataFrame,
) -> list[dict]:
    """Translate persistent memory into read-only engine guidance."""
    if (
        strategy_summary is None
        or strategy_summary.empty
    ):
        return []

    rows: list[dict] = []

    for _, row in strategy_summary.iterrows():
        engine_id = str(
            row.get("engine_id")
        )

        decision = str(
            row.get(
                "latest_decision",
                "UNKNOWN",
            )
        ).upper()

        reliability = float(
            row.get(
                "recency_weighted_reliability",
                0.0,
            )
            or 0.0
        )

        trend = float(
            row.get(
                "promotion_score_trend",
                0.0,
            )
            or 0.0
        )

        changed = bool(
            row.get(
                "decision_changed",
                False,
            )
        )

        if (
            decision == "PROMOTE"
            and reliability >= 0.65
            and not changed
        ):
            recommendation = (
                "SUSTAIN_PROMOTION"
            )
            weight_multiplier = 1.0

        elif (
            decision == "PROMOTE"
            and reliability < 0.65
        ):
            recommendation = (
                "PROMOTION_PROBATION"
            )
            weight_multiplier = 0.80

        elif (
            decision == "KEEP"
            and trend > 0.03
        ):
            recommendation = (
                "PROMOTION_WATCH"
            )
            weight_multiplier = 0.75

        elif decision == "KEEP":
            recommendation = (
                "MAINTAIN_RESEARCH_WEIGHT"
            )
            weight_multiplier = 0.60

        elif decision == "REVISE":
            recommendation = (
                "RECALIBRATE_THRESHOLDS"
            )
            weight_multiplier = 0.20

        elif decision == "RETIRE":
            recommendation = (
                "EXCLUDE_FROM_ENSEMBLE"
            )
            weight_multiplier = 0.0

        else:
            recommendation = (
                "INSUFFICIENT_MEMORY"
            )
            weight_multiplier = 0.0

        rows.append({
            "engine_id": engine_id,
            "latest_decision": decision,
            "memory_status": row.get(
                "memory_status"
            ),
            "observation_count": int(
                row.get(
                    "observation_count",
                    0,
                )
                or 0
            ),
            "reliability": round(
                reliability,
                8,
            ),
            "promotion_score_trend": round(
                trend,
                8,
            ),
            "recommendation": recommendation,
            "learning_weight_multiplier": (
                weight_multiplier
            ),
            "read_only": True,
        })

    return sorted(
        rows,
        key=lambda item: (
            -item[
                "learning_weight_multiplier"
            ],
            item["engine_id"],
        ),
    )
