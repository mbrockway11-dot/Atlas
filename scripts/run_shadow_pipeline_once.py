from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.execution.shadow_pipeline import run_shadow_pipeline


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Run one complete Atlas market-snapshot-to-paper-execution cycle."
        )
    )
    parser.add_argument(
        "--targets",
        required=True,
        help="JSON artifact containing strategy target allocations.",
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
    )
    parser.add_argument(
        "--maximum-intents",
        type=int,
        default=None,
    )
    args = parser.parse_args()

    report = run_shadow_pipeline(
        targets_path=Path(args.targets),
        initial_cash=args.initial_cash,
        maximum_intents=args.maximum_intents,
        resume=True,
        write_outputs=True,
    )

    summary = {
        "success": bool(report.get("success", False)),
        "status": report.get("status", ""),
        "pipeline_id": report.get("pipeline_id", ""),
        "snapshot_id": report.get("snapshot_id", ""),
        "plan_id": report.get("plan_id", ""),
        "cycle_id": report.get("cycle_id", ""),
        "market_data": report.get("market_data", {}),
        "intent_plan": report.get("intent_plan", {}),
        "shadow_cycle": report.get("shadow_cycle", {}),
        "performance": report.get("performance", {}),
        "errors": report.get("errors", []),
    }

    print(json.dumps(summary, sort_keys=True))

    return 0 if report.get("success", False) else 2


if __name__ == "__main__":
    raise SystemExit(main())
