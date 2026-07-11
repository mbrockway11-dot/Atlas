"""Evidence-backed research-hypothesis generation."""

from __future__ import annotations

import hashlib

import pandas as pd

from atlas.investment.meta_research.config import (
    MAX_HYPOTHESES,
    MIN_POSITIVE_LIFT,
    MIN_SEGMENT_TRADES,
    POSITIVE_MEAN_THRESHOLD,
    STRONG_PROFIT_FACTOR,
)


HYPOTHESIS_COLUMNS = [
    "hypothesis_id",
    "hypothesis_type",
    "priority",
    "confidence",
    "engine_id",
    "family",
    "feature",
    "state",
    "observation_count",
    "mean_return",
    "profit_factor",
    "return_lift",
    "thesis",
    "proposed_test",
    "validation_requirement",
    "status",
    "execution_instruction",
]


def build_hypothesis_library(
    interactions: pd.DataFrame,
    failure_modes: pd.DataFrame,
    family_gaps: pd.DataFrame,
) -> pd.DataFrame:
    rows = []

    rows.extend(
        build_opportunity_hypotheses(
            interactions
        )
    )

    rows.extend(
        build_failure_hypotheses(
            failure_modes
        )
    )

    rows.extend(
        build_gap_hypotheses(
            family_gaps
        )
    )

    if not rows:
        return pd.DataFrame(
            columns=HYPOTHESIS_COLUMNS
        )

    result = pd.DataFrame(
        rows,
        columns=HYPOTHESIS_COLUMNS,
    )

    result = result.sort_values(
        [
            "priority",
            "confidence",
            "observation_count",
            "hypothesis_id",
        ],
        ascending=[
            False,
            False,
            False,
            True,
        ],
        kind="stable",
    ).drop_duplicates(
        subset=["hypothesis_id"],
        keep="first",
    ).head(
        MAX_HYPOTHESES
    )

    return result.reset_index(
        drop=True
    )


def build_opportunity_hypotheses(
    interactions: pd.DataFrame,
) -> list[dict]:
    if (
        interactions is None
        or interactions.empty
    ):
        return []

    candidates = interactions[
        interactions[
            "observation_count"
        ].ge(
            MIN_SEGMENT_TRADES
        )
        & interactions[
            "mean_return"
        ].ge(
            POSITIVE_MEAN_THRESHOLD
        )
        & interactions[
            "profit_factor"
        ].ge(
            STRONG_PROFIT_FACTOR
        )
        & interactions[
            "return_lift"
        ].ge(
            MIN_POSITIVE_LIFT
        )
    ]

    rows = []

    for _, row in candidates.iterrows():
        engine_id = str(
            row["engine_id"]
        )

        feature = str(
            row["feature"]
        )

        state = str(
            row["state"]
        )

        confidence = float(
            row["confidence"]
        )

        rows.append({
            "hypothesis_id": make_id(
                "OPPORTUNITY",
                engine_id,
                feature,
                state,
            ),
            "hypothesis_type": (
                "CONDITIONAL_OPPORTUNITY"
            ),
            "priority": round(
                confidence
                * (
                    1.0
                    + min(
                        1.0,
                        float(
                            row[
                                "return_lift"
                            ]
                        ) / 0.04,
                    )
                )
                / 2.0,
                8,
            ),
            "confidence": confidence,
            "engine_id": engine_id,
            "family": str(
                row["family"]
            ),
            "feature": feature,
            "state": state,
            "observation_count": int(
                row[
                    "observation_count"
                ]
            ),
            "mean_return": float(
                row["mean_return"]
            ),
            "profit_factor": float(
                row[
                    "profit_factor"
                ]
            ),
            "return_lift": float(
                row["return_lift"]
            ),
            "thesis": (
                f"{engine_id} performs materially "
                f"better when {feature}={state}."
            ),
            "proposed_test": (
                "Build a research-only gated variant "
                f"of {engine_id} that activates when "
                f"{feature}={state}; compare it with the "
                "ungated engine using non-overlapping "
                "walk-forward trades."
            ),
            "validation_requirement": (
                "Out-of-sample improvement in net return, "
                "Sharpe, and drawdown across at least "
                "three rolling windows."
            ),
            "status": "PROPOSED",
            "execution_instruction": False,
        })

    return rows


def build_failure_hypotheses(
    failures: pd.DataFrame,
) -> list[dict]:
    if (
        failures is None
        or failures.empty
    ):
        return []

    rows = []

    for _, row in failures.iterrows():
        engine_id = str(
            row["engine_id"]
        )

        feature = str(
            row["feature"]
        )

        state = str(
            row["state"]
        )

        rows.append({
            "hypothesis_id": make_id(
                "FAILURE_GATE",
                engine_id,
                feature,
                state,
            ),
            "hypothesis_type": (
                "FAILURE_MODE_GATE"
            ),
            "priority": round(
                float(
                    row["severity"]
                ) * 0.60
                + float(
                    row["confidence"]
                ) * 0.40,
                8,
            ),
            "confidence": float(
                row["confidence"]
            ),
            "engine_id": engine_id,
            "family": str(
                row["family"]
            ),
            "feature": feature,
            "state": state,
            "observation_count": int(
                row[
                    "observation_count"
                ]
            ),
            "mean_return": float(
                row["mean_return"]
            ),
            "profit_factor": float(
                row[
                    "profit_factor"
                ]
            ),
            "return_lift": float(
                row["return_lift"]
            ),
            "thesis": str(
                row["failure_mode"]
            ),
            "proposed_test": str(
                row[
                    "recommended_action"
                ]
            ),
            "validation_requirement": (
                "The gate must improve net expectancy "
                "without eliminating more than 70% of "
                "the original trade sample."
            ),
            "status": "PROPOSED",
            "execution_instruction": False,
        })

    return rows


def build_gap_hypotheses(
    gaps: pd.DataFrame,
) -> list[dict]:
    if gaps is None or gaps.empty:
        return []

    candidates = gaps[
        gaps["gap_score"] >= 0.45
    ]

    rows = []

    for _, row in candidates.iterrows():
        family = str(
            row["family"]
        )

        status = str(
            row[
                "coverage_status"
            ]
        )

        rows.append({
            "hypothesis_id": make_id(
                "FAMILY_GAP",
                family,
                status,
            ),
            "hypothesis_type": (
                "ENGINE_FAMILY_GAP"
            ),
            "priority": float(
                row["gap_score"]
            ),
            "confidence": round(
                0.50
                + float(
                    row["gap_score"]
                ) * 0.30,
                8,
            ),
            "engine_id": "",
            "family": family,
            "feature": "",
            "state": status,
            "observation_count": int(
                row["engine_count"]
            ),
            "mean_return": float(
                row[
                    "best_mean_return"
                ]
            ),
            "profit_factor": float(
                row[
                    "best_profit_factor"
                ]
            ),
            "return_lift": 0.0,
            "thesis": (
                f"Atlas has a {status.lower()} "
                f"in the {family} family."
            ),
            "proposed_test": (
                f"Design one research-only {family} "
                "engine using features not already "
                "dominated by the eligible engine set."
            ),
            "validation_requirement": (
                "Candidate must pass historical validation, "
                "independence analysis, Research Lab review, "
                "and walk-forward portfolio contribution."
            ),
            "status": "PROPOSED",
            "execution_instruction": False,
        })

    return rows


def make_id(
    *parts: str,
) -> str:
    payload = "|".join(
        str(part)
        for part in parts
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:16]

    return f"HYP-{digest}"
