"""Audit G.23 Section 2 public market-monitor runtime artifacts."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.market_monitor import compute_hash


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_market_monitor/live"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    status_path = args.output_dir / "monitor_status.json"

    try:
        status = json.loads(status_path.read_text(encoding="utf-8-sig"))
        if status.get("paper_only") is not True:
            raise ValueError("paper_only must be true")
        if status.get("live_execution") is not False:
            raise ValueError("live_execution must be false")
        if status.get("credentials_used") is not False:
            raise ValueError("credentials_used must be false")

        snapshots = sorted(
            path
            for path in args.output_dir.glob("*.json")
            if path.name != "monitor_status.json"
        )
        if not snapshots:
            raise ValueError("No market snapshots were produced")

        snapshot_results = []
        for path in snapshots:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
            if payload.get("record_hash") != compute_hash(payload):
                raise ValueError(f"Snapshot hash mismatch: {path.name}")
            if payload.get("paper_only") is not True:
                raise ValueError(f"Unsafe snapshot: {path.name}")
            snapshot_results.append(
                {
                    "file": path.name,
                    "symbol": payload.get("symbol"),
                    "venue_count": len(payload.get("tickers", [])),
                    "record_hash_valid": True,
                }
            )

        collectors = status.get("collectors", [])
        if not collectors:
            raise ValueError("No collector status records exist")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "collectors": collectors,
                "snapshots": snapshot_results,
                "snapshots_written": status.get("snapshots_written", 0),
                "paper_only": True,
                "live_execution": False,
                "credentials_used": False,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
