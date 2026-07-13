"""Deterministic pre-trade risk engine."""

from __future__ import annotations

from datetime import UTC, datetime

from atlas.investment.execution.contracts import (
    AccountSnapshot,
    OrderIntent,
    RiskDecision,
    RiskLimits,
)
from atlas.investment.execution.instruments import (
    require_paper_instrument,
)


def evaluate_order_intent(
    intent: OrderIntent,
    account: AccountSnapshot,
    limits: RiskLimits,
) -> RiskDecision:
    """Evaluate one order intent against hard account limits."""
    reasons: list[str] = []

    try:
        instrument = (
            require_paper_instrument(
                intent.asset
            )
        )
    except (
        KeyError,
        ValueError,
    ) as error:
        instrument = None
        reasons.append(
            str(error)
        )

    if instrument is not None:
        if (
            intent.quantity
            < instrument.minimum_quantity
        ):
            reasons.append(
                "INSTRUMENT_MINIMUM_QUANTITY"
            )

        if (
            intent.notional
            < instrument.minimum_notional
        ):
            reasons.append(
                "INSTRUMENT_MINIMUM_NOTIONAL"
            )

        if (
            intent.side == "SELL"
            and not instrument.short_enabled
            and account.positions.get(
                intent.asset
            ) is None
        ):
            reasons.append(
                "INSTRUMENT_SHORT_DISABLED"
            )

    signed_quantity = (
        intent.quantity
        if intent.side == "BUY"
        else -intent.quantity
    )

    existing = account.positions.get(
        intent.asset
    )

    existing_quantity = (
        existing.quantity
        if existing is not None
        else 0.0
    )

    existing_asset_notional = (
        existing.absolute_notional
        if existing is not None
        else 0.0
    )

    projected_quantity = (
        existing_quantity
        + signed_quantity
    )

    projected_asset_notional = abs(
        projected_quantity
        * intent.reference_price
    )

    projected_gross_exposure = (
        account.gross_exposure
        - existing_asset_notional
        + projected_asset_notional
    )

    cash_delta = (
        -intent.notional
        if intent.side == "BUY"
        else intent.notional
    )

    projected_cash = (
        account.cash
        + cash_delta
    )

    net_liquidation_value = (
        account.net_liquidation_value
    )

    projected_leverage = (
        projected_gross_exposure
        / net_liquidation_value
        if net_liquidation_value > 0
        else float("inf")
    )

    if (
        intent.notional
        > limits.maximum_order_notional
    ):
        reasons.append(
            "ORDER_NOTIONAL_LIMIT"
        )

    if (
        projected_asset_notional
        > limits.maximum_asset_notional
    ):
        reasons.append(
            "ASSET_NOTIONAL_LIMIT"
        )

    if (
        projected_gross_exposure
        > limits.maximum_gross_exposure
    ):
        reasons.append(
            "GROSS_EXPOSURE_LIMIT"
        )

    if (
        projected_leverage
        > limits.maximum_leverage
    ):
        reasons.append(
            "LEVERAGE_LIMIT"
        )

    if (
        account.daily_pnl
        <= -abs(
            limits.maximum_daily_loss
        )
    ):
        reasons.append(
            "DAILY_LOSS_LIMIT"
        )

    if (
        intent.maximum_slippage_bps
        > limits.maximum_slippage_bps
    ):
        reasons.append(
            "SLIPPAGE_LIMIT"
        )

    if (
        intent.side == "BUY"
        and projected_cash < 0
    ):
        reasons.append(
            "INSUFFICIENT_CASH"
        )

    if (
        not limits.allow_short_positions
        and projected_quantity < 0
    ):
        reasons.append(
            "SHORT_POSITION_DISABLED"
        )

    if (
        intent.reduce_only
        and abs(projected_quantity)
        > abs(existing_quantity)
    ):
        reasons.append(
            "REDUCE_ONLY_VIOLATION"
        )

    return RiskDecision(
        approved=not reasons,
        reason_codes=tuple(reasons),
        intent_id=intent.intent_id,
        order_notional=(
            intent.notional
        ),
        projected_asset_notional=(
            projected_asset_notional
        ),
        projected_gross_exposure=(
            projected_gross_exposure
        ),
        projected_cash=(
            projected_cash
        ),
        evaluated_at=datetime.now(
            UTC
        ).isoformat(),
    )
