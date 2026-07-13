"""Core tests for portfolio target to order-intent conversion."""

from __future__ import annotations

import pytest

from atlas.investment.execution import (
    AccountSnapshot,
    PortfolioTarget,
    PositionSnapshot,
    RebalancePolicy,
    build_portfolio_intent_plan,
)


def test_empty_account_generates_buys():
    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.30,
                reference_price=50_000.0,
            ),
            PortfolioTarget(
                asset="ETH-USD",
                target_weight=0.20,
                reference_price=2_000.0,
            ),
        ],
        account=AccountSnapshot(
            cash=10_000.0
        ),
        strategy_id="optimizer",
        evidence_id="evidence-1",
        policy=RebalancePolicy(
            maximum_total_turnover=1.0,
            minimum_cash_weight=0.10,
        ),
        write_output=False,
    )

    assert plan["success"]

    assert [
        intent["side"]
        for intent
        in plan["intents"]
    ] == [
        "BUY",
        "BUY",
    ]

    assert (
        plan["counts"][
            "generated_intents"
        ]
        == 2
    )


def test_overweight_position_generates_sell():
    account = AccountSnapshot(
        cash=5_000.0,
        positions={
            "BTC-USD": PositionSnapshot(
                asset="BTC-USD",
                quantity=0.1,
                average_price=50_000.0,
                mark_price=50_000.0,
            )
        },
    )

    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.25,
                reference_price=50_000.0,
            )
        ],
        account=account,
        strategy_id="optimizer",
        evidence_id="evidence-2",
        policy=RebalancePolicy(
            maximum_total_turnover=1.0,
        ),
        write_output=False,
    )

    assert (
        plan["intents"][0][
            "side"
        ]
        == "SELL"
    )


def test_small_delta_is_skipped():
    account = AccountSnapshot(
        cash=9_000.0,
        positions={
            "BTC-USD": PositionSnapshot(
                asset="BTC-USD",
                quantity=0.02,
                average_price=50_000.0,
                mark_price=50_000.0,
            )
        },
    )

    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.105,
                reference_price=50_000.0,
            )
        ],
        account=account,
        strategy_id="optimizer",
        evidence_id="evidence-3",
        policy=RebalancePolicy(
            minimum_weight_delta=0.01,
        ),
        write_output=False,
    )

    assert (
        plan["counts"][
            "generated_intents"
        ]
        == 0
    )

    assert (
        plan["rebalance_lines"][0][
            "skip_reason"
        ]
        == "BELOW_WEIGHT_THRESHOLD"
    )


def test_cash_buffer_is_enforced():
    with pytest.raises(
        ValueError,
        match=(
            "TARGET_WEIGHT_EXCEEDS_CASH_BUFFER"
        ),
    ):
        build_portfolio_intent_plan(
            targets=[
                PortfolioTarget(
                    asset="BTC-USD",
                    target_weight=0.60,
                    reference_price=50_000.0,
                ),
                PortfolioTarget(
                    asset="ETH-USD",
                    target_weight=0.40,
                    reference_price=2_000.0,
                ),
            ],
            account=AccountSnapshot(
                cash=10_000.0
            ),
            strategy_id="optimizer",
            evidence_id="evidence-4",
            policy=RebalancePolicy(
                minimum_cash_weight=0.10,
            ),
            write_output=False,
        )
