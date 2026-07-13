"""Atomic market snapshot persistence and tamper-evident audit chain."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Mapping


OUTPUT_DIR = Path(
    "output/investment_market_data"
)

LATEST_MARKET_SNAPSHOT_JSON = (
    OUTPUT_DIR
    / "latest_market_snapshot.json"
)

MARKET_DATA_AUDIT_JSONL = (
    OUTPUT_DIR
    / "market_data_audit.jsonl"
)


def write_market_snapshot(
    snapshot: Mapping[
        str,
        Any,
    ],
    *,
    path: Path = (
        LATEST_MARKET_SNAPSHOT_JSON
    ),
    audit_path: Path = (
        MARKET_DATA_AUDIT_JSONL
    ),
) -> dict[str, Any]:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = dict(
        snapshot
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)

    event = append_market_data_audit(
        {
            "event_type": (
                "MARKET_SNAPSHOT_WRITTEN"
            ),
            "snapshot_id": str(
                payload.get(
                    "snapshot_id",
                    "",
                )
            ),
            "success": bool(
                payload.get(
                    "success",
                    False,
                )
            ),
            "counts": payload.get(
                "counts",
                {},
            ),
            "path": str(path),
        },
        path=audit_path,
    )

    return event


def load_market_snapshot(
    path: Path = (
        LATEST_MARKET_SNAPSHOT_JSON
    ),
) -> dict[str, Any]:
    if not path.exists():
        return {}

    payload = json.loads(
        path.read_text(
            encoding="utf-8"
        )
    )

    if not isinstance(
        payload,
        dict,
    ):
        raise ValueError(
            "MARKET_SNAPSHOT_INVALID"
        )

    return payload


def append_market_data_audit(
    payload: Mapping[
        str,
        Any,
    ],
    *,
    path: Path = (
        MARKET_DATA_AUDIT_JSONL
    ),
) -> dict[str, Any]:
    previous_hash = ""

    records = read_market_data_audit(
        path
    )

    if records:
        previous_hash = str(
            records[-1].get(
                "event_hash",
                "",
            )
        )

    event = {
        "recorded_at": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        **dict(payload),
        "previous_event_hash": (
            previous_hash
        ),
    }

    event["event_hash"] = (
        market_data_event_hash(
            event
        )
    )

    event["event_id"] = (
        "MARKET-EVENT-"
        + event[
            "event_hash"
        ][:24]
    )

    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                event,
                sort_keys=True,
                default=str,
            )
            + "\n"
        )

    return event


def read_market_data_audit(
    path: Path = (
        MARKET_DATA_AUDIT_JSONL
    ),
) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    records: list[
        dict[str, Any]
    ] = []

    with path.open(
        "r",
        encoding="utf-8",
    ) as handle:
        for line in handle:
            text = line.strip()

            if not text:
                continue

            try:
                payload = json.loads(
                    text
                )
            except json.JSONDecodeError:
                continue

            if isinstance(
                payload,
                dict,
            ):
                records.append(
                    payload
                )

    return records


def validate_market_data_audit(
    *,
    path: Path = (
        MARKET_DATA_AUDIT_JSONL
    ),
) -> dict[str, Any]:
    records = (
        read_market_data_audit(
            path
        )
    )

    errors: list[str] = []
    previous_hash = ""

    for index, event in enumerate(
        records,
        start=1,
    ):
        if str(
            event.get(
                "previous_event_hash",
                "",
            )
        ) != previous_hash:
            errors.append(
                "PREVIOUS_HASH_MISMATCH:"
                + str(index)
            )

        expected = (
            market_data_event_hash(
                event
            )
        )

        stored = str(
            event.get(
                "event_hash",
                "",
            )
        )

        if expected != stored:
            errors.append(
                "EVENT_HASH_MISMATCH:"
                + str(index)
            )

        previous_hash = stored

    return {
        "valid": not errors,
        "event_count": len(
            records
        ),
        "errors": errors,
        "latest_event_hash": (
            previous_hash
        ),
    }


def market_data_event_hash(
    event: Mapping[
        str,
        Any,
    ],
) -> str:
    payload = {
        key: value
        for key, value
        in event.items()
        if key not in {
            "event_id",
            "event_hash",
        }
    }

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


__all__ = [
    "LATEST_MARKET_SNAPSHOT_JSON",
    "MARKET_DATA_AUDIT_JSONL",
    "load_market_snapshot",
    "read_market_data_audit",
    "validate_market_data_audit",
    "write_market_snapshot",
]
