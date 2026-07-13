"""Safety-contract tests for the portfolio bridge."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    PortfolioTarget,
    build_portfolio_intent_plan,
)


def test_bridge_does_not_execute_orders():
    report = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC-USD",
                target_weight=0.20,
                reference_price=50_000.0,
            )
        ],
        account=AccountSnapshot(
            cash=10_000.0
        ),
        strategy_id="optimizer",
        evidence_id="evidence",
        write_output=False,
    )

    contract = report[
        "contract"
    ]

    assert contract[
        "intent_generation_only"
    ]

    assert not contract[
        "submits_orders"
    ]

    assert not contract[
        "mutates_account"
    ]

    assert not report[
        "live_execution"
    ]
