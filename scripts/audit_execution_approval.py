"""Audit G.20 supervised execution approval artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.approval import (
    ApprovalPersistenceError,
    compute_hash,
    read_history,
    validate_history,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--latest",
        type=Path,
        default=Path("output/investment_approval/latest_approval.json"),
    )
    parser.add_argument(
        "--history",
        type=Path,
        default=Path("output/investment_approval/approval_history.jsonl"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        latest = json.loads(args.latest.read_text(encoding="utf-8-sig"))
        if not isinstance(latest, dict):
            raise ValueError("Latest approval artifact must be an object")

        records = read_history(args.history)
        validate_history(records)
        if not records:
            raise ValueError("Approval history is empty")
        if records[-1].get("approval_hash") != latest.get("approval_hash"):
            raise ValueError("Latest approval does not match history tail")
        if latest.get("approval_hash") != compute_hash(latest):
            raise ValueError("Latest approval hash mismatch")
        if latest.get("paper_only") is not True:
            raise ValueError("paper_only must be true")
        if latest.get("live_execution") is not False:
            raise ValueError("live_execution must be false")
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        ApprovalPersistenceError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "approval_id": latest.get("approval_id"),
                "status": latest.get("status"),
                "history_records": len(records),
                "history_chain_valid": True,
                "approval_hash_valid": True,
                "paper_only": True,
                "live_execution": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
