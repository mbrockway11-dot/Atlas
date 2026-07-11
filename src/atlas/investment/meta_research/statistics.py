"""Statistical helpers for Meta Research Engine v1."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd


def summarize_returns(
    returns: pd.Series,
) -> dict:
    values = pd.to_numeric(
        returns,
        errors="coerce",
    ).replace(
        [
            np.inf,
            -np.inf,
        ],
        np.nan,
    ).dropna()

    if values.empty:
        return {
            "observation_count": 0,
            "win_rate": 0.0,
            "mean_return": 0.0,
            "median_return": 0.0,
            "return_std": 0.0,
            "profit_factor": 0.0,
            "downside_mean": 0.0,
            "best_return": 0.0,
            "worst_return": 0.0,
        }

    gains = float(
        values[
            values > 0
        ].sum()
    )

    losses = abs(
        float(
            values[
                values < 0
            ].sum()
        )
    )

    profit_factor = (
        gains / losses
        if losses > 1e-12
        else (
            999.0
            if gains > 0
            else 0.0
        )
    )

    downside = values[
        values < 0
    ]

    return {
        "observation_count": int(
            len(values)
        ),
        "win_rate": round(
            float(
                (
                    values > 0
                ).mean()
            ),
            8,
        ),
        "mean_return": round(
            float(
                values.mean()
            ),
            8,
        ),
        "median_return": round(
            float(
                values.median()
            ),
            8,
        ),
        "return_std": round(
            float(
                values.std(
                    ddof=0
                )
            ),
            8,
        ),
        "profit_factor": round(
            finite(
                profit_factor
            ),
            8,
        ),
        "downside_mean": round(
            float(
                downside.mean()
            )
            if not downside.empty
            else 0.0,
            8,
        ),
        "best_return": round(
            float(
                values.max()
            ),
            8,
        ),
        "worst_return": round(
            float(
                values.min()
            ),
            8,
        ),
    }


def confidence_score(
    *,
    observations: int,
    effect_size: float,
    consistency: float,
    minimum_observations: int,
) -> float:
    sample_score = min(
        1.0,
        observations
        / max(
            minimum_observations * 4,
            1,
        ),
    )

    effect_score = min(
        1.0,
        abs(
            effect_size
        ) / 0.04,
    )

    consistency_score = max(
        0.0,
        min(
            1.0,
            consistency,
        ),
    )

    return round(
        sample_score * 0.45
        + effect_score * 0.35
        + consistency_score * 0.20,
        8,
    )


def finite(
    value,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )
