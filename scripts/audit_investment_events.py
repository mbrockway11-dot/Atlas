"""Audit G.22 event-store integrity and safety."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from atlas.investment.events import (
    EventBusError,
    EventStore,
    compute_hash,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_events"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        store = EventStore(output_dir=args.output_dir)
        events = store.all()
        if not events:
            raise ValueError("Event store is empty")

        latest = json.loads(store.latest_path.read_text(encoding="utf-8-sig"))
        if latest.get("record_hash") != compute_hash(latest):
            raise ValueError("Latest event hash mismatch")
        if latest.get("record_hash") != events[-1].get("record_hash"):
            raise ValueError("Latest event does not match event-store tail")

        for event in events:
            if event.get("paper_only") is not True:
                raise ValueError("paper_only must be true")
            if event.get("live_execution") is not False:
                raise ValueError("live_execution must be false")
            if event.get("credentials_used") is not False:
                raise ValueError("credentials_used must be false")
    except (
        OSError,
        ValueError,
        json.JSONDecodeError,
        EventBusError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "event_count": len(events),
                "first_event_id": events[0]["event_id"],
                "last_event_id": events[-1]["event_id"],
                "history_chain_valid": True,
                "latest_event_hash_valid": True,
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
