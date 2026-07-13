"""Tests for paper cash and position ledger transitions."""

from __future__ import annotations

from atlas.investment.execution import (
    AccountSnapshot,
    FillRecord,
    apply_fill,
)


def fill(
    *,
    side: str,
    quantity: float,
    price: float,
    fee: float = 0.0,
):
    return FillRecord(
        fill_id="FILL-1",
        order_id="ORDER-1",
        intent_id="INTENT-1",
        asset="TEST",
        side=side,
        quantity=quantity,
        price=price,
        notional=(
            quantity
            * price
        ),
        fee=fee,
        slippage_bps=0.0,
        filled_at="now",
    )


def test_buy_creates_position():
    account = apply_fill(
        AccountSnapshot(
            cash=1_000.0
        ),
        fill(
            side="BUY",
            quantity=2.0,
            price=100.0,
            fee=1.0,
        ),
    )

    assert account.cash == 799.0
    assert (
        account.positions[
            "TEST"
        ].quantity
        == 2.0
    )


def test_sell_closes_and_realizes_profit():
    opened = apply_fill(
        AccountSnapshot(
            cash=1_000.0
        ),
        fill(
            side="BUY",
            quantity=1.0,
            price=100.0,
        ),
    )

    closed = apply_fill(
        opened,
        fill(
            side="SELL",
            quantity=1.0,
            price=110.0,
            fee=1.0,
        ),
    )

    assert "TEST" not in (
        closed.positions
    )

    assert (
        closed.realized_pnl
        == 9.0
    )
