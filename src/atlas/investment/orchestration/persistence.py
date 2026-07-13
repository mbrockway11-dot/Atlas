"""Persistent outputs for Atlas autonomous paper orchestration."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping


OUTPUT_DIR = Path(
    "output/investment_orchestration"
)

LATEST_ORCHESTRATION_REPORT_JSON = (
    OUTPUT_DIR
    / "latest_orchestration_report.json"
)

ORCHESTRATION_CHECKPOINT_JSON = (
    OUTPUT_DIR
    / "orchestration_checkpoint.json"
)

ORCHESTRATION_HISTORY_JSONL = (
    OUTPUT_DIR
    / "orchestration_history.jsonl"
)

ORCHESTRATION_PERSISTENCE_VERSION = (
    "1.0.0"
)


def load_orchestration_checkpoint(
    path: Path = (
        ORCHESTRATION_CHECKPOINT_JSON
    ),
) -> dict[str, Any]:
    """Load the most recent orchestration checkpoint."""
    if not path.exists():
        return {
            "version": (
                ORCHESTRATION_PERSISTENCE_VERSION
            ),
            "last_decision_id": "",
            "last_run_id": "",
            "last_status": "",
        }

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
            "ORCHESTRATION_CHECKPOINT_NOT_OBJECT"
        )

    return payload


def write_orchestration_outputs(
    report: Mapping[
        str,
        Any,
    ],
    *,
    report_path: Path = (
        LATEST_ORCHESTRATION_REPORT_JSON
    ),
    checkpoint_path: Path = (
        ORCHESTRATION_CHECKPOINT_JSON
    ),
    history_path: Path = (
        ORCHESTRATION_HISTORY_JSONL
    ),
    write_checkpoint: bool = True,
) -> dict[str, Any]:
    """Persist latest report, checkpoint, and hash-linked history."""
    payload = dict(
        report
    )

    write_json_atomic(
        report_path,
        payload,
    )

    checkpoint = build_checkpoint(
        payload
    )

    if write_checkpoint:
        write_json_atomic(
            checkpoint_path,
            checkpoint,
        )

    history_record = (
        append_orchestration_history(
            payload,
            path=history_path,
        )
    )

    return {
        "report_path": str(
            report_path
        ),
        "checkpoint_path": str(
            checkpoint_path
        ),
        "history_path": str(
            history_path
        ),
        "checkpoint": checkpoint,
        "history_record": (
            history_record
        ),
    }


def build_checkpoint(
    report: Mapping[
        str,
        Any,
    ],
) -> dict[str, Any]:
    """Build the restart checkpoint for one orchestration report."""
    payload = dict(
        report
    )

    return {
        "version": (
            ORCHESTRATION_PERSISTENCE_VERSION
        ),
        "last_decision_id": str(
            payload.get(
                "decision_id",
                "",
            )
        ),
        "last_run_id": str(
            payload.get(
                "run_id",
                "",
            )
        ),
        "last_status": str(
            payload.get(
                "status",
                "",
            )
        ),
        "last_success": bool(
            payload.get(
                "success",
                False,
            )
        ),
        "last_started_at": str(
            payload.get(
                "started_at",
                "",
            )
        ),
        "last_completed_at": str(
            payload.get(
                "completed_at",
                "",
            )
        ),
        "last_counts": dict(
            payload.get(
                "counts",
                {},
            )
            or {}
        ),
        "contract": {
            "restart_safe": True,
            "paper_only": True,
            "live_execution": False,
        },
    }


def append_orchestration_history(
    report: Mapping[
        str,
        Any,
    ],
    *,
    path: Path = (
        ORCHESTRATION_HISTORY_JSONL
    ),
) -> dict[str, Any]:
    """Append one hash-linked orchestration history record."""
    existing = read_orchestration_history(
        path
    )

    previous_hash = (
        str(
            existing[-1].get(
                "record_hash",
                "",
            )
        )
        if existing
        else ""
    )

    record = {
        "ledger_index": (
            len(existing)
            + 1
        ),
        "run_id": str(
            report.get(
                "run_id",
                "",
            )
        ),
        "decision_id": str(
            report.get(
                "decision_id",
                "",
            )
        ),
        "status": str(
            report.get(
                "status",
                "",
            )
        ),
        "success": bool(
            report.get(
                "success",
                False,
            )
        ),
        "started_at": str(
            report.get(
                "started_at",
                "",
            )
        ),
        "completed_at": str(
            report.get(
                "completed_at",
                "",
            )
        ),
        "counts": dict(
            report.get(
                "counts",
                {},
            )
            or {}
        ),
        "previous_record_hash": (
            previous_hash
        ),
    }

    record[
        "record_hash"
    ] = build_record_hash(
        record
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
                record,
                sort_keys=True,
                separators=(",", ":"),
                default=str,
            )
            + "\n"
        )

    return record


def read_orchestration_history(
    path: Path = (
        ORCHESTRATION_HISTORY_JSONL
    ),
) -> list[dict[str, Any]]:
    """Read orchestration history records."""
    if not path.exists():
        return []

    records: list[
        dict[str, Any]
    ] = []

    for line_number, line in enumerate(
        path.read_text(
            encoding="utf-8"
        ).splitlines(),
        start=1,
    ):
        text = line.strip()

        if not text:
            continue

        try:
            payload = json.loads(
                text
            )

        except json.JSONDecodeError as error:
            raise ValueError(
                "ORCHESTRATION_HISTORY_JSON_INVALID:"
                + str(
                    line_number
                )
            ) from error

        if not isinstance(
            payload,
            dict,
        ):
            raise ValueError(
                "ORCHESTRATION_HISTORY_ROW_NOT_OBJECT:"
                + str(
                    line_number
                )
            )

        records.append(
            payload
        )

    return records


def validate_orchestration_history(
    path: Path = (
        ORCHESTRATION_HISTORY_JSONL
    ),
) -> dict[str, Any]:
    """Validate history indexes and record hashes."""
    records = read_orchestration_history(
        path
    )

    errors: list[str] = []

    previous_hash = ""

    for expected_index, record in enumerate(
        records,
        start=1,
    ):
        if int(
            record.get(
                "ledger_index",
                0,
            )
        ) != expected_index:
            errors.append(
                "ORCHESTRATION_HISTORY_INDEX_MISMATCH:"
                + str(
                    expected_index
                )
            )

        if str(
            record.get(
                "previous_record_hash",
                "",
            )
        ) != previous_hash:
            errors.append(
                "ORCHESTRATION_HISTORY_PREVIOUS_HASH_MISMATCH:"
                + str(
                    expected_index
                )
            )

        expected_hash = build_record_hash(
            record
        )

        stored_hash = str(
            record.get(
                "record_hash",
                "",
            )
        )

        if expected_hash != stored_hash:
            errors.append(
                "ORCHESTRATION_HISTORY_HASH_MISMATCH:"
                + str(
                    expected_index
                )
            )

        previous_hash = stored_hash

    return {
        "valid": not errors,
        "record_count": len(
            records
        ),
        "errors": errors,
        "latest_record_hash": (
            previous_hash
        ),
    }


def build_record_hash(
    record: Mapping[
        str,
        Any,
    ],
) -> str:
    payload = {
        key: value
        for key, value
        in record.items()
        if key != "record_hash"
    }

    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()


def write_json_atomic(
    path: Path,
    payload: Mapping[
        str,
        Any,
    ],
) -> None:
    path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = path.with_suffix(
        path.suffix
        + ".tmp"
    )

    temporary.write_text(
        json.dumps(
            dict(payload),
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        path
    )


__all__ = [
    "LATEST_ORCHESTRATION_REPORT_JSON",
    "ORCHESTRATION_CHECKPOINT_JSON",
    "ORCHESTRATION_HISTORY_JSONL",
    "ORCHESTRATION_PERSISTENCE_VERSION",
    "append_orchestration_history",
    "load_orchestration_checkpoint",
    "read_orchestration_history",
    "validate_orchestration_history",
    "write_orchestration_outputs",
]
