
"""Live Market Scheduler v1.

Runs the daily investment runbook on a timer in paper/safe mode.
This does not execute live trades.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime, UTC
from pathlib import Path


OUT_DIR = Path("output/investment_scheduler")
LOG_JSONL = OUT_DIR / "live_market_scheduler_log.jsonl"
STATUS_JSON = OUT_DIR / "live_market_scheduler_status.json"

RUNBOOK = "scripts/daily_investment_runbook.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--interval-minutes", type=float, default=60.0)
    parser.add_argument("--max-runs", type=int, default=1)
    parser.add_argument("--paper-only", action="store_true", default=True)
    return parser.parse_args()


def run_once(run_id: int) -> dict:
    started = datetime.now(UTC).isoformat()

    proc = subprocess.run(
        [sys.executable, RUNBOOK],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    ended = datetime.now(UTC).isoformat()

    result = {
        "run_id": run_id,
        "started": started,
        "ended": ended,
        "success": proc.returncode == 0,
        "returncode": proc.returncode,
        "command": f"{sys.executable} {RUNBOOK}",
        "mode": "paper_only",
        "stdout_tail": proc.stdout[-5000:],
        "stderr_tail": proc.stderr[-5000:],
    }

    write_log(result)
    write_status(result)

    return result


def write_log(result: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with LOG_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(result, ensure_ascii=False, default=str) + "\n")


def write_status(result: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    STATUS_JSON.write_text(json.dumps(result, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def main() -> None:
    args = parse_args()

    interval_seconds = max(args.interval_minutes * 60.0, 60.0)

    print("Live Market Scheduler v1")
    print(f"Interval minutes: {args.interval_minutes}")
    print(f"Max runs: {args.max_runs}")
    print("Mode: paper_only")
    print("Live trading: DISABLED")

    for run_id in range(1, args.max_runs + 1):
        print(f"RUN {run_id} starting...")
        result = run_once(run_id)

        print("OK" if result["success"] else "FAILED")
        print(f"Status: {STATUS_JSON}")

        if run_id < args.max_runs:
            print(f"Sleeping {interval_seconds} seconds...")
            time.sleep(interval_seconds)

    print("Scheduler complete.")


if __name__ == "__main__":
    main()
