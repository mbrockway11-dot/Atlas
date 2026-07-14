"""Replay G.22 investment events deterministically."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.events import (
    EventBusError,
    EventStore,
    replay_events,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_events"),
    )
    parser.add_argument("--offset", type=int, default=0)
    parser.add_argument("--event-type", default="")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        store = EventStore(output_dir=args.output_dir)
        events = store.read_from(args.offset)
        if args.event_type:
            event_type = args.event_type.upper()
            events = [
                event
                for event in events
                if str(event.get("event_type", "")).upper() == event_type
            ]

        replayed_ids: list[str] = []
        result = replay_events(
            events,
            lambda event: replayed_ids.append(str(event.get("event_id", ""))),
        )
    except (OSError, ValueError, EventBusError) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    print(
        json.dumps(
            {
                "success": True,
                "result": asdict(result),
                "event_ids": replayed_ids,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
