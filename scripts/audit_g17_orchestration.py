"""Audit G.17 orchestration observability, reconciliation, and safety."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.orchestration.observability import (
    ObservabilityError,
    build_dashboard_snapshot,
)
from atlas.investment.orchestration.reconciliation import (
    ReconciliationError,
    reconcile,
)


def read_object(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scheduler-decision",
        type=Path,
        default=Path("output/investment_scheduler/scheduler_decision.json"),
    )
    parser.add_argument(
        "--latest-report",
        type=Path,
        default=Path("output/investment_orchestration/latest_report.json"),
    )
    parser.add_argument(
        "--checkpoint",
        type=Path,
        default=Path("output/investment_orchestration/checkpoint.json"),
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("output/investment_orchestration/history.jsonl"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        snapshot = build_dashboard_snapshot(
            scheduler_decision_path=args.scheduler_decision,
            latest_report_path=args.latest_report,
            checkpoint_path=args.checkpoint,
            history_path=args.history,
        )

        if snapshot.scheduler_decision is None:
            raise ValueError("Scheduler decision artifact is missing")
        if snapshot.latest_report is None:
            raise ValueError("Latest orchestration report is missing")

        reconciliation = reconcile(
            snapshot.scheduler_decision,
            snapshot.latest_report,
        )

        checks = {
            "history_chain_valid": snapshot.history_chain_valid,
            "dependency_chain_valid": snapshot.dependency_chain_valid,
            "duplicate_prevention_enabled": snapshot.duplicate_prevention_enabled,
            "scheduler_decision_current": not snapshot.stale_scheduler_decision,
            "reconciliation_passed": reconciliation.status == "PASS",
            "paper_only": reconciliation.paper_only,
            "live_execution_disabled": not reconciliation.live_execution,
        }
        success = all(checks.values())

        payload = {
            "success": success,
            "checks": checks,
            "snapshot": asdict(snapshot),
            "reconciliation": asdict(reconciliation),
        }
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        ObservabilityError,
        ReconciliationError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
