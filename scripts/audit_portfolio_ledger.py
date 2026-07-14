"""Audit G.21 portfolio ledger history and latest snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.ledger import (
    LedgerIntegrityError,
    compute_hash,
    read_jsonl,
    validate_hash_chain,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_ledger"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    latest = args.output_dir / "latest_snapshot.json"
    fills = args.output_dir / "fill_history.jsonl"
    snapshots = args.output_dir / "snapshot_history.jsonl"

    try:
        latest_payload = json.loads(latest.read_text(encoding="utf-8-sig"))
        fill_records = read_jsonl(fills)
        snapshot_records = read_jsonl(snapshots)
        validate_hash_chain(fill_records)
        validate_hash_chain(snapshot_records)

        if latest_payload.get("record_hash") != compute_hash(latest_payload):
            raise LedgerIntegrityError("Latest snapshot hash mismatch")
        if not snapshot_records:
            raise LedgerIntegrityError("Snapshot history is empty")
        if snapshot_records[-1]["record_hash"] != latest_payload["record_hash"]:
            raise LedgerIntegrityError("Latest snapshot does not match history tail")
        if latest_payload.get("paper_only") is not True:
            raise LedgerIntegrityError("paper_only must be true")
        if latest_payload.get("live_execution") is not False:
            raise LedgerIntegrityError("live_execution must be false")
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        LedgerIntegrityError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "fill_records": len(fill_records),
                "snapshot_records": len(snapshot_records),
                "fill_history_valid": True,
                "snapshot_history_valid": True,
                "latest_snapshot_hash_valid": True,
                "paper_only": True,
                "live_execution": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
