"""Safety-halt tests for the autonomous paper shadow loop."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)


def test_live_plan_is_rejected(
    tmp_path: Path,
):
    plan = tmp_path / "plan.json"

    plan.write_text(
        json.dumps({
            "plan_id": "LIVE-PLAN",
            "live_execution": True,
            "contract": {
                "submits_orders": False,
            },
            "intents": [],
        }),
        encoding="utf-8",
    )

    try:
        run_shadow_cycle(
            intent_plan_path=plan,
            account_path=(
                tmp_path / "account.json"
            ),
            checkpoint_path=(
                tmp_path / "checkpoint.json"
            ),
            report_path=(
                tmp_path / "report.json"
            ),
            history_path=(
                tmp_path / "history.jsonl"
            ),
            lifecycle_state_path=(
                tmp_path / "state.json"
            ),
            lifecycle_transitions_path=(
                tmp_path
                / "transitions.jsonl"
            ),
            write_outputs=False,
        )
    except RuntimeError as error:
        assert (
            "LIVE_EXECUTION_FORBIDDEN"
            in str(error)
        )
    else:
        raise AssertionError(
            "Live plan was not rejected."
        )


def test_provenance_failure_halts(
    tmp_path: Path,
    monkeypatch,
):
    plan = tmp_path / "plan.json"

    plan.write_text(
        json.dumps({
            "plan_id": "PLAN-HALT",
            "contract": {
                "submits_orders": False,
            },
            "intents": [
                {
                    "asset": "BTC-USD",
                    "side": "BUY",
                    "quantity": 0.001,
                    "reference_price": 50_000.0,
                    "strategy_id": "test",
                    "evidence_id": "halt",
                    "intent_id": "INTENT-HALT",
                }
            ],
        }),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "atlas.investment.execution.shadow_loop."
        "validate_execution_provenance",
        lambda: {
            "valid": False,
            "errors": [
                "EVENT_HASH_MISMATCH"
            ],
        },
    )

    report = run_shadow_cycle(
        intent_plan_path=plan,
        account_path=(
            tmp_path / "account.json"
        ),
        checkpoint_path=(
            tmp_path / "checkpoint.json"
        ),
        report_path=(
            tmp_path / "report.json"
        ),
        history_path=(
            tmp_path / "history.jsonl"
        ),
        lifecycle_state_path=(
            tmp_path / "state.json"
        ),
        lifecycle_transitions_path=(
            tmp_path
            / "transitions.jsonl"
        ),
        write_outputs=False,
    )

    assert not report["success"]

    assert (
        report["status"]
        == "HALTED"
    )

    assert (
        report["halt_reason"]
        == "PROVENANCE_CHAIN_INVALID"
    )
