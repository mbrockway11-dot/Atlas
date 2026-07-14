from __future__ import annotations

import json
from pathlib import Path

import pytest

from atlas.investment.orchestration.observability import (
    ObservabilityError,
    build_dashboard_snapshot,
    compute_record_hash,
    validate_dependency_order,
    validate_history_chain,
)


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def make_record(
    decision_id: str,
    *,
    status: str = "SUCCEEDED",
    previous: str = "",
) -> dict:
    record = {
        "schema_version": "g17.orchestration.v1",
        "run_id": f"run-{decision_id}",
        "decision_id": decision_id,
        "status": status,
        "dry_run": True,
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:00:01+00:00",
        "elapsed_ms": 1000,
        "jobs": [
            {
                "job_id": "one",
                "script": "scripts/one.py",
                "status": "DRY_RUN",
                "depends_on": [],
            },
            {
                "job_id": "two",
                "script": "scripts/two.py",
                "status": "DRY_RUN",
                "depends_on": ["one"],
            },
        ],
        "safety": {
            "paper_only": True,
            "live_execution": False,
        },
        "duplicate_prevention": {"enabled": True},
        "previous_record_hash": previous,
        "record_hash": "",
    }
    record["record_hash"] = compute_record_hash(record)
    return record


def test_snapshot_exposes_operational_state(tmp_path: Path) -> None:
    scheduler = tmp_path / "scheduler.json"
    latest = tmp_path / "latest.json"
    checkpoint = tmp_path / "checkpoint.json"
    history = tmp_path / "history.jsonl"

    record = make_record("decision-1")
    write_json(
        scheduler,
        {
            "decision_id": "decision-1",
            "jobs": [
                {"job_id": "one", "depends_on": []},
                {"job_id": "two", "depends_on": ["one"]},
            ],
        },
    )
    write_json(latest, record)
    write_json(checkpoint, {"decision_id": "decision-1", "status": "SUCCEEDED"})
    history.write_text(json.dumps(record) + "\n", encoding="utf-8")

    snapshot = build_dashboard_snapshot(
        scheduler_decision_path=scheduler,
        latest_report_path=latest,
        checkpoint_path=checkpoint,
        history_path=history,
    )

    assert snapshot.history_chain_valid is True
    assert snapshot.dependency_chain_valid is True
    assert snapshot.duplicate_prevention_enabled is True
    assert snapshot.stale_scheduler_decision is False
    assert snapshot.latest_successful_cycle["decision_id"] == "decision-1"


def test_history_tampering_is_reported(tmp_path: Path) -> None:
    record = make_record("decision-1")
    record["status"] = "FAILED"
    history = tmp_path / "history.jsonl"
    history.write_text(json.dumps(record) + "\n", encoding="utf-8")

    with pytest.raises(ObservabilityError, match="History hash mismatch"):
        validate_history_chain([record])


def test_out_of_order_dependency_is_rejected() -> None:
    with pytest.raises(ObservabilityError, match="Out-of-order"):
        validate_dependency_order(
            [
                {"job_id": "two", "depends_on": ["one"]},
                {"job_id": "one", "depends_on": []},
            ]
        )
