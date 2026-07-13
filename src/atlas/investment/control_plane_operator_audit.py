"""Tamper-evident operator audit trail for Atlas Studio.

The ledger records operator intent and control-plane outcomes. It never stores
approval secrets, HMAC signatures, nonces, environment variables, or raw
authorization records.

Each JSONL event contains the hash of the previous event, forming a simple
append-only integrity chain.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable, Mapping


OPERATOR_AUDIT_VERSION = "1.0.0"

OUTPUT_DIR = Path(
    "output/atlas_control_plane"
)

OPERATOR_AUDIT_JSONL = (
    OUTPUT_DIR
    / "operator_audit.jsonl"
)

OPERATOR_AUDIT_LATEST_JSON = (
    OUTPUT_DIR
    / "operator_audit_latest.json"
)


ALLOWED_ACTIONS = {
    "APPROVAL_PREFLIGHT_VIEWED",
    "APPROVAL_ATTEMPTED",
    "APPROVAL_REJECTED",
    "APPROVAL_CREATED",
    "DISPATCH_PREFLIGHT_VIEWED",
    "DISPATCH_ATTEMPTED",
    "DISPATCH_REJECTED",
    "DISPATCH_COMPLETED",
    "RECONCILIATION_ATTEMPTED",
    "RECONCILIATION_REJECTED",
    "RECONCILIATION_COMPLETED",
}

ALLOWED_RESULTS = {
    "OBSERVED",
    "REQUESTED",
    "SUCCEEDED",
    "REJECTED",
    "FAILED",
}

FORBIDDEN_KEYS = {
    "secret",
    "signature",
    "nonce",
    "approval_secret",
    "atlas_approval_secret",
    "environment",
    "env",
}


def build_operator_event(
    *,
    action: str,
    result: str,
    operator_id: str,
    session_id: str,
    reason: str = "",
    plan_hash: str = "",
    approval_id: str = "",
    dispatch_run_id: str = "",
    job_ids: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
    previous_event_hash: str = "",
    recorded_at: str | None = None,
) -> dict[str, Any]:
    """Build one sanitized operator audit event."""
    normalized_action = str(
        action
    ).strip().upper()

    normalized_result = str(
        result
    ).strip().upper()

    if normalized_action not in ALLOWED_ACTIONS:
        raise ValueError(
            "Unsupported operator audit action: "
            f"{normalized_action}"
        )

    if normalized_result not in ALLOWED_RESULTS:
        raise ValueError(
            "Unsupported operator audit result: "
            f"{normalized_result}"
        )

    safe_metadata = sanitize_metadata(
        metadata or {}
    )

    event = {
        "version": (
            OPERATOR_AUDIT_VERSION
        ),
        "recorded_at": (
            recorded_at
            or datetime.now(UTC).isoformat()
        ),
        "action": normalized_action,
        "result": normalized_result,
        "operator_id": str(
            operator_id
        ).strip(),
        "session_id": str(
            session_id
        ).strip(),
        "reason": str(reason),
        "plan_hash": str(
            plan_hash
        ),
        "approval_id": str(
            approval_id
        ),
        "dispatch_run_id": str(
            dispatch_run_id
        ),
        "job_ids": ordered_unique(
            str(value)
            for value in job_ids
        ),
        "metadata": safe_metadata,
        "previous_event_hash": str(
            previous_event_hash
        ),
    }

    event["event_hash"] = (
        operator_event_hash(
            event
        )
    )

    event["event_id"] = (
        "OPAUDIT-"
        + event["event_hash"][:24]
    )

    return event


def record_operator_event(
    *,
    action: str,
    result: str,
    operator_id: str,
    session_id: str,
    reason: str = "",
    plan_hash: str = "",
    approval_id: str = "",
    dispatch_run_id: str = "",
    job_ids: Iterable[str] = (),
    metadata: Mapping[str, Any] | None = None,
    ledger_path: Path = (
        OPERATOR_AUDIT_JSONL
    ),
    latest_path: Path = (
        OPERATOR_AUDIT_LATEST_JSON
    ),
) -> dict[str, Any]:
    """Append one chained operator audit event and update the latest index."""
    events = read_operator_events(
        ledger_path
    )

    previous_hash = (
        str(
            events[-1].get(
                "event_hash",
                "",
            )
        )
        if events
        else ""
    )

    event = build_operator_event(
        action=action,
        result=result,
        operator_id=operator_id,
        session_id=session_id,
        reason=reason,
        plan_hash=plan_hash,
        approval_id=approval_id,
        dispatch_run_id=(
            dispatch_run_id
        ),
        job_ids=job_ids,
        metadata=metadata,
        previous_event_hash=(
            previous_hash
        ),
    )

    append_operator_event(
        event,
        ledger_path=ledger_path,
    )

    latest = load_latest_operator_audit(
        latest_path
    )

    action_counts = dict(
        latest.get(
            "action_counts",
            {},
        )
        or {}
    )

    result_counts = dict(
        latest.get(
            "result_counts",
            {},
        )
        or {}
    )

    action_counts[
        event["action"]
    ] = int(
        action_counts.get(
            event["action"],
            0,
        )
    ) + 1

    result_counts[
        event["result"]
    ] = int(
        result_counts.get(
            event["result"],
            0,
        )
    ) + 1

    sessions = set(
        str(value)
        for value in latest.get(
            "session_ids",
            [],
        )
        or []
    )

    if event["session_id"]:
        sessions.add(
            event["session_id"]
        )

    operators = set(
        str(value)
        for value in latest.get(
            "operator_ids",
            [],
        )
        or []
    )

    if event["operator_id"]:
        operators.add(
            event["operator_id"]
        )

    next_latest = {
        "version": (
            OPERATOR_AUDIT_VERSION
        ),
        "updated_at": (
            event["recorded_at"]
        ),
        "event_count": int(
            latest.get(
                "event_count",
                0,
            )
        ) + 1,
        "latest_event_id": (
            event["event_id"]
        ),
        "latest_event_hash": (
            event["event_hash"]
        ),
        "action_counts": (
            action_counts
        ),
        "result_counts": (
            result_counts
        ),
        "session_ids": sorted(
            sessions
        ),
        "operator_ids": sorted(
            operators
        ),
    }

    write_latest_operator_audit(
        next_latest,
        latest_path,
    )

    return event


def append_operator_event(
    event: Mapping[str, Any],
    *,
    ledger_path: Path = (
        OPERATOR_AUDIT_JSONL
    ),
) -> None:
    """Append one event unless its event ID already exists."""
    ledger_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    existing_ids = {
        str(
            item.get(
                "event_id",
                "",
            )
        )
        for item in read_operator_events(
            ledger_path
        )
    }

    event_id = str(
        event.get(
            "event_id",
            "",
        )
    )

    if event_id in existing_ids:
        return

    with ledger_path.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                dict(event),
                sort_keys=True,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )


def read_operator_events(
    path: Path = OPERATOR_AUDIT_JSONL,
) -> list[dict[str, Any]]:
    """Read valid operator audit events."""
    if not path.exists():
        return []

    events: list[
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

            if isinstance(payload, dict):
                events.append(payload)

    return events


def validate_operator_audit_chain(
    events: Iterable[
        Mapping[str, Any]
    ] | None = None,
    *,
    ledger_path: Path = (
        OPERATOR_AUDIT_JSONL
    ),
) -> dict[str, Any]:
    """Validate event hashes and previous-event chain continuity."""
    records = [
        dict(event)
        for event in (
            events
            if events is not None
            else read_operator_events(
                ledger_path
            )
        )
    ]

    errors: list[str] = []
    previous_hash = ""

    for index, event in enumerate(
        records,
        start=1,
    ):
        stored_previous = str(
            event.get(
                "previous_event_hash",
                "",
            )
        )

        if stored_previous != previous_hash:
            errors.append(
                "PREVIOUS_HASH_MISMATCH:"
                f"{index}"
            )

        expected_hash = (
            operator_event_hash(
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
                f"{index}"
            )

        expected_id = (
            "OPAUDIT-"
            + stored_hash[:24]
        )

        if str(
            event.get(
                "event_id",
                "",
            )
        ) != expected_id:
            errors.append(
                "EVENT_ID_MISMATCH:"
                f"{index}"
            )

        forbidden = find_forbidden_keys(
            event
        )

        for key in forbidden:
            errors.append(
                "FORBIDDEN_KEY:"
                f"{index}:{key}"
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


def operator_event_hash(
    event: Mapping[str, Any],
) -> str:
    """Hash an event excluding its derived event ID and event hash."""
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
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    return hashlib.sha256(
        encoded
    ).hexdigest()


def sanitize_metadata(
    metadata: Mapping[str, Any],
) -> dict[str, Any]:
    """Recursively remove forbidden and sensitive metadata fields."""
    result: dict[str, Any] = {}

    for key, value in metadata.items():
        normalized_key = str(
            key
        ).strip()

        if normalized_key.lower() in (
            FORBIDDEN_KEYS
        ):
            continue

        result[
            normalized_key
        ] = sanitize_value(
            value
        )

    return result


def sanitize_value(
    value: Any,
) -> Any:
    if isinstance(
        value,
        Mapping,
    ):
        return sanitize_metadata(
            value
        )

    if isinstance(
        value,
        (list, tuple, set),
    ):
        return [
            sanitize_value(item)
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
    findings: list[str] = []

    if isinstance(
        value,
        Mapping,
    ):
        for key, child in value.items():
            key_text = str(key)
            path = (
                f"{prefix}.{key_text}"
                if prefix
                else key_text
            )

            if key_text.lower() in (
                FORBIDDEN_KEYS
            ):
                findings.append(path)

            findings.extend(
                find_forbidden_keys(
                    child,
                    prefix=path,
                )
            )

    elif isinstance(
        value,
        (list, tuple),
    ):
        for index, child in enumerate(
            value
        ):
            path = (
                f"{prefix}[{index}]"
            )

            findings.extend(
                find_forbidden_keys(
                    child,
                    prefix=path,
                )
            )

    return findings


def load_latest_operator_audit(
    path: Path = (
        OPERATOR_AUDIT_LATEST_JSON
    ),
) -> dict[str, Any]:
    if not path.exists():
        return empty_latest_state()

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        OSError,
        json.JSONDecodeError,
    ):
        return empty_latest_state()

    return (
        payload
        if isinstance(payload, dict)
        else empty_latest_state()
    )


def write_latest_operator_audit(
    state: Mapping[str, Any],
    path: Path = (
        OPERATOR_AUDIT_LATEST_JSON
    ),
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(state),
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(path)


def empty_latest_state() -> dict[str, Any]:
    return {
        "version": (
            OPERATOR_AUDIT_VERSION
        ),
        "updated_at": "",
        "event_count": 0,
        "latest_event_id": "",
        "latest_event_hash": "",
        "action_counts": {},
        "result_counts": {},
        "session_ids": [],
        "operator_ids": [],
    }


def ordered_unique(
    values: Iterable[str],
) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        text = str(value)

        if not text or text in seen:
            continue

        seen.add(text)
        result.append(text)

    return result


__all__ = [
    "ALLOWED_ACTIONS",
    "ALLOWED_RESULTS",
    "OPERATOR_AUDIT_JSONL",
    "OPERATOR_AUDIT_LATEST_JSON",
    "OPERATOR_AUDIT_VERSION",
    "append_operator_event",
    "build_operator_event",
    "load_latest_operator_audit",
    "operator_event_hash",
    "read_operator_events",
    "record_operator_event",
    "sanitize_metadata",
    "validate_operator_audit_chain",
]
