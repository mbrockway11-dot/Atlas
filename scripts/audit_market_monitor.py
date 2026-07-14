"""Audit the G.23 market-monitor snapshot."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.market_monitor import compute_hash


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("output/investment_market_monitor/latest_snapshot.json"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        payload = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, dict):
            raise ValueError("Snapshot root must be an object")
        if payload.get("record_hash") != compute_hash(payload):
            raise ValueError("Snapshot hash mismatch")
        if payload.get("paper_only") is not True:
            raise ValueError("paper_only must be true")
        if payload.get("live_execution") is not False:
            raise ValueError("live_execution must be false")
        if payload.get("credentials_used") is not False:
            raise ValueError("credentials_used must be false")
        if not payload.get("tickers"):
            raise ValueError("Snapshot has no tickers")
        if not payload.get("consolidated"):
            raise ValueError("Snapshot has no consolidated ticker")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "symbol": payload.get("symbol"),
                "venue_count": len(payload["tickers"]),
                "record_hash_valid": True,
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
