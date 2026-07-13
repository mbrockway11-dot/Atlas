"""Tests for deterministic pre-trade risk."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    PositionSnapshot,
    RiskLimits,
    evaluate_order_intent,
)


def intent(
    *,
    side="BUY",
    quantity=1.0,
    price=100.0,
    reduce_only=False,
):
    return OrderIntent(
        asset="TEST",
        side=side,
        quantity=quantity,
        reference_price=price,
        strategy_id="test",
        evidence_id="evidence",
        reduce_only=reduce_only,
    )


def test_safe_order_is_approved():
    decision = evaluate_order_intent(
        intent(),
        AccountSnapshot(
            cash=1_000.0
        ),
        RiskLimits(
            maximum_order_notional=500.0,
            maximum_asset_notional=500.0,
            maximum_gross_exposure=500.0,
            maximum_leverage=1.0,
        ),
    )

    assert decision.approved
    assert decision.reason_codes == ()


def test_order_notional_limit_rejects():
    decision = evaluate_order_intent(
        intent(
            quantity=10.0,
            price=100.0,
        ),
        AccountSnapshot(
            cash=10_000.0
        ),
        RiskLimits(
            maximum_order_notional=500.0
        ),
    )

    assert not decision.approved
    assert (
        "ORDER_NOTIONAL_LIMIT"
        in decision.reason_codes
    )


def test_short_position_disabled():
    decision = evaluate_order_intent(
        intent(
            side="SELL",
            quantity=1.0,
        ),
        AccountSnapshot(
            cash=1_000.0
        ),
        RiskLimits(
            allow_short_positions=False
        ),
    )

    assert not decision.approved
    assert (
        "SHORT_POSITION_DISABLED"
        in decision.reason_codes
    )


def test_reduce_only_cannot_increase_position():
    account = AccountSnapshot(
        cash=1_000.0,
        positions={
            "TEST": PositionSnapshot(
                asset="TEST",
                quantity=1.0,
                average_price=100.0,
                mark_price=100.0,
            )
        },
    )

    decision = evaluate_order_intent(
        intent(
            side="BUY",
            quantity=1.0,
            reduce_only=True,
        ),
        account,
        RiskLimits(),
    )

    assert not decision.approved
    assert (
        "REDUCE_ONLY_VIOLATION"
        in decision.reason_codes
    )
