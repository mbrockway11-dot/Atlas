"""Feature-state analysis for Meta Research Engine v1."""

from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.meta_research.config import (
    CATEGORICAL_COLUMNS,
    FEATURE_COLUMNS,
    MIN_FEATURE_COVERAGE,
    MIN_SEGMENT_TRADES,
)
from atlas.investment.meta_research.statistics import (
    confidence_score,
    summarize_returns,
)


INTERACTION_COLUMNS = [
    "engine_id",
    "family",
    "feature",
    "feature_type",
    "state",
    "observation_count",
    "coverage_ratio",
    "win_rate",
    "mean_return",
    "median_return",
    "profit_factor",
    "engine_mean_return",
    "return_lift",
    "confidence",
    "evidence_status",
]


def build_feature_interactions(
    evidence: pd.DataFrame,
) -> pd.DataFrame:
    if evidence is None or evidence.empty:
        return pd.DataFrame(
            columns=INTERACTION_COLUMNS
        )

    rows = []

    for engine_id, engine_group in (
        evidence.groupby(
            "engine_id",
            sort=True,
        )
    ):
        engine_metrics = summarize_returns(
            engine_group[
                "strategy_return"
            ]
        )

        engine_mean = engine_metrics[
            "mean_return"
        ]

        family = str(
            engine_group[
                "family"
            ].iloc[0]
        )

        for feature in FEATURE_COLUMNS:
            if feature not in engine_group.columns:
                continue

            numeric = pd.to_numeric(
                engine_group[feature],
                errors="coerce",
            )

            coverage = float(
                numeric.notna().mean()
            )

            if coverage < MIN_FEATURE_COVERAGE:
                continue

            states = build_numeric_states(
                numeric
            )

            rows.extend(
                summarize_states(
                    engine_id=engine_id,
                    family=family,
                    feature=feature,
                    feature_type="NUMERIC_TERCILE",
                    states=states,
                    group=engine_group,
                    engine_mean=engine_mean,
                )
            )

        for feature in CATEGORICAL_COLUMNS:
            if feature not in engine_group.columns:
                continue

            values = (
                engine_group[feature]
                .fillna("UNKNOWN")
                .astype(str)
            )

            rows.extend(
                summarize_states(
                    engine_id=engine_id,
                    family=family,
                    feature=feature,
                    feature_type="CATEGORICAL",
                    states=values,
                    group=engine_group,
                    engine_mean=engine_mean,
                )
            )

    if not rows:
        return pd.DataFrame(
            columns=INTERACTION_COLUMNS
        )

    return pd.DataFrame(
        rows,
        columns=INTERACTION_COLUMNS,
    ).sort_values(
        [
            "confidence",
            "observation_count",
            "engine_id",
            "feature",
            "state",
        ],
        ascending=[
            False,
            False,
            True,
            True,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def build_numeric_states(
    values: pd.Series,
) -> pd.Series:
    valid = values.dropna()

    result = pd.Series(
        "UNKNOWN",
        index=values.index,
        dtype=object,
    )

    if valid.empty:
        return result

    low = float(
        valid.quantile(
            1.0 / 3.0
        )
    )

    high = float(
        valid.quantile(
            2.0 / 3.0
        )
    )

    if abs(
        high - low
    ) <= 1e-12:
        result.loc[
            values.notna()
        ] = "MID"

        return result

    result.loc[
        values <= low
    ] = "LOW"

    result.loc[
        (
            values > low
        )
        & (
            values < high
        )
    ] = "MID"

    result.loc[
        values >= high
    ] = "HIGH"

    return result


def summarize_states(
    *,
    engine_id: str,
    family: str,
    feature: str,
    feature_type: str,
    states: pd.Series,
    group: pd.DataFrame,
    engine_mean: float,
) -> list[dict]:
    rows = []

    valid_mask = states.ne(
        "UNKNOWN"
    )

    available_count = int(
        valid_mask.sum()
    )

    if available_count <= 0:
        return rows

    for state in sorted(
        states[
            valid_mask
        ].unique().tolist()
    ):
        segment = group.loc[
            states.eq(state)
        ]

        metrics = summarize_returns(
            segment[
                "strategy_return"
            ]
        )

        count = metrics[
            "observation_count"
        ]

        coverage_ratio = (
            count
            / max(
                available_count,
                1,
            )
        )

        return_lift = (
            metrics[
                "mean_return"
            ]
            - engine_mean
        )

        consistency = abs(
            metrics["win_rate"]
            - 0.50
        ) * 2.0

        confidence = confidence_score(
            observations=count,
            effect_size=return_lift,
            consistency=consistency,
            minimum_observations=(
                MIN_SEGMENT_TRADES
            ),
        )

        rows.append({
            "engine_id": engine_id,
            "family": family,
            "feature": feature,
            "feature_type": (
                feature_type
            ),
            "state": str(state),
            "observation_count": count,
            "coverage_ratio": round(
                coverage_ratio,
                8,
            ),
            "win_rate": metrics[
                "win_rate"
            ],
            "mean_return": metrics[
                "mean_return"
            ],
            "median_return": metrics[
                "median_return"
            ],
            "profit_factor": metrics[
                "profit_factor"
            ],
            "engine_mean_return": (
                engine_mean
            ),
            "return_lift": round(
                return_lift,
                8,
            ),
            "confidence": confidence,
            "evidence_status": (
                "SUFFICIENT"
                if count
                >= MIN_SEGMENT_TRADES
                else "LOW_SAMPLE"
            ),
        })

    return rows
