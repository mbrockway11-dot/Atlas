"""Tests for Alpha Ensemble v6 research governance."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha_ensemble.engine_votes import (
    build_research_engine_votes,
)
from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)


def decisions_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "promoted_engine",
            "family": "trend",
            "decision": "PROMOTE",
            "promotion_score": 0.80,
            "performance_score": 0.80,
            "stability_score": 0.75,
            "risk_score": 0.70,
            "independence_score": 0.60,
            "portfolio_sharpe": 0.80,
            "portfolio_recovery_factor": 1.20,
            "hard_failures": "",
        },
        {
            "engine_id": "keep_engine",
            "family": "volatility",
            "decision": "KEEP",
            "promotion_score": 0.65,
            "performance_score": 0.70,
            "stability_score": 0.70,
            "risk_score": 0.75,
            "independence_score": 0.50,
            "portfolio_sharpe": 0.60,
            "portfolio_recovery_factor": 0.80,
            "hard_failures": "",
        },
        {
            "engine_id": "retired_engine",
            "family": "momentum",
            "decision": "RETIRE",
            "promotion_score": 0.30,
            "performance_score": 0.20,
            "stability_score": 0.30,
            "risk_score": 0.50,
            "independence_score": 0.70,
            "portfolio_sharpe": -0.20,
            "portfolio_recovery_factor": -0.50,
            "hard_failures": "NONPOSITIVE_EXPECTANCY",
        },
    ])


def signals_frame() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "promoted_engine",
            "asset": "BTC-USD",
            "normalized_score": 0.80,
            "confidence": 0.90,
        },
        {
            "engine_id": "keep_engine",
            "asset": "BTC-USD",
            "normalized_score": 0.60,
            "confidence": 0.80,
        },
        {
            "engine_id": "retired_engine",
            "asset": "BTC-USD",
            "normalized_score": 0.00,
            "confidence": 1.00,
        },
    ])


def test_governance_admits_only_promote_and_keep():
    governance = build_engine_governance(
        decisions_frame()
    )

    indexed = governance.set_index(
        "engine_id"
    )

    assert bool(
        indexed.loc[
            "promoted_engine",
            "eligible",
        ]
    )

    assert bool(
        indexed.loc[
            "keep_engine",
            "eligible",
        ]
    )

    assert not bool(
        indexed.loc[
            "retired_engine",
            "eligible",
        ]
    )


def test_governance_weights_sum_to_one():
    governance = build_engine_governance(
        decisions_frame()
    )

    eligible = governance[
        governance["eligible"]
    ]

    assert round(
        float(
            eligible[
                "governance_weight"
            ].sum()
        ),
        8,
    ) == 1.0


def test_promoted_engine_receives_more_weight_than_keep():
    governance = build_engine_governance(
        decisions_frame()
    ).set_index(
        "engine_id"
    )

    assert (
        float(
            governance.loc[
                "promoted_engine",
                "governance_weight",
            ]
        )
        > float(
            governance.loc[
                "keep_engine",
                "governance_weight",
            ]
        )
    )


def test_retired_engine_does_not_influence_vote():
    governance = build_engine_governance(
        decisions_frame()
    )

    votes = build_research_engine_votes(
        signals_frame(),
        governance,
    )

    btc = votes["BTC-USD"]

    assert (
        "retired_engine"
        not in btc[
            "research_engine_ids"
        ]
    )

    assert btc["research_engine_count"] == 2
    assert btc["research_engine_vote"] > 0.60


def test_engine_vote_is_deterministic():
    governance = build_engine_governance(
        decisions_frame()
    )

    first = build_research_engine_votes(
        signals_frame(),
        governance,
    )

    second = build_research_engine_votes(
        signals_frame(),
        governance,
    )

    assert first == second


def test_nan_hard_failures_do_not_block_eligible_engine():
    decisions = pd.DataFrame([
        {
            "engine_id": "eligible_engine",
            "family": "trend",
            "decision": "PROMOTE",
            "promotion_score": 0.80,
            "performance_score": 0.75,
            "stability_score": 0.70,
            "risk_score": 0.70,
            "independence_score": 0.60,
            "portfolio_sharpe": 0.75,
            "portfolio_recovery_factor": 1.10,
            "hard_failures": float("nan"),
        }
    ])

    governance = build_engine_governance(
        decisions
    )

    row = governance.iloc[0]

    assert bool(row["eligible"])
    assert float(
        row["governance_weight"]
    ) == 1.0
    assert row["hard_failures"] == ""
