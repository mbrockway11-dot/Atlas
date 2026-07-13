"""Turnover and order-cap tests for portfolio intent generation."""

from __future__ import annotations

import pytest

from atlas.investment.execution import (
    AccountSnapshot,
    PortfolioTarget,
    RebalancePolicy,
    build_portfolio_intent_plan,
)


def test_total_turnover_is_capped():
    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.40,
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
        evidence_id="evidence",
        policy=RebalancePolicy(
            maximum_total_turnover=0.20,
            minimum_cash_weight=0.10,
            minimum_order_notional=1.0,
        ),
        write_output=False,
    )

    assert (
        plan[
            "total_turnover_weight"
        ]
        == pytest.approx(
            0.20
        )
    )


def test_individual_order_notional_is_capped():
    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.50,
                reference_price=50_000.0,
            )
        ],
        account=AccountSnapshot(
            cash=10_000.0
        ),
        strategy_id="optimizer",
        evidence_id="evidence",
        policy=RebalancePolicy(
            maximum_order_notional=1_000.0,
            maximum_total_turnover=1.0,
            minimum_cash_weight=0.10,
        ),
        write_output=False,
    )

    line = (
        plan["rebalance_lines"][0]
    )

    assert (
        abs(
            line[
                "approved_notional_delta"
            ]
        )
        == pytest.approx(
            1_000.0
        )
    )


def test_turnover_scaling_is_deterministic():
    kwargs = {
        "targets": [
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.40,
                reference_price=50_000.0,
            ),
            PortfolioTarget(
                asset="ETH-USD",
                target_weight=0.30,
                reference_price=2_000.0,
            ),
        ],
        "account": AccountSnapshot(
            cash=10_000.0
        ),
        "strategy_id": "optimizer",
        "evidence_id": "evidence",
        "policy": RebalancePolicy(
            maximum_total_turnover=0.25,
            minimum_cash_weight=0.10,
        ),
        "write_output": False,
    }

    first = (
        build_portfolio_intent_plan(
            **kwargs
        )
    )

    second = (
        build_portfolio_intent_plan(
            **kwargs
        )
    )

    assert (
        first["plan_id"]
        == second["plan_id"]
    )

    def deterministic_intents(report):
        return [
            {
                key: value
                for key, value
                in intent.items()
                if key != "created_at"
            }
            for intent
            in report["intents"]
        ]

    assert (
        deterministic_intents(first)
        == deterministic_intents(second)
    )

    assert [
        intent["intent_id"]
        for intent
        in first["intents"]
    ] == [
        intent["intent_id"]
        for intent
        in second["intents"]
    ]
