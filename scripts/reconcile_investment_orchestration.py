"""Reconcile a scheduler decision with the latest orchestration report."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

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
        "--orchestration-report",
        type=Path,
        default=Path("output/investment_orchestration/latest_report.json"),
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/investment_orchestration/reconciliation_report.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        scheduler = read_object(args.scheduler_decision)
        orchestration = read_object(args.orchestration_report)
        report = reconcile(scheduler, orchestration)
    except (OSError, ValueError, json.JSONDecodeError, ReconciliationError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    payload = asdict(report)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"success": report.status == "PASS", "report": payload}, indent=2))
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
