"""Tests for the read-only paper execution dashboard model."""

from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.execution.dashboard import (
    build_paper_execution_dashboard_model,
)


def write_json(
    path: Path,
    payload: dict,
) -> None:
    path.write_text(
        json.dumps(payload),
        encoding="utf-8",
    )


def test_empty_dashboard_is_healthy(
    tmp_path: Path,
):
    model = (
        build_paper_execution_dashboard_model(
            intent_plan_path=(
                tmp_path / "plan.json"
            ),
            execution_report_path=(
                tmp_path / "report.json"
            ),
            execution_ledger_path=(
                tmp_path / "ledger.jsonl"
            ),
            lifecycle_state_path=(
                tmp_path / "state.json"
            ),
            lifecycle_transitions_path=(
                tmp_path
                / "transitions.jsonl"
            ),
        )
    )

    assert model["success"]
    assert (
        model["status"]
        == "HEALTHY"
    )
    assert (
        model["lifecycle"][
            "chain_valid"
        ]
    )


def test_model_loads_plan_and_execution(
    tmp_path: Path,
):
    plan = tmp_path / "plan.json"
    report = tmp_path / "report.json"

    write_json(
        plan,
        {
            "plan_id": "PLAN-1",
            "account_equity": 10_000.0,
            "target_weight_total": 0.7,
            "minimum_cash_weight": 0.2,
            "total_turnover_weight": 0.25,
            "counts": {
                "generated_intents": 1,
            },
            "targets": [
                {
                    "asset": "BTC-USD",
                    "target_weight": 0.25,
                }
            ],
            "intents": [
                {
                    "asset": "BTC-USD",
                    "side": "BUY",
                }
            ],
            "contract": {
                "intent_generation_only": True,
                "submits_orders": False,
                "mutates_account": False,
                "live_credentials_used": False,
                "broker_neutral": True,
            },
        },
    )

    write_json(
        report,
        {
            "success": True,
            "mode": "PAPER",
            "live_execution": False,
            "risk": {
                "approved": True,
            },
            "order": {
                "status": "FILLED",
                "filled_quantity": 0.01,
            },
            "fills": [
                {
                    "asset": "BTC-USD",
                    "quantity": 0.01,
                }
            ],
            "account_after": {
                "cash": 9_500.0,
                "positions": {
                    "BTC-USD": {
                        "quantity": 0.01,
                        "average_price": 50_000.0,
                        "mark_price": 50_000.0,
                    }
                },
            },
            "contract": {
                "paper_only": True,
                "live_credentials_used": False,
                "broker_neutral": True,
            },
        },
    )

    model = (
        build_paper_execution_dashboard_model(
            intent_plan_path=plan,
            execution_report_path=report,
            execution_ledger_path=(
                tmp_path / "ledger.jsonl"
            ),
            lifecycle_state_path=(
                tmp_path / "state.json"
            ),
            lifecycle_transitions_path=(
                tmp_path
                / "transitions.jsonl"
            ),
        )
    )

    assert (
        model["intent_plan"][
            "plan_id"
        ]
        == "PLAN-1"
    )

    assert (
        model["latest_execution"][
            "order"
        ][
            "status"
        ]
        == "FILLED"
    )

    assert (
        model["latest_execution"][
            "positions"
        ][0][
            "asset"
        ]
        == "BTC-USD"
    )


def test_live_execution_marks_model_critical(
    tmp_path: Path,
):
    report = tmp_path / "report.json"

    write_json(
        report,
        {
            "success": True,
            "live_execution": True,
            "contract": {
                "paper_only": False,
            },
        },
    )

    model = (
        build_paper_execution_dashboard_model(
            intent_plan_path=(
                tmp_path / "plan.json"
            ),
            execution_report_path=report,
            execution_ledger_path=(
                tmp_path / "ledger.jsonl"
            ),
            lifecycle_state_path=(
                tmp_path / "state.json"
            ),
            lifecycle_transitions_path=(
                tmp_path
                / "transitions.jsonl"
            ),
        )
    )

    assert (
        model["status"]
        == "CRITICAL"
    )
