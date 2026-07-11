"""Tests for Macro-Regime Fusion v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.macro_regime_fusion.fusion import (
    build_fused_context,
)
from atlas.investment.macro_regime_fusion.modifiers import (
    build_fused_engine_modifiers,
)


def macro_report() -> dict:
    return {
        "macro_environment": {
            "macro_regime": (
                "RESTRICTIVE_STABILITY"
            ),
            "confidence": 0.52,
            "risk_pressure": 0.46,
            "liquidity_support": 0.49,
            "inflation_pressure": 0.65,
            "growth_stress": 0.27,
            "policy_restriction": 0.75,
            "credit_stress": 0.35,
        }
    }


def regime_report() -> dict:
    return {
        "regime": {
            "regime": "TRANSITION",
            "primary_regime": (
                "MEAN_REVERTING_DISPERSION"
            ),
            "confidence": 0.59,
            "stability_score": 0.86,
        }
    }


def test_restrictive_transition_is_detected():
    context = build_fused_context(
        macro_report(),
        regime_report(),
    )

    assert (
        context["fused_regime"]
        == "RESTRICTIVE_TRANSITION"
    )


def test_context_controls_are_bounded():
    context = build_fused_context(
        macro_report(),
        regime_report(),
    )

    controls = context["controls"]

    assert (
        0.55
        <= controls[
            "risk_budget_multiplier"
        ]
        <= 1.10
    )

    assert (
        0.10
        <= controls[
            "minimum_cash_weight"
        ]
        <= 0.70
    )

    assert (
        0.40
        <= controls[
            "conviction_ceiling"
        ]
        <= 0.90
    )


def test_fusion_is_deterministic():
    first = build_fused_context(
        macro_report(),
        regime_report(),
    )

    second = build_fused_context(
        macro_report(),
        regime_report(),
    )

    assert first == second


def test_engine_modifiers_are_bounded():
    context = build_fused_context(
        macro_report(),
        regime_report(),
    )

    engines = pd.DataFrame([
        {
            "engine_id": "recovery",
            "family": "drawdown_recovery",
        },
        {
            "engine_id": "trend",
            "family": "trend",
        },
    ])

    rows = build_fused_engine_modifiers(
        context,
        engines,
    )

    assert rows

    for row in rows:
        assert (
            0.80
            <= row[
                "effective_context_modifier"
            ]
            <= 1.20
        )


def test_fusion_does_not_emit_execution_instruction():
    context = build_fused_context(
        macro_report(),
        regime_report(),
    )

    assert (
        context[
            "controls"
        ][
            "execution_instruction"
        ]
        is False
    )
