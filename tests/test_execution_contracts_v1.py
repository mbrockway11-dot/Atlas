"""Tests for canonical paper execution contracts."""

from __future__ import annotations

import pytest

from atlas.investment.execution import (
    OrderIntent,
)


def test_intent_id_is_deterministic():
    first = OrderIntent(
        asset="BTC-USD",
        side="BUY",
        quantity=0.01,
        reference_price=50_000.0,
        strategy_id="alpha",
        evidence_id="evidence-1",
        created_at="first",
    )

    second = OrderIntent(
        asset="BTC-USD",
        side="BUY",
        quantity=0.01,
        reference_price=50_000.0,
        strategy_id="alpha",
        evidence_id="evidence-1",
        created_at="second",
    )

    assert (
        first.intent_id
        == second.intent_id
    )


def test_invalid_quantity_is_rejected():
    with pytest.raises(
        ValueError,
        match="positive",
    ):
        OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=0.0,
            reference_price=50_000.0,
            strategy_id="alpha",
            evidence_id="evidence-1",
        )


def test_limit_requires_price():
    with pytest.raises(
        ValueError,
        match="limit_price",
    ):
        OrderIntent(
            asset="BTC-USD",
            side="BUY",
            quantity=0.01,
            reference_price=50_000.0,
            strategy_id="alpha",
            evidence_id="evidence-1",
            order_type="LIMIT",
        )
