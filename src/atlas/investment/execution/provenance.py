"""Tamper-evident provenance for Atlas paper executions."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


EXECUTION_PROVENANCE_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

EXECUTION_PROVENANCE_JSONL = (
    OUTPUT_DIR
    / "paper_execution_provenance.jsonl"
)

EXECUTION_PROVENANCE_LATEST_JSON = (
    OUTPUT_DIR
    / "paper_execution_provenance_latest.json"
)


EVENT_TYPES = {
    "INTENT_RECORDED",
    "RISK_EVALUATED",
    "ORDER_RECORDED",
    "FILL_RECORDED",
    "ACCOUNT_UPDATED",
    "LIFECYCLE_RECORDED",
    "EXECUTION_RECONCILED",
}

FORBIDDEN_KEYS = {
    "secret",
    "signature",
    "nonce",
    "api_key",
    "api_secret",
    "access_token",
    "refresh_token",
    "private_key",
    "credentials",
}


def build_execution_event(
    *,
    event_type: str,
    execution_id: str,
    intent_id: str = "",
    order_id: str = "",
    fill_id: str = "",
    status: str = "",
    payload: Mapping[str, Any] | None = None,
    previous_event_hash: str = "",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Build one sanitized immutable provenance event."""
    normalized_type = str(
        event_type
    ).strip().upper()

    if normalized_type not in EVENT_TYPES:
        raise ValueError(
            "Unsupported execution provenance event: "
            + normalized_type
        )

    event = {
        "version": (
            EXECUTION_PROVENANCE_VERSION
        ),
        "recorded_at": (
            recorded_at
            or datetime.now(
                UTC
            ).isoformat()
        ),
        "event_type": (
            normalized_type
        ),
        "execution_id": str(
            execution_id
        ),
        "intent_id": str(
            intent_id
        ),
        "order_id": str(
            order_id
        ),
        "fill_id": str(
            fill_id
        ),
        "status": str(
            status
        ),
        "payload": sanitize_value(
            payload or {}
        ),
        "previous_event_hash": str(
            previous_event_hash
        ),
    }

    event["event_hash"] = (
        execution_event_hash(
            event
        )
    )

    event["event_id"] = (
        "EXEC-EVENT-"
        + event["event_hash"][:24]
    )

    return event


def record_execution_events(
    *,
    execution_id: str,
    events: Iterable[
        Mapping[str, Any]
    ],
    ledger_path: Path = (
        EXECUTION_PROVENANCE_JSONL
    ),
    latest_path: Path = (
        EXECUTION_PROVENANCE_LATEST_JSON
    ),
) -> list[dict[str, Any]]:
    """Append one ordered event batch to the global hash chain."""
    existing = read_execution_events(
        ledger_path
    )

    previous_hash = (
        str(
            existing[-1].get(
                "event_hash",
                "",
            )
        )
        if existing
        else ""
    )

    recorded: list[
        dict[str, Any]
    ] = []

    for raw in events:
        event = build_execution_event(
            event_type=str(
                raw.get(
                    "event_type",
                    "",
                )
            ),
            execution_id=(
                execution_id
            ),
            intent_id=str(
                raw.get(
                    "intent_id",
                    "",
                )
            ),
            order_id=str(
                raw.get(
                    "order_id",
                    "",
                )
            ),
            fill_id=str(
                raw.get(
                    "fill_id",
                    "",
                )
            ),
            status=str(
                raw.get(
                    "status",
                    "",
                )
            ),
            payload=raw.get(
                "payload",
                {},
            ),
            previous_event_hash=(
                previous_hash
            ),
        )

        append_execution_event(
            event,
            ledger_path=ledger_path,
        )

        recorded.append(event)
        previous_hash = (
            event["event_hash"]
        )

    update_latest_index(
        new_events=recorded,
        ledger_path=ledger_path,
        latest_path=latest_path,
    )

    return recorded


def append_execution_event(
    event: Mapping[str, Any],
    *,
    ledger_path: Path = (
        EXECUTION_PROVENANCE_JSONL
    ),
) -> None:
    ledger_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with ledger_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                dict(event),
                sort_keys=True,
                default=str,
            )
            + "\n"
        )


def read_execution_events(
    path: Path = (
        EXECUTION_PROVENANCE_JSONL
    ),
) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    result: list[
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
                result.append(
                    payload
                )

    return result


def validate_execution_provenance(
    events: Iterable[
        Mapping[str, Any]
    ] | None = None,
    *,
    ledger_path: Path = (
        EXECUTION_PROVENANCE_JSONL
    ),
) -> dict[str, Any]:
    records = [
        dict(item)
        for item in (
            events
            if events is not None
            else read_execution_events(
                ledger_path
            )
        )
    ]

    errors: list[str] = []
    previous_hash = ""
    event_ids: set[str] = set()

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

        expected_hash = (
            execution_event_hash(
                event
            )
        )

        stored_hash = str(
            event.get(
                "event_hash",
                "",
            )
        )

        if stored_hash != expected_hash:
            errors.append(
                "EVENT_HASH_MISMATCH:"
                + str(index)
            )

        event_id = str(
            event.get(
                "event_id",
                "",
            )
        )

        if event_id in event_ids:
            errors.append(
                "DUPLICATE_EVENT_ID:"
                + event_id
            )

        event_ids.add(
            event_id
        )

        for forbidden in find_forbidden_keys(
            event
        ):
            errors.append(
                "FORBIDDEN_KEY:"
                + str(index)
                + ":"
                + forbidden
            )

        previous_hash = stored_hash

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


def execution_event_hash(
    event: Mapping[str, Any],
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

    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def update_latest_index(
    *,
    new_events: list[
        Mapping[str, Any]
    ],
    ledger_path: Path,
    latest_path: Path,
) -> None:
    all_events = read_execution_events(
        ledger_path
    )

    latest_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    executions: dict[
        str,
        dict[str, Any],
    ] = {}

    for event in all_events:
        execution_id = str(
            event.get(
                "execution_id",
                "",
            )
        )

        if not execution_id:
            continue

        current = executions.setdefault(
            execution_id,
            {
                "execution_id": (
                    execution_id
                ),
                "event_count": 0,
                "latest_event_id": "",
                "latest_event_hash": "",
                "latest_event_type": "",
                "latest_status": "",
                "intent_id": "",
                "order_id": "",
            },
        )

        current["event_count"] += 1
        current["latest_event_id"] = str(
            event.get(
                "event_id",
                "",
            )
        )
        current["latest_event_hash"] = str(
            event.get(
                "event_hash",
                "",
            )
        )
        current["latest_event_type"] = str(
            event.get(
                "event_type",
                "",
            )
        )
        current["latest_status"] = str(
            event.get(
                "status",
                "",
            )
        )

        if event.get(
            "intent_id"
        ):
            current["intent_id"] = str(
                event["intent_id"]
            )

        if event.get(
            "order_id"
        ):
            current["order_id"] = str(
                event["order_id"]
            )

    payload = {
        "version": (
            EXECUTION_PROVENANCE_VERSION
        ),
        "updated_at": (
            datetime.now(
                UTC
            ).isoformat()
        ),
        "event_count": len(
            all_events
        ),
        "execution_count": len(
            executions
        ),
        "latest_event_hash": (
            str(
                all_events[-1].get(
                    "event_hash",
                    "",
                )
            )
            if all_events
            else ""
        ),
        "executions": executions,
    }

    temporary = latest_path.with_suffix(
        latest_path.suffix
        + ".tmp"
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

    temporary.replace(
        latest_path
    )


def sanitize_value(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Mapping,
    ):
        return {
            str(key): sanitize_value(
                item
            )
            for key, item
            in value.items()
            if str(
                key
            ).lower()
            not in FORBIDDEN_KEYS
        }

    if isinstance(
        value,
        (list, tuple),
    ):
        return [
            sanitize_value(
                item
            )
            for item in value
        ]

    if isinstance(
        value,
        (
            str,
            int,
            float,
            bool,
        ),
    ) or value is None:
        return value

    return str(value)


def find_forbidden_keys(
    value: Any,
    *,
    prefix: str = "",
) -> list[str]:
    result: list[str] = []

    if isinstance(
        value,
        Mapping,
    ):
        for key, item in value.items():
            key_text = str(key)

            path = (
                prefix
                + "."
                + key_text
                if prefix
                else key_text
            )

            if (
                key_text.lower()
                in FORBIDDEN_KEYS
            ):
                result.append(path)

            result.extend(
                find_forbidden_keys(
                    item,
                    prefix=path,
                )
            )

    elif isinstance(
        value,
        (list, tuple),
    ):
        for index, item in enumerate(
            value
        ):
            result.extend(
                find_forbidden_keys(
                    item,
                    prefix=(
                        prefix
                        + "["
                        + str(index)
                        + "]"
                    ),
                )
            )

    return result


__all__ = [
    "EVENT_TYPES",
    "EXECUTION_PROVENANCE_JSONL",
    "EXECUTION_PROVENANCE_LATEST_JSON",
    "EXECUTION_PROVENANCE_VERSION",
    "build_execution_event",
    "read_execution_events",
    "record_execution_events",
    "validate_execution_provenance",
]
