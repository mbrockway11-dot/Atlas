"""Publish one paper-only event into the G.22 event store."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from atlas.investment.events import (
    AtlasEvent,
    EventBusError,
    EventStore,
    EventType,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("output/investment_events"),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        payload = json.loads(args.input.read_text(encoding="utf-8-sig"))
        event = AtlasEvent(
            event_id=str(payload["event_id"]),
            event_type=EventType(str(payload["event_type"]).upper()),
            aggregate_type=str(payload["aggregate_type"]),
            aggregate_id=str(payload["aggregate_id"]),
            occurred_at=str(payload["occurred_at"]),
            source=str(payload["source"]),
            payload=dict(payload.get("payload", {})),
            correlation_id=payload.get("correlation_id"),
            causation_id=payload.get("causation_id"),
            paper_only=bool(payload.get("paper_only", True)),
            live_execution=bool(payload.get("live_execution", False)),
            credentials_used=bool(payload.get("credentials_used", False)),
        )
        stored = EventStore(output_dir=args.output_dir).append(event)
    except (
        OSError,
        ValueError,
        KeyError,
        json.JSONDecodeError,
        EventBusError,
    ) as exc:
        print(json.dumps({"success": False, "error": str(exc)}, indent=2))
        return 2

    result = asdict(stored)
    result["event_type"] = stored.event_type.value
    print(json.dumps({"success": True, "event": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
