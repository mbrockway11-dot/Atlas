"""Research engine vote aggregation for Alpha Ensemble v6.1."""

from __future__ import annotations

import math

import pandas as pd

from atlas.investment.alpha_ensemble.governance import (
    governance_by_engine,
)


def build_research_engine_votes(
    signals: pd.DataFrame,
    governance: pd.DataFrame,
) -> dict[str, dict]:
    """Aggregate eligible engine signals into asset-level votes."""
    if (
        signals is None
        or signals.empty
        or governance is None
        or governance.empty
    ):
        return {}

    required = {
        "engine_id",
        "asset",
        "normalized_score",
    }

    if not required.issubset(
        signals.columns
    ):
        return {}

    governance_map = governance_by_engine(
        governance
    )

    frame = signals.copy()

    frame["engine_id"] = (
        frame["engine_id"]
        .astype(str)
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
    )

    frame["normalized_score"] = (
        pd.to_numeric(
            frame["normalized_score"],
            errors="coerce",
        )
    )

    if "confidence" not in frame.columns:
        frame["confidence"] = 1.0

    frame["confidence"] = (
        pd.to_numeric(
            frame["confidence"],
            errors="coerce",
        )
        .fillna(0.0)
        .clip(0.0, 1.0)
    )

    frame = frame.dropna(
        subset=[
            "engine_id",
            "asset",
            "normalized_score",
        ]
    )

    rows: list[dict] = []

    for asset, group in frame.groupby(
        "asset",
        sort=True,
    ):
        weighted_total = 0.0
        available_weight = 0.0
        contributing_engines: list[str] = []
        promoted_count = 0
        keep_count = 0

        for _, signal in group.iterrows():
            engine_id = str(
                signal["engine_id"]
            )

            policy = governance_map.get(
                engine_id,
                {},
            )

            if not bool(
                policy.get(
                    "eligible",
                    False,
                )
            ):
                continue

            governance_weight = finite(
                policy.get(
                    "governance_weight"
                )
            )

            confidence = finite(
                signal.get("confidence"),
                default=1.0,
            )

            effective_weight = (
                governance_weight
                * max(
                    0.0,
                    min(
                        1.0,
                        confidence,
                    ),
                )
            )

            if effective_weight <= 0:
                continue

            score = max(
                0.0,
                min(
                    1.0,
                    finite(
                        signal.get(
                            "normalized_score"
                        ),
                        default=0.5,
                    ),
                ),
            )

            weighted_total += (
                score * effective_weight
            )

            available_weight += (
                effective_weight
            )

            contributing_engines.append(
                engine_id
            )

            decision = str(
                policy.get(
                    "decision",
                    "",
                )
            ).upper()

            if decision == "PROMOTE":
                promoted_count += 1
            elif decision == "KEEP":
                keep_count += 1

        if available_weight <= 0:
            continue

        vote = (
            weighted_total
            / available_weight
        )

        engine_count = len(
            contributing_engines
        )

        coverage = min(
            1.0,
            engine_count
            / max(
                1,
                int(
                    governance[
                        "eligible"
                    ].sum()
                ),
            ),
        )

        rows.append({
            "asset": asset,
            "research_engine_vote": round(
                vote,
                8,
            ),
            "research_engine_confidence": round(
                coverage,
                8,
            ),
            "research_engine_count": engine_count,
            "research_promoted_count": promoted_count,
            "research_keep_count": keep_count,
            "research_engine_ids": "|".join(
                sorted(
                    contributing_engines
                )
            ),
        })

    return {
        row["asset"]: row
        for row in rows
    }


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )

