"""Tests for Portfolio Promotion Lab v1."""

from __future__ import annotations

import pandas as pd

from atlas.investment.portfolio_promotion_lab.evaluator import (
    build_asset_return_matrix,
    evaluate_portfolio_windows,
    normalize_portfolio,
)
from atlas.investment.portfolio_promotion_lab.promotion import (
    compare_portfolios,
)


def market_history() -> pd.DataFrame:
    rows = []

    for day in range(220):
        timestamp = (
            pd.Timestamp(
                "2025-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        rows.extend([
            {
                "timestamp": timestamp,
                "asset": "BTC-USD",
                "close": 100 + day * 1.0,
            },
            {
                "timestamp": timestamp,
                "asset": "ETH-USD",
                "close": 100 + day * 0.6,
            },
            {
                "timestamp": timestamp,
                "asset": "SOL-USD",
                "close": 100 + day * 0.3,
            },
        ])

    return pd.DataFrame(rows)


def baseline_portfolio() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset": "BTC-USD",
            "target_weight": 0.40,
        },
        {
            "asset": "ETH-USD",
            "target_weight": 0.30,
        },
        {
            "asset": "CASH",
            "target_weight": 0.30,
        },
    ])


def candidate_portfolio() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset": "BTC-USD",
            "target_weight": 0.30,
        },
        {
            "asset": "ETH-USD",
            "target_weight": 0.20,
        },
        {
            "asset": "SOL-USD",
            "target_weight": 0.15,
        },
        {
            "asset": "CASH",
            "target_weight": 0.35,
        },
    ])


def test_weights_are_normalized():
    weights = normalize_portfolio(
        candidate_portfolio()
    )

    assert round(
        float(weights.sum()),
        8,
    ) == 1.0


def test_return_matrix_is_created():
    returns = build_asset_return_matrix(
        market_history()
    )

    assert not returns.empty
    assert "BTC-USD" in returns.columns


def test_window_metrics_are_generated():
    returns = build_asset_return_matrix(
        market_history()
    )

    weights = normalize_portfolio(
        candidate_portfolio()
    )

    metrics = evaluate_portfolio_windows(
        portfolio_name="candidate",
        weights=weights,
        returns=returns,
        windows=[
            30,
            60,
            90,
            180,
        ],
        reference_weights=None,
    )

    assert len(metrics) == 4
    assert (
        metrics[
            "observation_count"
        ] > 0
    ).all()


def test_comparison_is_deterministic():
    returns = build_asset_return_matrix(
        market_history()
    )

    baseline_weights = normalize_portfolio(
        baseline_portfolio()
    )

    candidate_weights = normalize_portfolio(
        candidate_portfolio()
    )

    baseline = evaluate_portfolio_windows(
        portfolio_name="baseline",
        weights=baseline_weights,
        returns=returns,
        windows=[
            30,
            60,
            90,
            180,
        ],
        reference_weights=None,
    )

    candidate = evaluate_portfolio_windows(
        portfolio_name="candidate",
        weights=candidate_weights,
        returns=returns,
        windows=[
            30,
            60,
            90,
            180,
        ],
        reference_weights=baseline_weights,
    )

    first_comparison, first_decision = (
        compare_portfolios(
            baseline,
            candidate,
        )
    )

    second_comparison, second_decision = (
        compare_portfolios(
            baseline,
            candidate,
        )
    )

    pd.testing.assert_frame_equal(
        first_comparison,
        second_comparison,
    )

    assert (
        first_decision
        == second_decision
    )


def test_lab_never_changes_execution_target():
    returns = build_asset_return_matrix(
        market_history()
    )

    baseline = evaluate_portfolio_windows(
        portfolio_name="baseline",
        weights=normalize_portfolio(
            baseline_portfolio()
        ),
        returns=returns,
        windows=[
            30,
            60,
            90,
            180,
        ],
        reference_weights=None,
    )

    candidate = evaluate_portfolio_windows(
        portfolio_name="candidate",
        weights=normalize_portfolio(
            candidate_portfolio()
        ),
        returns=returns,
        windows=[
            30,
            60,
            90,
            180,
        ],
        reference_weights=normalize_portfolio(
            baseline_portfolio()
        ),
    )

    _, decision = compare_portfolios(
        baseline,
        candidate,
    )

    assert (
        decision[
            "execution_target_changed"
        ]
        is False
    )
