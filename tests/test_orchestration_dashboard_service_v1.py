from __future__ import annotations

import json
from pathlib import Path

from atlas.investment.orchestration.observability import (
    build_dashboard_snapshot,
    compute_record_hash,
)


def test_dashboard_service_is_read_only_and_complete(tmp_path: Path) -> None:
    scheduler = {
        "decision_id": "decision-dashboard",
        "jobs": [{"job_id": "one", "depends_on": []}],
    }
    report = {
        "schema_version": "g17.orchestration.v1",
        "run_id": "run-dashboard",
        "decision_id": "decision-dashboard",
        "status": "SUCCEEDED",
        "dry_run": True,
        "started_at": "2026-01-01T00:00:00+00:00",
        "finished_at": "2026-01-01T00:00:01+00:00",
        "elapsed_ms": 1,
        "jobs": [
            {
                "job_id": "one",
                "script": "scripts/one.py",
                "status": "DRY_RUN",
                "depends_on": [],
            }
        ],
        "safety": {
            "paper_only": True,
            "live_execution": False,
            "credentials_used": False,
            "shell_execution": False,
        },
        "duplicate_prevention": {"enabled": True},
        "previous_record_hash": "",
        "record_hash": "",
    }
    report["record_hash"] = compute_record_hash(report)

    scheduler_path = tmp_path / "scheduler.json"
    report_path = tmp_path / "latest.json"
    checkpoint_path = tmp_path / "checkpoint.json"
    history_path = tmp_path / "history.jsonl"

    scheduler_path.write_text(json.dumps(scheduler), encoding="utf-8")
    report_path.write_text(json.dumps(report), encoding="utf-8")
    checkpoint_path.write_text(
        json.dumps(
            {
                "decision_id": "decision-dashboard",
                "status": "SUCCEEDED",
                "paper_only": True,
                "live_execution": False,
            }
        ),
        encoding="utf-8",
    )
    history_path.write_text(json.dumps(report) + "\n", encoding="utf-8")

    snapshot = build_dashboard_snapshot(
        scheduler_decision_path=scheduler_path,
        latest_report_path=report_path,
        checkpoint_path=checkpoint_path,
        history_path=history_path,
    )

    assert snapshot.latest_report["safety"]["paper_only"] is True
    assert snapshot.latest_report["safety"]["live_execution"] is False
    assert snapshot.missing_artifacts == []
    assert snapshot.warnings == []
