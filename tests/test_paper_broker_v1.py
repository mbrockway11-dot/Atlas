"""Tests for deterministic paper broker behavior."""

from __future__ import annotations

from atlas.investment.execution import (
    OrderIntent,
    PaperBroker,
    PaperBrokerConfig,
    RiskDecision,
)


def approved_risk(
    intent_id: str,
):
    return RiskDecision(
        approved=True,
        reason_codes=(),
        intent_id=intent_id,
        order_notional=100.0,
        projected_asset_notional=100.0,
        projected_gross_exposure=100.0,
        projected_cash=900.0,
        evaluated_at="now",
    )


def test_market_order_fills():
    intent = OrderIntent(
        asset="TEST",
        side="BUY",
        quantity=1.0,
        reference_price=100.0,
        strategy_id="test",
        evidence_id="evidence",
    )

    broker = PaperBroker(
        PaperBrokerConfig(
            fee_bps=10.0,
            slippage_bps=5.0,
        )
    )

    order, fills = broker.submit(
        intent,
        approved_risk(
            intent.intent_id
        ),
    )

    assert order.status == "FILLED"
    assert len(fills) == 1
    assert fills[0].price > 100.0
    assert fills[0].fee > 0


def test_partial_fill_from_liquidity_cap():
    intent = OrderIntent(
        asset="TEST",
        side="BUY",
        quantity=10.0,
        reference_price=100.0,
        strategy_id="test",
        evidence_id="evidence",
    )

    broker = PaperBroker(
        PaperBrokerConfig(
            available_liquidity_quantity=4.0
        )
    )

    order, fills = broker.submit(
        intent,
        approved_risk(
            intent.intent_id
        ),
    )

    assert (
        order.status
        == "PARTIALLY_FILLED"
    )
    assert (
        order.filled_quantity
        == 4.0
    )
    assert (
        order.remaining_quantity
        == 6.0
    )
