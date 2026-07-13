"""Create a signed approval for the current Atlas remediation plan."""

from __future__ import annotations

import argparse

from atlas.investment.control_plane_approval import (
    APPROVAL_JSON,
    REMEDIATION_PLAN_JSON,
    create_approval,
    load_json,
    write_approval,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Approve the exact current Atlas "
            "remediation-plan hash."
        )
    )

    parser.add_argument(
        "--approved-by",
        required=True,
    )

    parser.add_argument(
        "--ttl-minutes",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--max-steps",
        type=int,
        default=None,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    plan = load_json(
        REMEDIATION_PLAN_JSON
    )

    approval = create_approval(
        plan,
        approved_by=args.approved_by,
        ttl_minutes=args.ttl_minutes,
        max_steps=args.max_steps,
    )

    write_approval(
        approval,
        APPROVAL_JSON,
    )

    print(
        "ATLAS REMEDIATION APPROVED"
    )
    print(
        "Approval ID:",
        approval["approval_id"],
    )
    print(
        "Approved by:",
        approval["approved_by"],
    )
    print(
        "Plan hash:",
        approval["plan_hash"],
    )
    print(
        "Expires at:",
        approval["expires_at"],
    )
    print(
        "Approved jobs:",
        len(
            approval[
                "approved_job_ids"
            ]
        ),
    )
    print(
        "Approval file:",
        APPROVAL_JSON,
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
