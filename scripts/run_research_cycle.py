"""Run one controlled Atlas research cycle."""

from __future__ import annotations

import argparse

from atlas.investment.research_orchestrator import (
    build_orchestrator_report,
)
from atlas.investment.research_orchestrator.config import (
    DEFAULT_MAX_JOBS,
    DEFAULT_MAX_RECOVERY_ATTEMPTS,
    DEFAULT_TIMEOUT_SECONDS,
)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Preview or execute one dependency-aware "
            "Atlas research cycle."
        )
    )

    parser.add_argument(
        "--execute",
        action="store_true",
        help=(
            "Execute READY research jobs. "
            "Without this flag, the cycle is dry-run only."
        ),
    )

    parser.add_argument(
        "--max-jobs",
        type=int,
        default=DEFAULT_MAX_JOBS,
    )

    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=DEFAULT_TIMEOUT_SECONDS,
    )

    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
    )

    parser.add_argument(
        "--no-self-heal",
        action="store_true",
        help=(
            "Disable verified artifact recovery retries."
        ),
    )

    parser.add_argument(
        "--max-recovery-attempts",
        type=int,
        default=DEFAULT_MAX_RECOVERY_ATTEMPTS,
        help=(
            "Maximum execution attempts per unhealthy "
            "job before recovery fails."
        ),
    )

    mode_group = parser.add_mutually_exclusive_group()

    mode_group.add_argument(
        "--resume",
        action="store_true",
        help=(
            "Resume the last incomplete executable cycle "
            "and skip its successful jobs."
        ),
    )

    mode_group.add_argument(
        "--restart",
        action="store_true",
        help=(
            "Ignore any prior checkpoint and start a fresh "
            "execution cycle."
        ),
    )

    return parser.parse_args()


def main() -> None:
    arguments = parse_arguments()

    report = build_orchestrator_report(
        execute=arguments.execute,
        max_jobs=arguments.max_jobs,
        timeout_seconds=(
            arguments.timeout_seconds
        ),
        continue_on_failure=(
            arguments.continue_on_failure
        ),
        resume=arguments.resume,
        restart=arguments.restart,
        self_heal=(
            not arguments.no_self_heal
        ),
        max_recovery_attempts=(
            arguments.max_recovery_attempts
        ),
    )

    print(report["success"])
    print(report["summary"])
    print("Mode:", report["mode"])
    print("Run ID:", report["run_id"])
    print("Counts:", report["counts"])
    print("Outputs:")

    for name, path in report[
        "outputs"
    ].items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
