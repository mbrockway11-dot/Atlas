"""Restart and checkpoint tests for the paper shadow loop."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)


def write_plan(
    path: Path,
) -> None:
    path.write_text(
        json.dumps({
            "plan_id": "PLAN-RESUME",
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
                    "evidence_id": "resume",
                    "intent_id": "INTENT-A",
                },
                {
                    "asset": "ETH-USD",
                    "side": "BUY",
                    "quantity": 0.01,
                    "reference_price": 2_000.0,
                    "strategy_id": "test",
                    "evidence_id": "resume",
                    "intent_id": "INTENT-B",
                },
            ],
        }),
        encoding="utf-8",
    )


def test_cycle_resumes_remaining_intents(
    tmp_path: Path,
    monkeypatch,
):
    plan = tmp_path / "plan.json"
    write_plan(plan)

    monkeypatch.setattr(
        "atlas.investment.execution.shadow_loop."
        "validate_execution_provenance",
        lambda: {
            "valid": True,
            "errors": [],
        },
    )

    common = {
        "intent_plan_path": plan,
        "account_path": (
            tmp_path / "account.json"
        ),
        "checkpoint_path": (
            tmp_path / "checkpoint.json"
        ),
        "report_path": (
            tmp_path / "report.json"
        ),
        "history_path": (
            tmp_path / "history.jsonl"
        ),
        "lifecycle_state_path": (
            tmp_path / "state.json"
        ),
        "lifecycle_transitions_path": (
            tmp_path
            / "transitions.jsonl"
        ),
    }

    first = run_shadow_cycle(
        **common,
        maximum_intents=1,
        write_outputs=True,
    )

    assert (
        first["status"]
        == "PAUSED"
    )

    second = run_shadow_cycle(
        **common,
        write_outputs=True,
    )

    assert second["resumed"]

    assert (
        second["status"]
        == "COMPLETED"
    )

    assert (
        second["counts"][
            "completed_total"
        ]
        == 2
    )

    assert (
        second["counts"][
            "processed_this_run"
        ]
        == 1
    )


def test_completed_plan_does_not_reexecute(
    tmp_path: Path,
    monkeypatch,
):
    plan = tmp_path / "plan.json"
    write_plan(plan)

    monkeypatch.setattr(
        "atlas.investment.execution.shadow_loop."
        "validate_execution_provenance",
        lambda: {
            "valid": True,
            "errors": [],
        },
    )

    common = {
        "intent_plan_path": plan,
        "account_path": (
            tmp_path / "account.json"
        ),
        "checkpoint_path": (
            tmp_path / "checkpoint.json"
        ),
        "report_path": (
            tmp_path / "report.json"
        ),
        "history_path": (
            tmp_path / "history.jsonl"
        ),
        "lifecycle_state_path": (
            tmp_path / "state.json"
        ),
        "lifecycle_transitions_path": (
            tmp_path
            / "transitions.jsonl"
        ),
    }

    run_shadow_cycle(
        **common,
        write_outputs=True,
    )

    repeated = run_shadow_cycle(
        **common,
        write_outputs=True,
    )

    assert (
        repeated["counts"][
            "processed_this_run"
        ]
        == 0
    )

    assert (
        repeated["status"]
        == "COMPLETED"
    )
