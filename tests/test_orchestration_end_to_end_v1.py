from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

from atlas.investment.orchestration.observability import build_dashboard_snapshot
from atlas.investment.orchestration.reconciliation import reconcile


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_PATH = ROOT / "scripts" / "run_investment_orchestrator.py"
SPEC = importlib.util.spec_from_file_location("g17_section3_runtime", RUNTIME_PATH)
assert SPEC is not None and SPEC.loader is not None
runtime = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = runtime
SPEC.loader.exec_module(runtime)


def test_scheduler_to_orchestration_to_reconciliation(tmp_path: Path) -> None:
    scheduler_payload = {
        "decision_id": "decision-e2e",
        "jobs": [
            {
                "job_id": "one",
                "script": "scripts/one.py",
                "depends_on": [],
            },
            {
                "job_id": "two",
                "script": "scripts/two.py",
                "depends_on": ["one"],
            },
        ],
    }

    scheduler_path = tmp_path / "output/investment_scheduler/scheduler_decision.json"
    scheduler_path.parent.mkdir(parents=True, exist_ok=True)
    scheduler_path.write_text(json.dumps(scheduler_payload), encoding="utf-8")

    plan = runtime.OrchestrationPlan.from_mapping(scheduler_payload)
    runtime.run(
        plan,
        repo_root=tmp_path,
        output_dir=Path("output/investment_orchestration"),
        dry_run=True,
        allowlist={"scripts/one.py", "scripts/two.py"},
    )

    orchestration_dir = tmp_path / "output/investment_orchestration"
    snapshot = build_dashboard_snapshot(
        scheduler_decision_path=scheduler_path,
        latest_report_path=orchestration_dir / "latest_report.json",
        checkpoint_path=orchestration_dir / "checkpoint.json",
        history_path=orchestration_dir / "history.jsonl",
    )

    assert snapshot.history_chain_valid is True
    assert snapshot.dependency_chain_valid is True
    assert snapshot.stale_scheduler_decision is False

    report = reconcile(
        snapshot.scheduler_decision,
        snapshot.latest_report,
    )
    assert report.status == "PASS"
    assert report.matched_job_count == 2
    assert report.paper_only is True
    assert report.live_execution is False
