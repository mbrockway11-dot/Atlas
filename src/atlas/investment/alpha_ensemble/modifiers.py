"""Bounded adaptive modifiers for Ensemble Intelligence v7."""

from __future__ import annotations

import math

import pandas as pd


LEARNING_MIN = 0.75
LEARNING_MAX = 1.10

REGIME_MIN = 0.75
REGIME_MAX = 1.25

FUSION_MIN = 0.80
FUSION_MAX = 1.20


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


def build_fusion_modifier_map(
    context_modifiers: pd.DataFrame | None,
) -> dict[str, dict]:
    """Index bounded Macro-Regime Fusion modifiers by engine."""
    if (
        context_modifiers is None
        or context_modifiers.empty
        or "engine_id" not in context_modifiers.columns
    ):
        return {}

    frame = context_modifiers.copy()

    if "effective_context_modifier" not in frame.columns:
        frame["effective_context_modifier"] = 1.0

    frame["effective_context_modifier"] = pd.to_numeric(
        frame["effective_context_modifier"],
        errors="coerce",
    ).fillna(1.0)

    output: dict[str, dict] = {}

    for _, row in frame.iterrows():
        engine_id = str(
            row.get("engine_id")
        )

        raw = finite(
            row.get(
                "effective_context_modifier"
            ),
            default=1.0,
        )

        bounded = max(
            FUSION_MIN,
            min(
                FUSION_MAX,
                raw,
            ),
        )

        output[engine_id] = {
            "fusion_raw_modifier": round(
                raw,
                8,
            ),
            "fusion_modifier": round(
                bounded,
                8,
            ),
            "fused_regime": str(
                row.get(
                    "fused_regime",
                    "UNKNOWN",
                )
            ),
            "fusion_confidence": finite(
                row.get(
                    "fusion_confidence"
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
