"""Deterministic market-regime classifier."""

from __future__ import annotations

import math

import pandas as pd


REGIME_TYPES = {
    "BROAD_TRENDING_RISK_ON",
    "SELECTIVE_TRENDING_RISK_ON",
    "VOLATILITY_EXPANSION",
    "VOLATILITY_COMPRESSION",
    "MEAN_REVERTING_DISPERSION",
    "CORRELATED_RISK_OFF",
    "LIQUIDITY_CONTRACTION",
    "TRANSITION",
    "NEUTRAL",
    "INSUFFICIENT_DATA",
}


def classify_regime(
    state_history: pd.DataFrame,
) -> dict:
    """Classify the latest market state and confidence."""
    if (
        state_history is None
        or state_history.empty
    ):
        return insufficient_regime()

    latest = state_history.iloc[-1]

    if int(
        latest.get(
            "asset_count",
            0,
        )
    ) < 3:
        return insufficient_regime()

    breadth_30d = number(
        latest.get(
            "positive_30d_ratio"
        )
    )

    uptrend = number(
        latest.get(
            "uptrend_ratio"
        )
    )

    downtrend = number(
        latest.get(
            "downtrend_ratio"
        )
    )

    return_30d = number(
        latest.get(
            "median_return_30d"
        )
    )

    momentum_30d = number(
        latest.get(
            "median_momentum_30d"
        )
    )

    volatility_ratio = number(
        latest.get(
            "volatility_ratio"
        )
    )

    volatility_30d = number(
        latest.get(
            "median_volatility_30d"
        )
    )

    liquidity = number(
        latest.get(
            "median_volume_ratio_30d"
        )
    )

    drawdown = number(
        latest.get(
            "median_drawdown_90d"
        )
    )

    dispersion = number(
        latest.get(
            "return_dispersion_30d"
        )
    )

    correlation = number(
        latest.get(
            "average_pairwise_correlation_30d"
        )
    )

    concentration = number(
        latest.get(
            "cross_sectional_concentration"
        )
    )

    scores = {
        "BROAD_TRENDING_RISK_ON": clamp(
            breadth_30d * 0.30
            + uptrend * 0.25
            + scale(
                return_30d,
                0.0,
                0.20,
            ) * 0.20
            + scale(
                momentum_30d,
                0.0,
                0.20,
            ) * 0.15
            + scale(
                liquidity,
                0.8,
                1.5,
            ) * 0.10
        ),
        "SELECTIVE_TRENDING_RISK_ON": clamp(
            scale(
                breadth_30d,
                0.30,
                0.70,
            ) * 0.25
            + uptrend * 0.20
            + scale(
                return_30d,
                -0.02,
                0.15,
            ) * 0.20
            + scale(
                dispersion,
                0.02,
                0.20,
            ) * 0.20
            + scale(
                concentration,
                0.10,
                0.35,
            ) * 0.15
        ),
        "VOLATILITY_EXPANSION": clamp(
            scale(
                volatility_ratio,
                1.05,
                1.80,
            ) * 0.45
            + scale(
                volatility_30d,
                0.25,
                1.20,
            ) * 0.20
            + scale(
                abs(
                    number(
                        latest.get(
                            "median_return_7d"
                        )
                    )
                ),
                0.02,
                0.20,
            ) * 0.20
            + scale(
                liquidity,
                0.9,
                1.8,
            ) * 0.15
        ),
        "VOLATILITY_COMPRESSION": clamp(
            inverse_scale(
                volatility_ratio,
                0.65,
                1.00,
            ) * 0.45
            + inverse_scale(
                volatility_30d,
                0.15,
                0.60,
            ) * 0.20
            + inverse_scale(
                dispersion,
                0.02,
                0.15,
            ) * 0.20
            + scale(
                liquidity,
                0.7,
                1.2,
            ) * 0.15
        ),
        "MEAN_REVERTING_DISPERSION": clamp(
            scale(
                dispersion,
                0.05,
                0.25,
            ) * 0.30
            + inverse_scale(
                abs(return_30d),
                0.0,
                0.15,
            ) * 0.20
            + inverse_scale(
                abs(momentum_30d),
                0.0,
                0.15,
            ) * 0.20
            + inverse_scale(
                abs(
                    uptrend - downtrend
                ),
                0.0,
                0.60,
            ) * 0.15
            + inverse_scale(
                correlation,
                0.20,
                0.80,
            ) * 0.15
        ),
        "CORRELATED_RISK_OFF": clamp(
            downtrend * 0.25
            + inverse_scale(
                breadth_30d,
                0.10,
                0.50,
            ) * 0.20
            + inverse_scale(
                return_30d,
                -0.25,
                0.0,
            ) * 0.20
            + scale(
                correlation,
                0.45,
                0.90,
            ) * 0.20
            + inverse_scale(
                drawdown,
                -0.40,
                -0.05,
            ) * 0.15
        ),
        "LIQUIDITY_CONTRACTION": clamp(
            inverse_scale(
                liquidity,
                0.40,
                1.00,
            ) * 0.45
            + inverse_scale(
                breadth_30d,
                0.20,
                0.60,
            ) * 0.15
            + inverse_scale(
                return_30d,
                -0.20,
                0.05,
            ) * 0.15
            + scale(
                volatility_ratio,
                0.90,
                1.50,
            ) * 0.15
            + inverse_scale(
                drawdown,
                -0.35,
                -0.05,
            ) * 0.10
        ),
    }

    ordered = sorted(
        scores.items(),
        key=lambda item: (
            -item[1],
            item[0],
        ),
    )

    primary, primary_score = ordered[0]

    secondary, secondary_score = (
        ordered[1]
        if len(ordered) > 1
        else ("NEUTRAL", 0.0)
    )

    score_gap = (
        primary_score
        - secondary_score
    )

    transition = detect_transition(
        state_history,
        current_primary=primary,
        current_score=primary_score,
        score_gap=score_gap,
    )

    if primary_score < 0.42:
        regime = "NEUTRAL"
    elif transition["is_transition"]:
        regime = "TRANSITION"
    else:
        regime = primary

    confidence = clamp(
        primary_score * 0.60
        + scale(
            score_gap,
            0.0,
            0.35,
        ) * 0.25
        + transition[
            "stability_score"
        ] * 0.15
    )

    return {
        "regime": regime,
        "primary_regime": primary,
        "secondary_regime": secondary,
        "confidence": round(
            confidence,
            8,
        ),
        "primary_score": round(
            primary_score,
            8,
        ),
        "secondary_score": round(
            secondary_score,
            8,
        ),
        "score_gap": round(
            score_gap,
            8,
        ),
        "is_transition": transition[
            "is_transition"
        ],
        "transition_reason": transition[
            "reason"
        ],
        "stability_score": transition[
            "stability_score"
        ],
        "component_scores": {
            key: round(value, 8)
            for key, value in scores.items()
        },
        "state": {
            key: serializable(
                latest.get(key)
            )
            for key in latest.index
        },
        "source": (
            "regime_intelligence_v1"
        ),
    }


def detect_transition(
    history: pd.DataFrame,
    *,
    current_primary: str,
    current_score: float,
    score_gap: float,
) -> dict:
    """Detect unstable or rapidly changing market states."""
    if len(history) < 5:
        return {
            "is_transition": False,
            "reason": (
                "Insufficient history for "
                "transition detection."
            ),
            "stability_score": 0.25,
        }

    recent = history.tail(5)

    breadth_change = abs(
        number(
            recent.iloc[-1].get(
                "positive_30d_ratio"
            )
        )
        - number(
            recent.iloc[0].get(
                "positive_30d_ratio"
            )
        )
    )

    volatility_change = abs(
        number(
            recent.iloc[-1].get(
                "volatility_ratio"
            )
        )
        - number(
            recent.iloc[0].get(
                "volatility_ratio"
            )
        )
    )

    correlation_change = abs(
        number(
            recent.iloc[-1].get(
                "average_pairwise_correlation_30d"
            )
        )
        - number(
            recent.iloc[0].get(
                "average_pairwise_correlation_30d"
            )
        )
    )

    unstable = (
        score_gap < 0.08
        or breadth_change >= 0.35
        or volatility_change >= 0.35
        or correlation_change >= 0.25
    )

    stability = clamp(
        1.0
        - min(
            1.0,
            breadth_change * 0.40
            + volatility_change * 0.35
            + correlation_change * 0.25
        )
    )

    reasons = []

    if score_gap < 0.08:
        reasons.append(
            "Competing regime scores are close."
        )

    if breadth_change >= 0.35:
        reasons.append(
            "Breadth changed rapidly."
        )

    if volatility_change >= 0.35:
        reasons.append(
            "Volatility structure changed rapidly."
        )

    if correlation_change >= 0.25:
        reasons.append(
            "Cross-asset correlation changed rapidly."
        )

    return {
        "is_transition": unstable,
        "reason": (
            " ".join(reasons)
            if reasons
            else (
                f"{current_primary} is stable "
                f"at score {current_score:.4f}."
            )
        ),
        "stability_score": round(
            stability,
            8,
        ),
    }


def insufficient_regime() -> dict:
    return {
        "regime": "INSUFFICIENT_DATA",
        "primary_regime": (
            "INSUFFICIENT_DATA"
        ),
        "secondary_regime": (
            "INSUFFICIENT_DATA"
        ),
        "confidence": 0.0,
        "primary_score": 0.0,
        "secondary_score": 0.0,
        "score_gap": 0.0,
        "is_transition": False,
        "transition_reason": (
            "Insufficient market history."
        ),
        "stability_score": 0.0,
        "component_scores": {},
        "state": {},
        "source": "regime_intelligence_v1",
    }


def scale(
    value: float,
    low: float,
    high: float,
) -> float:
    if high <= low:
        return 0.0

    return clamp(
        (number(value) - low)
        / (high - low)
    )


def inverse_scale(
    value: float,
    low: float,
    high: float,
) -> float:
    return 1.0 - scale(
        value,
        low,
        high,
    )


def number(
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
            float(value),
        ),
    )


def serializable(
    value,
):
    if isinstance(
        value,
        pd.Timestamp,
    ):
        return value.isoformat()

    if pd.isna(value):
        return None

    if hasattr(
        value,
        "item",
    ):
        return value.item()

    return value
