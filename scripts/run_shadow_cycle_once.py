from __future__ import annotations

import argparse
import json

from atlas.investment.execution.shadow_loop import run_shadow_cycle


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run one restart-safe Atlas shadow paper cycle."
    )
    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
    )
    args = parser.parse_args()

    report = run_shadow_cycle(
        initial_cash=args.initial_cash,
        resume=True,
        write_outputs=True,
    )

    summary = {
        "success": report.get("success", False),
        "status": report.get("status", ""),
        "cycle_id": report.get("cycle_id", ""),
        "plan_id": report.get("plan_id", ""),
        "halt_reason": report.get("halt_reason", ""),
        "counts": report.get("counts", {}),
    }

    print(
        json.dumps(
            summary,
            sort_keys=True,
        )
    )

    return 0 if report.get("status") != "HALTED" else 2


if __name__ == "__main__":
    raise SystemExit(main())
