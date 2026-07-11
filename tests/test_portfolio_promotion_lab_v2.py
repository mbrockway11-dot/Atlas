"""Tests for Portfolio Promotion Lab v2."""

from __future__ import annotations

import pandas as pd

from atlas.investment.portfolio_promotion_lab_v2.baseline import (
    reconstruct_baseline_portfolio,
)
from atlas.investment.portfolio_promotion_lab_v2.candidate import (
    build_governance_map,
    reconstruct_candidate_portfolio,
)
from atlas.investment.portfolio_promotion_lab_v2.data import (
    build_price_matrix,
    build_return_matrix,
    normalize_engine_signals,
    normalize_market_history,
)
from atlas.investment.portfolio_promotion_lab_v2.simulator import (
    run_walk_forward,
)


def market_history() -> pd.DataFrame:
    rows = []

    for day in range(420):
        timestamp = (
            pd.Timestamp(
                "2025-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        for asset, slope in [
            ("BTC-USD", 0.40),
            ("ETH-USD", 0.30),
            ("SOL-USD", 0.20),
        ]:
            close = (
                100.0
                + day * slope
            )

            rows.append({
                "timestamp": timestamp,
                "asset": asset,
                "close": close,
                "cross_sectional_score": (
                    slope
                ),
            })

    return pd.DataFrame(rows)


def engine_signals() -> pd.DataFrame:
    rows = []

    for day in range(420):
        timestamp = (
            pd.Timestamp(
                "2025-01-01",
                tz="UTC",
            )
            + pd.Timedelta(
                days=day
            )
        )

        for asset, score in [
            ("BTC-USD", 0.80),
            ("ETH-USD", 0.70),
            ("SOL-USD", 0.60),
        ]:
            rows.extend([
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "engine_id": (
                        "engine_a"
                    ),
                    "normalized_score": (
                        score
                    ),
                    "confidence": 0.90,
                },
                {
                    "timestamp": timestamp,
                    "asset": asset,
                    "engine_id": (
                        "engine_b"
                    ),
                    "normalized_score": (
                        score - 0.05
                    ),
                    "confidence": 0.80,
                },
            ])

    return pd.DataFrame(rows)


def governance() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "engine_id": "engine_a",
            "eligible": True,
            "governance_weight": 0.70,
        },
        {
            "engine_id": "engine_b",
            "eligible": True,
            "governance_weight": 0.30,
        },
        {
            "engine_id": "retired",
            "eligible": False,
            "governance_weight": 1.00,
        },
    ])


def test_baseline_reconstructs_using_date_snapshot():
    market = normalize_market_history(
        market_history()
    )

    date = market[
        "date"
    ].iloc[200]

    weights = reconstruct_baseline_portfolio(
        market,
        rebalance_date=date,
    )

    assert round(
        float(weights.sum()),
        8,
    ) == 1.0

    assert (
        weights.get(
            "CASH",
            0.0,
        )
        >= 0.10
    )


def test_candidate_reconstructs_without_future_returns():
    market = normalize_market_history(
        market_history()
    )

    signals = normalize_engine_signals(
        engine_signals()
    )

    prices = build_price_matrix(
        market
    )

    returns = build_return_matrix(
        prices
    )

    governance_map = build_governance_map(
        governance()
    )

    date = market[
        "date"
    ].iloc[250]

    weights = reconstruct_candidate_portfolio(
        rebalance_date=date,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
    )

    assert round(
        float(weights.sum()),
        8,
    ) == 1.0

    assert (
        weights.get(
            "CASH",
            0.0,
        )
        >= 0.20
    )


def test_retired_engine_is_not_admitted():
    mapping = build_governance_map(
        governance()
    )

    assert "retired" not in mapping


def test_walk_forward_is_deterministic():
    market = normalize_market_history(
        market_history()
    )

    signals = normalize_engine_signals(
        engine_signals()
    )

    returns = build_return_matrix(
        build_price_matrix(
            market
        )
    )

    governance_map = build_governance_map(
        governance()
    )

    first = run_walk_forward(
        market=market,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
    )

    second = run_walk_forward(
        market=market,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
    )

    assert (
        first["baseline"]["metrics"]
        == second["baseline"]["metrics"]
    )

    assert (
        first["candidate"]["metrics"]
        == second["candidate"]["metrics"]
    )


def test_walk_forward_generates_rebalances():
    market = normalize_market_history(
        market_history()
    )

    signals = normalize_engine_signals(
        engine_signals()
    )

    returns = build_return_matrix(
        build_price_matrix(
            market
        )
    )

    result = run_walk_forward(
        market=market,
        signals=signals,
        returns=returns,
        governance_map=(
            build_governance_map(
                governance()
            )
        ),
    )

    assert (
        result[
            "baseline"
        ][
            "metrics"
        ][
            "rebalance_count"
        ] > 0
    )

    assert (
        result[
            "candidate"
        ][
            "metrics"
        ][
            "rebalance_count"
        ] > 0
    )
