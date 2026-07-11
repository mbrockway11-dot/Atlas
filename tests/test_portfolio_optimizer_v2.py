"""Tests for Portfolio Optimizer v2."""

from __future__ import annotations

import pandas as pd

from atlas.investment.portfolio_optimizer.optimizer import (
    optimize_portfolio,
)


def ensemble_scores() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "asset": "BTC-USD",
            "ensemble_score": 0.80,
            "confidence": 0.85,
        },
        {
            "asset": "ETH-USD",
            "ensemble_score": 0.70,
            "confidence": 0.80,
        },
        {
            "asset": "SOL-USD",
            "ensemble_score": 0.60,
            "confidence": 0.75,
        },
    ])


def contributions() -> pd.DataFrame:
    rows = []

    for asset in [
        "BTC-USD",
        "ETH-USD",
        "SOL-USD",
    ]:
        rows.extend([
            {
                "asset": asset,
                "engine_id": "engine_a",
                "weighted_contribution": 0.60,
                "signed_contribution": 0.30,
            },
            {
                "asset": asset,
                "engine_id": "engine_b",
                "weighted_contribution": 0.40,
                "signed_contribution": 0.15,
            },
        ])

    return pd.DataFrame(rows)


def history() -> pd.DataFrame:
    rows = []

    for day in range(220):
        date = pd.Timestamp(
            "2025-01-01",
            tz="UTC",
        ) + pd.Timedelta(
            days=day
        )

        rows.extend([
            {
                "timestamp": date,
                "asset": "BTC-USD",
                "close": 100 + day * 0.8,
            },
            {
                "timestamp": date,
                "asset": "ETH-USD",
                "close": 80 + day * 0.6,
            },
            {
                "timestamp": date,
                "asset": "SOL-USD",
                "close": 40 + day * 0.5,
            },
        ])

    return pd.DataFrame(rows)


def fusion_report() -> dict:
    return {
        "fused_context": {
            "fused_regime": (
                "RESTRICTIVE_TRANSITION"
            ),
            "confidence": 0.60,
            "controls": {
                "risk_budget_multiplier": 0.90,
                "minimum_cash_weight": 0.35,
                "conviction_ceiling": 0.68,
                "volatility_target_multiplier": 0.85,
                "turnover_multiplier": 0.75,
            },
        }
    }


def test_optimizer_weights_sum_to_one():
    result = optimize_portfolio(
        ensemble_scores=ensemble_scores(),
        contributions=contributions(),
        market_history=history(),
        fusion_report=fusion_report(),
    )

    portfolio = result[
        "portfolio"
    ]

    assert round(
        float(
            portfolio[
                "target_weight"
            ].sum()
        ),
        8,
    ) == 1.0


def test_optimizer_respects_cash_floor():
    result = optimize_portfolio(
        ensemble_scores=ensemble_scores(),
        contributions=contributions(),
        market_history=history(),
        fusion_report=fusion_report(),
    )

    portfolio = result[
        "portfolio"
    ].set_index("asset")

    assert (
        float(
            portfolio.loc[
                "CASH",
                "target_weight",
            ]
        )
        >= 0.35
    )


def test_optimizer_respects_asset_cap():
    result = optimize_portfolio(
        ensemble_scores=ensemble_scores(),
        contributions=contributions(),
        market_history=history(),
        fusion_report=fusion_report(),
    )

    risky = result[
        "portfolio"
    ]

    risky = risky[
        risky["asset"] != "CASH"
    ]

    assert (
        risky[
            "target_weight"
        ]
        <= 0.40 + 1e-8
    ).all()


def test_optimizer_is_deterministic():
    kwargs = {
        "ensemble_scores": (
            ensemble_scores()
        ),
        "contributions": (
            contributions()
        ),
        "market_history": history(),
        "fusion_report": fusion_report(),
    }

    first = optimize_portfolio(
        **kwargs
    )

    second = optimize_portfolio(
        **kwargs
    )

    pd.testing.assert_frame_equal(
        first["portfolio"],
        second["portfolio"],
    )

    assert (
        first["risk"]
        == second["risk"]
    )


def test_empty_scores_returns_cash():
    result = optimize_portfolio(
        ensemble_scores=pd.DataFrame(),
        contributions=pd.DataFrame(),
        market_history=pd.DataFrame(),
        fusion_report={},
    )

    portfolio = result[
        "portfolio"
    ]

    assert len(portfolio) == 1

    assert (
        portfolio.iloc[0][
            "asset"
        ]
        == "CASH"
    )

    assert (
        float(
            portfolio.iloc[0][
                "target_weight"
            ]
        )
        == 1.0
    )
