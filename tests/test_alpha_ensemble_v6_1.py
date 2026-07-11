"""Tests for Alpha Ensemble v6.1 adaptive governance."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)


def decisions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "promoted",
            "family": "drawdown_recovery",
            "decision": "PROMOTE",
            "promotion_score": 0.75,
            "performance_score": 0.75,
            "stability_score": 0.75,
            "risk_score": 0.70,
            "independence_score": 0.50,
            "portfolio_sharpe": 0.80,
            "portfolio_recovery_factor": 1.10,
            "hard_failures": "",
        },
        {
            "engine_id": "kept",
            "family": "volatility_compression",
            "decision": "KEEP",
            "promotion_score": 0.65,
            "performance_score": 0.65,
            "stability_score": 0.70,
            "risk_score": 0.70,
            "independence_score": 0.40,
            "portfolio_sharpe": 0.60,
            "portfolio_recovery_factor": 0.80,
            "hard_failures": "",
        },
        {
            "engine_id": "retired",
            "family": "mean_reversion",
            "decision": "RETIRE",
            "promotion_score": 0.30,
            "performance_score": 0.30,
            "stability_score": 0.30,
            "risk_score": 0.30,
            "independence_score": 0.80,
            "portfolio_sharpe": -0.20,
            "portfolio_recovery_factor": -0.50,
            "hard_failures": "NONPOSITIVE_EXPECTANCY",
        },
    ])


def learning() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "promoted",
            "learning_weight_multiplier": 1.0,
            "reliability": 0.75,
            "recommendation": "SUSTAIN_PROMOTION",
        },
        {
            "engine_id": "kept",
            "learning_weight_multiplier": 0.6,
            "reliability": 0.60,
            "recommendation": "MAINTAIN_RESEARCH_WEIGHT",
        },
        {
            "engine_id": "retired",
            "learning_weight_multiplier": 1.0,
            "reliability": 1.0,
            "recommendation": "SUSTAIN_PROMOTION",
        },
    ])


def regime() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "promoted",
            "effective_suitability": 0.65,
            "market_regime": "TRANSITION",
            "regime_confidence": 0.60,
        },
        {
            "engine_id": "kept",
            "effective_suitability": 0.55,
            "market_regime": "TRANSITION",
            "regime_confidence": 0.60,
        },
        {
            "engine_id": "retired",
            "effective_suitability": 1.0,
            "market_regime": "TRANSITION",
            "regime_confidence": 0.60,
        },
    ])


def test_retired_engine_cannot_be_revived():
    result = build_engine_governance(
        decisions(),
        learning(),
        regime(),
    ).set_index("engine_id")

    assert not bool(
        result.loc[
            "retired",
            "eligible",
        ]
    )

    assert (
        float(
            result.loc[
                "retired",
                "governance_weight",
            ]
        )
        == 0.0
    )


def test_final_weights_sum_to_one():
    result = build_engine_governance(
        decisions(),
        learning(),
        regime(),
    )

    eligible = result[
        result["eligible"]
    ]

    assert round(
        float(
            eligible[
                "governance_weight"
            ].sum()
        ),
        8,
    ) == 1.0


def test_modifiers_are_bounded():
    result = build_engine_governance(
        decisions(),
        learning(),
        regime(),
    )

    assert result[
        "learning_modifier"
    ].between(
        0.75,
        1.10,
    ).all()

    assert result[
        "regime_modifier"
    ].between(
        0.75,
        1.25,
    ).all()


def test_missing_adaptive_inputs_preserves_base_governance():
    result = build_engine_governance(
        decisions()
    )

    eligible = result[
        result["eligible"]
    ]

    assert round(
        float(
            eligible[
                "governance_weight"
            ].sum()
        ),
        8,
    ) == 1.0

    assert (
        eligible[
            "learning_modifier"
        ]
        == 1.0
    ).all()

    assert (
        eligible[
            "regime_modifier"
        ]
        == 1.0
    ).all()


def test_governance_is_deterministic():
    first = build_engine_governance(
        decisions(),
        learning(),
        regime(),
    )

    second = build_engine_governance(
        decisions(),
        learning(),
        regime(),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )
