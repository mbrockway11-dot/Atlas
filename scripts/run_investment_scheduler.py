"""Evaluate one Atlas investment scheduler iteration.

This command writes a command plan but does not execute workflow commands.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.scheduling import (
    SCHEDULER_STATE_JSON,
    SchedulerLock,
    evaluate_scheduler,
    load_scheduler_state,
    write_scheduler_outputs,
)


LOCK_PATH = Path(
    "output/investment_scheduler/"
    "scheduler.lock"
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Evaluate one Atlas scheduler iteration "
            "without executing workflow commands."
        )
    )

    parser.add_argument(
        "--state-file",
        default=str(
            SCHEDULER_STATE_JSON
        ),
    )

    parser.add_argument(
        "--json",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    state_path = Path(
        args.state_file
    )

    with SchedulerLock(
        LOCK_PATH
    ):
        state = load_scheduler_state(
            state_path
        )

        decision = evaluate_scheduler(
            state=state
        )

        write_scheduler_outputs(
            decision=decision,
            state=None,
        )

    if args.json:
        print(
            json.dumps(
                decision,
                indent=2,
                sort_keys=True,
            )
        )

        return 0

    print(
        "ATLAS INVESTMENT SCHEDULER READY"
    )

    print(
        "Decision ID:",
        decision["decision_id"],
    )

    print(
        "Evaluated at:",
        decision["evaluated_at"],
    )

    print(
        "Due jobs:",
        decision["due_jobs"],
    )

    for row in decision[
        "decisions"
    ]:
        print(
            row["job"]["name"],
            (
                "DUE"
                if row["due"]
                else "IDLE"
            ),
            row["reasons"],
        )

    print(
        "Commands executed: False"
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
