"""Engine failure-mode detection."""

from __future__ import annotations

import hashlib

import pandas as pd

from atlas.investment.meta_research.config import (
    MIN_NEGATIVE_LIFT,
    MIN_SEGMENT_TRADES,
    NEGATIVE_MEAN_THRESHOLD,
    WEAK_PROFIT_FACTOR,
)


FAILURE_COLUMNS = [
    "failure_id",
    "engine_id",
    "family",
    "feature",
    "state",
    "observation_count",
    "win_rate",
    "mean_return",
    "profit_factor",
    "return_lift",
    "severity",
    "confidence",
    "failure_mode",
    "recommended_action",
]


def build_engine_failure_modes(
    interactions: pd.DataFrame,
) -> pd.DataFrame:
    if (
        interactions is None
        or interactions.empty
    ):
        return pd.DataFrame(
            columns=FAILURE_COLUMNS
        )

    candidates = interactions[
        interactions[
            "observation_count"
        ].ge(
            MIN_SEGMENT_TRADES
        )
        & (
            interactions[
                "mean_return"
            ].le(
                NEGATIVE_MEAN_THRESHOLD
            )
            | interactions[
                "profit_factor"
            ].lt(
                WEAK_PROFIT_FACTOR
            )
        )
        & interactions[
            "return_lift"
        ].le(
            -MIN_NEGATIVE_LIFT
        )
    ].copy()

    rows = []

    for _, row in candidates.iterrows():
        severity = calculate_severity(
            mean_return=float(
                row[
                    "mean_return"
                ]
            ),
            profit_factor=float(
                row[
                    "profit_factor"
                ]
            ),
            return_lift=float(
                row[
                    "return_lift"
                ]
            ),
        )

        engine_id = str(
            row["engine_id"]
        )

        feature = str(
            row["feature"]
        )

        state = str(
            row["state"]
        )

        failure_id = hashlib.sha256(
            (
                f"{engine_id}|"
                f"{feature}|"
                f"{state}"
            ).encode("utf-8")
        ).hexdigest()[:16]

        rows.append({
            "failure_id": (
                f"FAIL-{failure_id}"
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
            "win_rate": float(
                row["win_rate"]
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
            "severity": severity,
            "confidence": float(
                row["confidence"]
            ),
            "failure_mode": (
                f"{engine_id} underperforms when "
                f"{feature} is {state}."
            ),
            "recommended_action": (
                "Test a gating rule that suppresses "
                f"{engine_id} when {feature}={state}; "
                "validate with walk-forward analysis "
                "before changing production governance."
            ),
        })

    return pd.DataFrame(
        rows,
        columns=FAILURE_COLUMNS,
    ).sort_values(
        [
            "severity",
            "confidence",
            "observation_count",
        ],
        ascending=[
            False,
            False,
            False,
        ],
        kind="stable",
    ).reset_index(drop=True)


def calculate_severity(
    *,
    mean_return: float,
    profit_factor: float,
    return_lift: float,
) -> float:
    return_loss = min(
        1.0,
        abs(
            min(
                mean_return,
                0.0,
            )
        ) / 0.05,
    )

    lift_loss = min(
        1.0,
        abs(
            min(
                return_lift,
                0.0,
            )
        ) / 0.05,
    )

    factor_loss = min(
        1.0,
        max(
            0.0,
            1.0 - profit_factor,
        ),
    )

    return round(
        return_loss * 0.40
        + lift_loss * 0.35
        + factor_loss * 0.25,
        8,
    )
