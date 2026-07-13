"""End-to-end tests for the G.9 paper shadow cycle."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution import (
    RiskLimits,
)
from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)


def write_plan(
    path: Path,
) -> None:
    path.write_text(
        json.dumps({
            "plan_id": "PLAN-1",
            "live_execution": False,
            "contract": {
                "intent_generation_only": True,
                "submits_orders": False,
            },
            "intents": [
                {
                    "asset": "BTC-USD",
                    "side": "BUY",
                    "quantity": 0.01,
                    "reference_price": 50_000.0,
                    "strategy_id": "test",
                    "evidence_id": "evidence-1",
                    "order_type": "MARKET",
                    "time_in_force": "IOC",
                    "maximum_slippage_bps": 25.0,
                    "reduce_only": False,
                    "intent_id": "INTENT-1",
                },
                {
                    "asset": "ETH-USD",
                    "side": "BUY",
                    "quantity": 0.1,
                    "reference_price": 2_000.0,
                    "strategy_id": "test",
                    "evidence_id": "evidence-1",
                    "order_type": "MARKET",
                    "time_in_force": "IOC",
                    "maximum_slippage_bps": 25.0,
                    "reduce_only": False,
                    "intent_id": "INTENT-2",
                },
            ],
        }),
        encoding="utf-8",
    )


def test_shadow_cycle_executes_all_intents(
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
        limits=RiskLimits(
            maximum_order_notional=(
                1_000.0
            ),
            maximum_asset_notional=(
                2_000.0
            ),
            maximum_gross_exposure=(
                5_000.0
            ),
        ),
        write_outputs=False,
    )

    assert report["success"]
    assert (
        report["status"]
        == "COMPLETED"
    )
    assert (
        report["counts"][
            "completed_total"
        ]
        == 2
    )
    assert (
        "BTC-USD"
        in report[
            "account_after"
        ][
            "positions"
        ]
    )


def test_shadow_cycle_is_paper_only(
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
        maximum_intents=1,
        write_outputs=False,
    )

    assert not report[
        "live_execution"
    ]

    assert report[
        "contract"
    ][
        "paper_only"
    ]

    assert not report[
        "contract"
    ][
        "live_credentials_used"
    ]
