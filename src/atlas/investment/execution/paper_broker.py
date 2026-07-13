"""Deterministic broker-neutral paper order simulator."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from atlas.investment.execution.contracts import (
    FillRecord,
    OrderIntent,
    OrderRecord,
    RiskDecision,
    build_record_id,
)


@dataclass(frozen=True)
class PaperBrokerConfig:
    """Paper fill model configuration."""

    fee_bps: float = 8.0
    slippage_bps: float = 5.0
    available_liquidity_quantity: (
        float | None
    ) = None


class PaperBroker:
    """Immediate deterministic paper broker."""

    def __init__(
        self,
        config: PaperBrokerConfig | None = None,
    ) -> None:
        self.config = (
            config
            or PaperBrokerConfig()
        )

    def submit(
        self,
        intent: OrderIntent,
        risk: RiskDecision,
    ) -> tuple[
        OrderRecord,
        tuple[FillRecord, ...],
    ]:
        submitted_at = datetime.now(
            UTC
        ).isoformat()

        order_id = build_record_id(
            "ORDER",
            {
                "intent_id": intent.intent_id,
                "submitted_at": submitted_at,
            },
        )

        if not risk.approved:
            return (
                OrderRecord(
                    order_id=order_id,
                    intent_id=(
                        intent.intent_id
                    ),
                    asset=intent.asset,
                    side=intent.side,
                    requested_quantity=(
                        intent.quantity
                    ),
                    filled_quantity=0.0,
                    remaining_quantity=(
                        intent.quantity
                    ),
                    status="REJECTED",
                    submitted_at=(
                        submitted_at
                    ),
                    completed_at=(
                        submitted_at
                    ),
                    average_fill_price=0.0,
                    fee_paid=0.0,
                    rejection_reason="|".join(
                        risk.reason_codes
                    ),
                ),
                (),
            )

        fill_quantity = (
            intent.quantity
        )

        if (
            self.config
            .available_liquidity_quantity
            is not None
        ):
            fill_quantity = min(
                fill_quantity,
                max(
                    0.0,
                    float(
                        self.config
                        .available_liquidity_quantity
                    ),
                ),
            )

        if fill_quantity <= 0:
            return (
                OrderRecord(
                    order_id=order_id,
                    intent_id=(
                        intent.intent_id
                    ),
                    asset=intent.asset,
                    side=intent.side,
                    requested_quantity=(
                        intent.quantity
                    ),
                    filled_quantity=0.0,
                    remaining_quantity=(
                        intent.quantity
                    ),
                    status="CANCELLED",
                    submitted_at=(
                        submitted_at
                    ),
                    completed_at=(
                        submitted_at
                    ),
                    average_fill_price=0.0,
                    fee_paid=0.0,
                    rejection_reason=(
                        "NO_PAPER_LIQUIDITY"
                    ),
                ),
                (),
            )

        direction = (
            1.0
            if intent.side == "BUY"
            else -1.0
        )

        configured_slippage = min(
            max(
                0.0,
                float(
                    self.config
                    .slippage_bps
                ),
            ),
            intent.maximum_slippage_bps,
        )

        fill_price = (
            intent.reference_price
            * (
                1.0
                + direction
                * configured_slippage
                / 10_000.0
            )
        )

        if intent.order_type == "LIMIT":
            assert (
                intent.limit_price
                is not None
            )

            if (
                intent.side == "BUY"
                and fill_price
                > intent.limit_price
            ):
                return (
                    cancelled_limit_order(
                        order_id=order_id,
                        intent=intent,
                        submitted_at=(
                            submitted_at
                        ),
                    ),
                    (),
                )

            if (
                intent.side == "SELL"
                and fill_price
                < intent.limit_price
            ):
                return (
                    cancelled_limit_order(
                        order_id=order_id,
                        intent=intent,
                        submitted_at=(
                            submitted_at
                        ),
                    ),
                    (),
                )

        notional = (
            fill_quantity
            * fill_price
        )

        fee = (
            notional
            * max(
                0.0,
                self.config.fee_bps,
            )
            / 10_000.0
        )

        fill_id = build_record_id(
            "FILL",
            {
                "order_id": order_id,
                "quantity": fill_quantity,
                "price": fill_price,
            },
        )

        fill = FillRecord(
            fill_id=fill_id,
            order_id=order_id,
            intent_id=intent.intent_id,
            asset=intent.asset,
            side=intent.side,
            quantity=fill_quantity,
            price=fill_price,
            notional=notional,
            fee=fee,
            slippage_bps=(
                configured_slippage
            ),
            filled_at=datetime.now(
                UTC
            ).isoformat(),
        )

        remaining = max(
            0.0,
            intent.quantity
            - fill_quantity,
        )

        status = (
            "FILLED"
            if remaining == 0
            else "PARTIALLY_FILLED"
        )

        order = OrderRecord(
            order_id=order_id,
            intent_id=intent.intent_id,
            asset=intent.asset,
            side=intent.side,
            requested_quantity=(
                intent.quantity
            ),
            filled_quantity=(
                fill_quantity
            ),
            remaining_quantity=(
                remaining
            ),
            status=status,
            submitted_at=(
                submitted_at
            ),
            completed_at=(
                fill.filled_at
            ),
            average_fill_price=(
                fill_price
            ),
            fee_paid=fee,
        )

        return order, (fill,)


def cancelled_limit_order(
    *,
    order_id: str,
    intent: OrderIntent,
    submitted_at: str,
) -> OrderRecord:
    return OrderRecord(
        order_id=order_id,
        intent_id=intent.intent_id,
        asset=intent.asset,
        side=intent.side,
        requested_quantity=(
            intent.quantity
        ),
        filled_quantity=0.0,
        remaining_quantity=(
            intent.quantity
        ),
        status="CANCELLED",
        submitted_at=submitted_at,
        completed_at=submitted_at,
        average_fill_price=0.0,
        fee_paid=0.0,
        rejection_reason=(
            "LIMIT_PRICE_NOT_MARKETABLE"
        ),
    )
