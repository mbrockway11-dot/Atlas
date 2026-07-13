"""Tests for persistent paper-order lifecycle transitions."""

from __future__ import annotations

from pathlib import Path

import pytest

from atlas.investment.execution import (
    OrderIntent,
    RiskDecision,
)
from atlas.investment.execution.lifecycle import (
    PaperOrderLifecycleStore,
)


def make_store(
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


def make_intent() -> OrderIntent:
    return OrderIntent(
        asset="BTC-USD",
        side="BUY",
        quantity=0.01,
        reference_price=50_000.0,
        strategy_id="engine-a",
        evidence_id="evidence-1",
    )


def risk(
    intent_id: str,
    approved: bool,
) -> RiskDecision:
    return RiskDecision(
        approved=approved,
        reason_codes=(
            ()
            if approved
            else (
                "ORDER_NOTIONAL_LIMIT",
            )
        ),
        intent_id=intent_id,
        order_notional=500.0,
        projected_asset_notional=500.0,
        projected_gross_exposure=500.0,
        projected_cash=9_500.0,
        evaluated_at="now",
    )


def test_create_and_approve(
    tmp_path: Path,
):
    store = make_store(
        tmp_path
    )
    intent = make_intent()

    created = store.create(
        intent
    )

    approved = (
        store.apply_risk_decision(
            intent.intent_id,
            risk(
                intent.intent_id,
                True,
            ),
        )
    )

    assert (
        created.state
        == "CREATED"
    )
    assert (
        approved.state
        == "RISK_APPROVED"
    )


def test_illegal_transition_rejected(
    tmp_path: Path,
):
    store = make_store(
        tmp_path
    )
    intent = make_intent()

    store.create(intent)

    with pytest.raises(
        ValueError,
        match=(
            "ILLEGAL_ORDER_TRANSITION"
        ),
    ):
        store.transition(
            intent.intent_id,
            "FILLED",
            reason="invalid",
        )


def test_risk_rejection_is_terminal(
    tmp_path: Path,
):
    store = make_store(
        tmp_path
    )
    intent = make_intent()

    store.create(intent)

    rejected = (
        store.apply_risk_decision(
            intent.intent_id,
            risk(
                intent.intent_id,
                False,
            ),
        )
    )

    assert rejected.terminal

    with pytest.raises(
        ValueError,
        match=(
            "ILLEGAL_ORDER_TRANSITION"
        ),
    ):
        store.cancel(
            intent.intent_id
        )
