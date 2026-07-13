"""Tests for instrument-aware pre-trade risk."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    RiskLimits,
    evaluate_order_intent,
)


def test_registered_etf_order_is_approved():
    decision = evaluate_order_intent(
        OrderIntent(
            asset="GLD",
            side="BUY",
            quantity=1.0,
            reference_price=300.0,
            strategy_id="test",
            evidence_id="gold",
        ),
        AccountSnapshot(
            cash=10_000.0
        ),
        RiskLimits(
            maximum_order_notional=(
                1_000.0
            ),
            maximum_asset_notional=(
                2_000.0
            ),
            maximum_gross_exposure=(
                5_000.0
            ),
        ),
    )

    assert decision.approved


def test_direct_future_is_rejected():
    decision = evaluate_order_intent(
        OrderIntent(
            asset="CL=F",
            side="BUY",
            quantity=1.0,
            reference_price=80.0,
            strategy_id="test",
            evidence_id="oil",
        ),
        AccountSnapshot(
            cash=100_000.0
        ),
        RiskLimits(
            maximum_order_notional=(
                100_000.0
            ),
            maximum_asset_notional=(
                100_000.0
            ),
            maximum_gross_exposure=(
                100_000.0
            ),
        ),
    )

    assert not decision.approved

    assert any(
        "PAPER_EXECUTION_DISABLED"
        in reason
        for reason
        in decision.reason_codes
    )


def test_below_etf_minimum_notional_is_rejected():
    decision = evaluate_order_intent(
        OrderIntent(
            asset="GLD",
            side="BUY",
            quantity=0.01,
            reference_price=300.0,
            strategy_id="test",
            evidence_id="small",
        ),
        AccountSnapshot(
            cash=10_000.0
        ),
        RiskLimits(),
    )

    assert not decision.approved

    assert (
        "INSTRUMENT_MINIMUM_NOTIONAL"
        in decision.reason_codes
    )
