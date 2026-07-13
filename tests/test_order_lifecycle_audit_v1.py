"""Integrity-chain tests for paper lifecycle transitions."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution import (
    OrderIntent,
)
from atlas.investment.execution.lifecycle import (
    PaperOrderLifecycleStore,
)


def test_transition_chain_is_valid(
    tmp_path: Path,
):
    store = (
        PaperOrderLifecycleStore(
            state_path=(
                tmp_path / "state.json"
            ),
            transitions_path=(
                tmp_path
                / "transitions.jsonl"
            ),
        )
    )

    intent = OrderIntent(
        asset="BTC-USD",
        side="BUY",
        quantity=0.01,
        reference_price=50_000.0,
        strategy_id="test",
        evidence_id="evidence",
    )

    store.create(intent)

    store.cancel(
        intent.intent_id,
        reason="test cancellation",
    )

    validation = (
        store
        .validate_transition_chain()
    )

    assert validation["valid"]
    assert (
        validation[
            "transition_count"
        ]
        == 2
    )


def test_tampering_breaks_chain(
    tmp_path: Path,
):
    transitions_path = (
        tmp_path
        / "transitions.jsonl"
    )

    store = (
        PaperOrderLifecycleStore(
            state_path=(
                tmp_path / "state.json"
            ),
            transitions_path=(
                transitions_path
            ),
        )
    )

    intent = OrderIntent(
        asset="BTC-USD",
        side="BUY",
        quantity=0.01,
        reference_price=50_000.0,
        strategy_id="test",
        evidence_id="evidence",
    )

    store.create(intent)

    rows = transitions_path.read_text(
        encoding="utf-8"
    ).splitlines()

    payload = json.loads(
        rows[0]
    )

    payload["reason"] = "tampered"

    transitions_path.write_text(
        json.dumps(payload)
        + "\n",
        encoding="utf-8",
    )

    validation = (
        store
        .validate_transition_chain()
    )

    assert not validation["valid"]
    assert any(
        error.startswith(
            "EVENT_HASH_MISMATCH"
        )
        for error
        in validation["errors"]
    )
