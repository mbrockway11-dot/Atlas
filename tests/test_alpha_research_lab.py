"""Tests for Atlas Alpha Research Lab v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.alpha.research_lab.metrics import (
    build_engine_metrics,
)
from atlas.investment.alpha.research_lab.promotion import (
    build_promotion_decisions,
)


def sample_trades() -> pd.DataFrame:
    rows = []

    for index in range(120):
        rows.append({
            "engine_id": "strong_engine",
            "family": "trend",
            "timestamp": (
                pd.Timestamp(
                    "2024-01-01",
                    tz="UTC",
                )
                + pd.Timedelta(
                    days=index * 3
                )
            ),
            "asset": (
                "BTC-USD"
                if index % 2 == 0
                else "ETH-USD"
            ),
            "regime": (
                "UPTREND"
                if index % 3
                else "NEUTRAL"
            ),
            "strategy_return": (
                0.035
                if index % 4
                else -0.012
            ),
        })

    for index in range(120):
        rows.append({
            "engine_id": "weak_engine",
            "family": "momentum",
            "timestamp": (
                pd.Timestamp(
                    "2024-01-01",
                    tz="UTC",
                )
                + pd.Timedelta(
                    days=index * 3
                )
            ),
            "asset": (
                "BTC-USD"
                if index % 2 == 0
                else "ETH-USD"
            ),
            "regime": "NEUTRAL",
            "strategy_return": (
                0.008
                if index % 4 == 0
                else -0.015
            ),
        })

    return pd.DataFrame(rows)


def sample_independence() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_a": "strong_engine",
            "engine_b": "weak_engine",
            "correlation": 0.20,
            "absolute_correlation": 0.20,
            "independence_score": 0.80,
        }
    ])


def test_metrics_build_engine_rows_and_curves():
    metrics, curves = build_engine_metrics(
        sample_trades(),
        transaction_cost_bps=10.0,
    )

    assert len(metrics) == 2
    assert not curves.empty

    assert {
        "trade_sharpe",
        "trade_sortino",
        "max_drawdown",
        "recovery_factor",
        "positive_asset_ratio",
        "positive_year_ratio",
    }.issubset(
        set(metrics.columns)
    )


def test_metrics_apply_transaction_cost():
    trades = pd.DataFrame([
        {
            "engine_id": "test",
            "family": "test",
            "timestamp": "2025-01-01T00:00:00Z",
            "asset": "BTC-USD",
            "regime": "TEST",
            "strategy_return": 0.01,
        }
    ])

    metrics, _ = build_engine_metrics(
        trades,
        transaction_cost_bps=10.0,
    )

    assert float(
        metrics.iloc[0]["mean_return"]
    ) == 0.009


def test_promotion_decisions_rank_strong_engine_higher():
    metrics, _ = build_engine_metrics(
        sample_trades(),
        transaction_cost_bps=10.0,
    )

    decisions = build_promotion_decisions(
        metrics,
        sample_independence(),
    )

    scores = decisions.set_index(
        "engine_id"
    )["promotion_score"]

    assert (
        float(scores["strong_engine"])
        > float(scores["weak_engine"])
    )


def test_weak_engine_is_not_promoted():
    metrics, _ = build_engine_metrics(
        sample_trades(),
        transaction_cost_bps=10.0,
    )

    decisions = build_promotion_decisions(
        metrics,
        sample_independence(),
    )

    weak = decisions[
        decisions["engine_id"].eq(
            "weak_engine"
        )
    ].iloc[0]

    assert weak["decision"] in {
        "REVISE",
        "RETIRE",
    }


def test_decision_columns_are_deterministic():
    metrics, _ = build_engine_metrics(
        sample_trades(),
        transaction_cost_bps=10.0,
    )

    first = build_promotion_decisions(
        metrics,
        sample_independence(),
    )

    second = build_promotion_decisions(
        metrics,
        sample_independence(),
    )

    pd.testing.assert_frame_equal(
        first,
        second,
    )
