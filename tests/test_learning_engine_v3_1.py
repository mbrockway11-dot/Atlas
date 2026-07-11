"""Tests for Learning Engine v3.1 persistent memory."""

from __future__ import annotations

import pandas as pd

from atlas.investment.learning.engine_learning import (
    build_engine_learning_recommendations,
)
from atlas.investment.learning.strategy_memory import (
    build_strategy_memory_snapshot,
    build_strategy_memory_summary,
)


def research_decisions() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "strong_engine",
            "family": "trend",
            "decision": "PROMOTE",
            "promotion_score": 0.80,
            "performance_score": 0.75,
            "stability_score": 0.75,
            "risk_score": 0.70,
            "independence_score": 0.60,
            "trade_count": 200,
            "mean_return": 0.02,
            "profit_factor": 1.40,
            "portfolio_cumulative_return": 0.30,
            "portfolio_sharpe": 0.80,
            "portfolio_recovery_factor": 1.10,
            "max_drawdown": -0.25,
            "hard_failures": "",
        },
        {
            "engine_id": "weak_engine",
            "family": "mean_reversion",
            "decision": "RETIRE",
            "promotion_score": 0.25,
            "performance_score": 0.20,
            "stability_score": 0.30,
            "risk_score": 0.30,
            "independence_score": 0.50,
            "trade_count": 300,
            "mean_return": -0.01,
            "profit_factor": 0.80,
            "portfolio_cumulative_return": -0.40,
            "portfolio_sharpe": -0.50,
            "portfolio_recovery_factor": -0.80,
            "max_drawdown": -0.70,
            "hard_failures": "NONPOSITIVE_EXPECTANCY",
        },
    ])


def test_strategy_snapshot_preserves_engine_decisions():
    snapshot = build_strategy_memory_snapshot(
        research_decisions()
    )

    assert len(snapshot) == 2

    indexed = snapshot.set_index(
        "engine_id"
    )

    assert (
        indexed.loc[
            "strong_engine",
            "decision",
        ]
        == "PROMOTE"
    )

    assert (
        indexed.loc[
            "weak_engine",
            "decision",
        ]
        == "RETIRE"
    )


def test_strategy_summary_builds_reliability():
    first = build_strategy_memory_snapshot(
        research_decisions()
    )

    second = first.copy()

    second["observed_at"] = (
        pd.Timestamp.now(
            tz="UTC"
        )
        + pd.Timedelta(
            minutes=1
        )
    ).isoformat()

    memory = pd.concat(
        [
            first,
            second,
        ],
        ignore_index=True,
    )

    summary = build_strategy_memory_summary(
        memory
    )

    assert len(summary) == 2

    assert summary[
        "recency_weighted_reliability"
    ].between(
        0.0,
        1.0,
    ).all()


def test_learning_recommendations_exclude_retired_engine():
    snapshot = build_strategy_memory_snapshot(
        research_decisions()
    )

    summary = build_strategy_memory_summary(
        snapshot
    )

    recommendations = (
        build_engine_learning_recommendations(
            summary
        )
    )

    indexed = {
        row["engine_id"]: row
        for row in recommendations
    }

    assert (
        indexed[
            "weak_engine"
        ][
            "recommendation"
        ]
        == "EXCLUDE_FROM_ENSEMBLE"
    )

    assert (
        indexed[
            "weak_engine"
        ][
            "learning_weight_multiplier"
        ]
        == 0.0
    )


def test_promoted_engine_receives_positive_multiplier():
    snapshot = build_strategy_memory_snapshot(
        research_decisions()
    )

    summary = build_strategy_memory_summary(
        snapshot
    )

    recommendations = (
        build_engine_learning_recommendations(
            summary
        )
    )

    indexed = {
        row["engine_id"]: row
        for row in recommendations
    }

    assert (
        indexed[
            "strong_engine"
        ][
            "learning_weight_multiplier"
        ]
        > 0.0
    )


def test_strategy_memory_is_deterministic_for_same_input():
    snapshot = build_strategy_memory_snapshot(
        research_decisions()
    )

    first = build_strategy_memory_summary(
        snapshot
    )

    second = build_strategy_memory_summary(
        snapshot
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )
