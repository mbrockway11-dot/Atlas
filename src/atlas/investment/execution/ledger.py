"""Authoritative paper position and cash ledger transitions."""

from __future__ import annotations

from atlas.investment.execution.contracts import (
    AccountSnapshot,
    FillRecord,
    PositionSnapshot,
)


def apply_fill(
    account: AccountSnapshot,
    fill: FillRecord,
) -> AccountSnapshot:
    """Apply one fill and return a new immutable account snapshot."""
    positions = dict(
        account.positions
    )

    current = positions.get(
        fill.asset
    )

    current_quantity = (
        current.quantity
        if current is not None
        else 0.0
    )

    current_average = (
        current.average_price
        if current is not None
        else 0.0
    )

    signed_fill_quantity = (
        fill.quantity
        if fill.side == "BUY"
        else -fill.quantity
    )

    next_quantity = (
        current_quantity
        + signed_fill_quantity
    )

    realized_delta = 0.0

    same_direction = bool(
        current_quantity == 0
        or (
            current_quantity > 0
            and signed_fill_quantity > 0
        )
        or (
            current_quantity < 0
            and signed_fill_quantity < 0
        )
    )

    if same_direction:
        total_absolute_quantity = (
            abs(current_quantity)
            + abs(
                signed_fill_quantity
            )
        )

        next_average = (
            (
                abs(current_quantity)
                * current_average
                + abs(
                    signed_fill_quantity
                )
                * fill.price
            )
            / total_absolute_quantity
            if total_absolute_quantity
            else 0.0
        )
    else:
        closing_quantity = min(
            abs(current_quantity),
            abs(
                signed_fill_quantity
            ),
        )

        direction = (
            1.0
            if current_quantity > 0
            else -1.0
        )

        realized_delta = (
            fill.price
            - current_average
        ) * closing_quantity * direction

        if next_quantity == 0:
            next_average = 0.0
        elif (
            current_quantity
            * next_quantity
            > 0
        ):
            next_average = (
                current_average
            )
        else:
            next_average = (
                fill.price
            )

    cash_delta = (
        -fill.notional
        if fill.side == "BUY"
        else fill.notional
    )

    next_cash = (
        account.cash
        + cash_delta
        - fill.fee
    )

    if next_quantity == 0:
        positions.pop(
            fill.asset,
            None,
        )
    else:
        positions[
            fill.asset
        ] = PositionSnapshot(
            asset=fill.asset,
            quantity=next_quantity,
            average_price=(
                next_average
            ),
            mark_price=fill.price,
        )

    net_realized_delta = (
        realized_delta
        - fill.fee
    )

    return AccountSnapshot(
        cash=next_cash,
        positions=positions,
        realized_pnl=(
            account.realized_pnl
            + net_realized_delta
        ),
        daily_pnl=(
            account.daily_pnl
            + net_realized_delta
        ),
    )
