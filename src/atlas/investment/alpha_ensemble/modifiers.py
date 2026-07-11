"""Bounded Learning and Regime modifiers for Alpha Ensemble v6.1."""

from __future__ import annotations

import math

import pandas as pd


LEARNING_MIN = 0.75
LEARNING_MAX = 1.10

REGIME_MIN = 0.75
REGIME_MAX = 1.25


def build_learning_modifier_map(
    recommendations: pd.DataFrame | None,
) -> dict[str, dict]:
    """Index bounded Learning Engine modifiers by engine."""
    if (
        recommendations is None
        or recommendations.empty
        or "engine_id" not in recommendations.columns
    ):
        return {}

    frame = recommendations.copy()

    if "learning_weight_multiplier" not in frame.columns:
        frame["learning_weight_multiplier"] = 1.0

    frame["learning_weight_multiplier"] = pd.to_numeric(
        frame["learning_weight_multiplier"],
        errors="coerce",
    ).fillna(1.0)

    output: dict[str, dict] = {}

    for _, row in frame.iterrows():
        engine_id = str(
            row.get("engine_id")
        )

        raw = clamp(
            finite(
                row.get(
                    "learning_weight_multiplier"
                ),
                default=1.0,
            )
        )

        # Convert the Learning Engine's 0–1 recommendation into a
        # deliberately narrow production influence band.
        bounded = (
            LEARNING_MIN
            + raw
            * (
                LEARNING_MAX
                - LEARNING_MIN
            )
        )

        output[engine_id] = {
            "learning_raw_multiplier": raw,
            "learning_modifier": round(
                bounded,
                8,
            ),
            "learning_recommendation": str(
                row.get(
                    "recommendation",
                    "",
                )
            ),
            "learning_reliability": finite(
                row.get(
                    "reliability"
                )
            ),
        }

    return output


def build_regime_modifier_map(
    suitability: pd.DataFrame | None,
) -> dict[str, dict]:
    """Index bounded Regime Intelligence modifiers by engine."""
    if (
        suitability is None
        or suitability.empty
        or "engine_id" not in suitability.columns
    ):
        return {}

    frame = suitability.copy()

    if "effective_suitability" not in frame.columns:
        frame["effective_suitability"] = 0.50

    frame["effective_suitability"] = pd.to_numeric(
        frame["effective_suitability"],
        errors="coerce",
    ).fillna(0.50)

    output: dict[str, dict] = {}

    for _, row in frame.iterrows():
        engine_id = str(
            row.get("engine_id")
        )

        raw = clamp(
            finite(
                row.get(
                    "effective_suitability"
                ),
                default=0.50,
            )
        )

        bounded = (
            REGIME_MIN
            + raw
            * (
                REGIME_MAX
                - REGIME_MIN
            )
        )

        output[engine_id] = {
            "regime_raw_suitability": raw,
            "regime_modifier": round(
                bounded,
                8,
            ),
            "market_regime": str(
                row.get(
                    "market_regime",
                    "UNKNOWN",
                )
            ),
            "regime_confidence": finite(
                row.get(
                    "regime_confidence"
                )
            ),
        }

    return output


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


def clamp(
    value: float,
) -> float:
    return max(
        0.0,
        min(
            1.0,
            finite(value),
        ),
    )
