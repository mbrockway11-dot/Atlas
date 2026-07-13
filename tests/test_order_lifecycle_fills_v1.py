"""Partial-fill and completion tests for paper lifecycle."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.execution import (
    FillRecord,
    OrderIntent,
    RiskDecision,
)
from atlas.investment.execution.lifecycle import (
    PaperOrderLifecycleStore,
)


def store(
    tmp_path: Path,
) -> PaperOrderLifecycleStore:
    return PaperOrderLifecycleStore(
        state_path=(
            tmp_path / "state.json"
        ),
        transitions_path=(
            tmp_path
            / "transitions.jsonl"
        ),
    )


def prepare(
    tmp_path: Path,
):
    lifecycle = store(
        tmp_path
    )

    intent = OrderIntent(
        asset="SOL-USD",
        side="BUY",
        quantity=10.0,
        reference_price=100.0,
        strategy_id="engine-a",
        evidence_id="evidence-3",
    )

    lifecycle.create(intent)

    lifecycle.apply_risk_decision(
        intent.intent_id,
        RiskDecision(
            approved=True,
            reason_codes=(),
            intent_id=(
                intent.intent_id
            ),
            order_notional=1_000.0,
            projected_asset_notional=(
                1_000.0
            ),
            projected_gross_exposure=(
                1_000.0
            ),
            projected_cash=9_000.0,
            evaluated_at="now",
        ),
    )

    lifecycle.transition(
        intent.intent_id,
        "SUBMITTED",
        reason="submitted",
        order_id="ORDER-1",
    )

    return lifecycle, intent


def fill(
    intent_id: str,
    quantity: float,
    price: float,
) -> FillRecord:
    return FillRecord(
        fill_id=(
            "FILL-"
            + str(quantity)
        ),
        order_id="ORDER-1",
        intent_id=intent_id,
        asset="SOL-USD",
        side="BUY",
        quantity=quantity,
        price=price,
        notional=(
            quantity * price
        ),
        fee=1.0,
        slippage_bps=0.0,
        filled_at="now",
    )


def test_partial_then_complete_fill(
    tmp_path: Path,
):
    lifecycle, intent = prepare(
        tmp_path
    )

    partial = lifecycle.apply_fill(
        intent.intent_id,
        fill(
            intent.intent_id,
            4.0,
            100.0,
        ),
    )

    completed = lifecycle.apply_fill(
        intent.intent_id,
        fill(
            intent.intent_id,
            6.0,
            102.0,
        ),
    )

    assert (
        partial.state
        == "PARTIALLY_FILLED"
    )
    assert (
        partial.remaining_quantity
        == 6.0
    )

    assert (
        completed.state
        == "FILLED"
    )
    assert (
        completed.remaining_quantity
        == 0.0
    )
    assert (
        completed.filled_quantity
        == 10.0
    )
    assert (
        completed.average_fill_price
        == pytest.approx(
            101.2
        )
    )


def test_overfill_is_rejected(
    tmp_path: Path,
):
    lifecycle, intent = prepare(
        tmp_path
    )

    with pytest.raises(
        ValueError,
        match="OVERFILL_DETECTED",
    ):
        lifecycle.apply_fill(
            intent.intent_id,
            fill(
                intent.intent_id,
                11.0,
                100.0,
            ),
        )
