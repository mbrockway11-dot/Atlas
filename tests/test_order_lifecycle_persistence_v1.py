"""Persistence and restart tests for paper order lifecycle."""

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
        asset="ETH-USD",
        side="BUY",
        quantity=1.0,
        reference_price=2_000.0,
        strategy_id="ensemble",
        evidence_id="evidence-2",
    )


def approved(
    intent_id: str,
) -> RiskDecision:
    return RiskDecision(
        approved=True,
        reason_codes=(),
        intent_id=intent_id,
        order_notional=2_000.0,
        projected_asset_notional=2_000.0,
        projected_gross_exposure=2_000.0,
        projected_cash=8_000.0,
        evaluated_at="now",
    )


def test_restart_recovers_open_order(
    tmp_path: Path,
):
    first = make_store(
        tmp_path
    )
    intent = make_intent()

    first.create(intent)
    first.apply_risk_decision(
        intent.intent_id,
        approved(
            intent.intent_id
        ),
    )

    restarted = make_store(
        tmp_path
    )

    recovered = (
        restarted
        .recover_open_orders()
    )

    assert len(recovered) == 1
    assert (
        recovered[0].intent_id
        == intent.intent_id
    )
    assert (
        recovered[0].state
        == "RISK_APPROVED"
    )


def test_duplicate_active_intent_rejected(
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
            "DUPLICATE_ACTIVE_INTENT"
        ),
    ):
        store.create(intent)


def test_terminal_intent_can_be_recreated(
    tmp_path: Path,
):
    store = make_store(
        tmp_path
    )
    intent = make_intent()

    store.create(intent)
    store.cancel(
        intent.intent_id
    )

    recreated = store.create(
        intent
    )

    assert (
        recreated.state
        == "CREATED"
    )
