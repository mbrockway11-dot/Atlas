"""Approve a pending supervised paper execution request."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.approval import ApprovalError, ApprovalService


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approval-id", required=True)
    parser.add_argument("--approver", required=True)
    parser.add_argument("--plan-hash", required=True)
    parser.add_argument("--reason", default="")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_approval"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        decision = ApprovalService(output_dir=args.output_dir).decide(
            approval_id=args.approval_id,
            approve=True,
            approver_identity_reference=args.approver,
            expected_plan_hash=args.plan_hash,
            reason=args.reason,
        )
    except (OSError, ValueError, ApprovalError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(json.dumps({"success": True, "decision": asdict(decision)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
