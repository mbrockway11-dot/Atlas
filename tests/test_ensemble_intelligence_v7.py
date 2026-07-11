"""Tests for Ensemble Intelligence v7."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha_ensemble.contributions import (
    build_contribution_ledger,
)
from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)


def decisions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "engine_a",
            "family": "trend",
            "decision": "PROMOTE",
            "promotion_score": 0.80,
            "performance_score": 0.75,
            "stability_score": 0.70,
            "risk_score": 0.70,
            "independence_score": 0.70,
            "portfolio_sharpe": 0.80,
            "portfolio_recovery_factor": 1.10,
            "hard_failures": "",
        },
        {
            "engine_id": "engine_b",
            "family": "volatility_compression",
            "decision": "KEEP",
            "promotion_score": 0.65,
            "performance_score": 0.65,
            "stability_score": 0.65,
            "risk_score": 0.65,
            "independence_score": 0.60,
            "portfolio_sharpe": 0.60,
            "portfolio_recovery_factor": 0.80,
            "hard_failures": "",
        },
        {
            "engine_id": "engine_c",
            "family": "mean_reversion",
            "decision": "RETIRE",
            "promotion_score": 0.90,
            "performance_score": 0.90,
            "stability_score": 0.90,
            "risk_score": 0.90,
            "independence_score": 0.90,
            "portfolio_sharpe": 1.50,
            "portfolio_recovery_factor": 2.00,
            "hard_failures": "",
        },
    ])


def context_modifiers() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "engine_a",
            "effective_context_modifier": 1.10,
            "fused_regime": "RESTRICTIVE_TRANSITION",
            "fusion_confidence": 0.60,
        },
        {
            "engine_id": "engine_b",
            "effective_context_modifier": 1.05,
            "fused_regime": "RESTRICTIVE_TRANSITION",
            "fusion_confidence": 0.60,
        },
        {
            "engine_id": "engine_c",
            "effective_context_modifier": 1.20,
            "fused_regime": "RESTRICTIVE_TRANSITION",
            "fusion_confidence": 0.60,
        },
    ])


def test_retired_engine_remains_ineligible_with_fusion():
    result = build_engine_governance(
        decisions(),
        context_modifiers=(
            context_modifiers()
        ),
    ).set_index("engine_id")

    assert not bool(
        result.loc[
            "engine_c",
            "eligible",
        ]
    )

    assert (
        float(
            result.loc[
                "engine_c",
                "governance_weight",
            ]
        )
        == 0.0
    )


def test_governance_weights_normalize():
    result = build_engine_governance(
        decisions(),
        context_modifiers=(
            context_modifiers()
        ),
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


def test_fusion_modifier_is_bounded():
    result = build_engine_governance(
        decisions(),
        context_modifiers=(
            context_modifiers()
        ),
    )

    assert result[
        "fusion_modifier"
    ].between(
        0.80,
        1.20,
    ).all()


def test_contribution_ledger_excludes_retired_engines():
    governance = build_engine_governance(
        decisions(),
        context_modifiers=(
            context_modifiers()
        ),
    )

    signals = pd.DataFrame([
        {
            "asset": "BTC-USD",
            "engine_id": "engine_a",
            "normalized_score": 0.80,
            "confidence": 0.90,
            "direction": "LONG",
        },
        {
            "asset": "BTC-USD",
            "engine_id": "engine_b",
            "normalized_score": 0.60,
            "confidence": 0.80,
            "direction": "LONG",
        },
        {
            "asset": "BTC-USD",
            "engine_id": "engine_c",
            "normalized_score": 1.00,
            "confidence": 1.00,
            "direction": "LONG",
        },
    ])

    ledger = build_contribution_ledger(
        signals,
        governance,
    )

    assert set(
        ledger["engine_id"]
    ) == {
        "engine_a",
        "engine_b",
    }


def test_contribution_shares_sum_to_one():
    governance = build_engine_governance(
        decisions(),
        context_modifiers=(
            context_modifiers()
        ),
    )

    signals = pd.DataFrame([
        {
            "asset": "BTC-USD",
            "engine_id": "engine_a",
            "normalized_score": 0.80,
            "confidence": 0.90,
        },
        {
            "asset": "BTC-USD",
            "engine_id": "engine_b",
            "normalized_score": 0.60,
            "confidence": 0.80,
        },
    ])

    ledger = build_contribution_ledger(
        signals,
        governance,
    )

    assert round(
        float(
            ledger[
                "contribution_share"
            ].sum()
        ),
        8,
    ) == 1.0
