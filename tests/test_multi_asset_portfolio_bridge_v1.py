"""Tests for multi-asset portfolio target normalization."""

from __future__ import annotations

import pytest

from atlas.investment.execution import (
    AccountSnapshot,
    PortfolioTarget,
    RebalancePolicy,
    build_portfolio_intent_plan,
)


def test_crypto_metals_energy_and_rates_generate_intents():
    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="BTC",
                target_weight=0.10,
                reference_price=50_000.0,
            ),
            PortfolioTarget(
                asset="GOLD",
                target_weight=0.10,
                reference_price=300.0,
            ),
            PortfolioTarget(
                asset="OIL",
                target_weight=0.10,
                reference_price=80.0,
            ),
            PortfolioTarget(
                asset="TLT",
                target_weight=0.10,
                reference_price=90.0,
            ),
        ],
        account=AccountSnapshot(
            cash=10_000.0
        ),
        strategy_id="multi-asset",
        evidence_id="universe-test",
        policy=RebalancePolicy(
            maximum_total_turnover=1.0,
            minimum_cash_weight=0.50,
        ),
        write_output=False,
    )

    assets = {
        intent["asset"]
        for intent
        in plan["intents"]
    }

    assert assets == {
        "BTC-USD",
        "GLD",
        "USO",
        "TLT",
    }


def test_rebalance_lines_include_instrument_metadata():
    plan = build_portfolio_intent_plan(
        targets=[
            PortfolioTarget(
                asset="GLD",
                target_weight=0.10,
                reference_price=300.0,
            )
        ],
        account=AccountSnapshot(
            cash=10_000.0
        ),
        strategy_id="multi-asset",
        evidence_id="metadata",
        policy=RebalancePolicy(
            maximum_total_turnover=1.0,
        ),
        write_output=False,
    )

    line = (
        plan["rebalance_lines"][0]
    )

    assert (
        line["asset_class"]
        == "METALS"
    )

    assert (
        line["instrument_type"]
        == "ETF"
    )

    assert (
        line["market_session"]
        == "US_EQUITIES"
    )


def test_unregistered_target_is_rejected():
    with pytest.raises(
        KeyError,
        match=(
            "UNREGISTERED_INSTRUMENT"
        ),
    ):
        build_portfolio_intent_plan(
            targets=[
                PortfolioTarget(
                    asset="UNKNOWN-ASSET",
                    target_weight=0.10,
                    reference_price=100.0,
                )
            ],
            account=AccountSnapshot(
                cash=10_000.0
            ),
            strategy_id="test",
            evidence_id="unknown",
            write_output=False,
        )


def test_direct_future_target_is_rejected():
    with pytest.raises(
        ValueError,
        match=(
            "PAPER_EXECUTION_DISABLED"
        ),
    ):
        build_portfolio_intent_plan(
            targets=[
                PortfolioTarget(
                    asset="CL=F",
                    target_weight=0.10,
                    reference_price=80.0,
                )
            ],
            account=AccountSnapshot(
                cash=100_000.0
            ),
            strategy_id="test",
            evidence_id="future",
            write_output=False,
        )
