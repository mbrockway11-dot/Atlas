"""Dispatch an explicitly approved Atlas remediation plan."""

from __future__ import annotations

import argparse

from atlas.investment.control_plane_dispatch import (
    dispatch_approved_plan,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Validate and dispatch the signed "
            "Atlas remediation approval."
        )
    )

    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=1800,
    )

    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    result = dispatch_approved_plan(
        timeout_seconds=(
            args.timeout_seconds
        ),
        continue_on_failure=(
            args.continue_on_failure
        ),
    )

    print(
        "ATLAS CONTROLLED DISPATCH "
        + (
            "SUCCEEDED"
            if result["success"]
            else "FAILED"
        )
    )
    print(
        "Approval ID:",
        result["approval_id"],
    )
    print(
        "Approved by:",
        result["approved_by"],
    )
    print(
        "Run ID:",
        result["run_id"],
    )
    print(
        "Approved jobs:",
        len(
            result[
                "approved_job_ids"
            ]
        ),
    )

    return (
        0
        if result["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
