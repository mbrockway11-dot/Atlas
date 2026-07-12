"""Research Program Manager identity and lifecycle utilities."""

from __future__ import annotations

import hashlib
import json
import math
from datetime import UTC, datetime
from typing import Any

from atlas.investment.research_program_manager.config import (
    ALLOWED_TRANSITIONS,
    PROGRAM_STATUSES,
)


def history_id(
    *,
    program_id: str,
    previous_status: str,
    new_status: str,
    reviewer: str,
    recorded_at: str,
) -> str:
    payload = {
        "program_id": program_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "reviewer": reviewer,
        "recorded_at": recorded_at,
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:24]

    return f"RPHIST-{digest}"


def evidence_id(
    *,
    program_id: str,
    evidence_type: str,
    source_key: str,
    payload: Any,
) -> str:
    digest = hashlib.sha256(
        json.dumps(
            {
                "program_id": program_id,
                "evidence_type": evidence_type,
                "source_key": source_key,
                "payload": payload,
            },
            sort_keys=True,
            separators=(",", ":"),
            default=str,
        ).encode("utf-8")
    ).hexdigest()[:24]

    return f"RPEVID-{digest}"


def dependency_id(
    *,
    program_id: str,
    dependency_type: str,
    dependency_key: str,
) -> str:
    digest = hashlib.sha256(
        (
            f"{program_id}|"
            f"{dependency_type}|"
            f"{dependency_key}"
        ).encode("utf-8")
    ).hexdigest()[:24]

    return f"RPDEP-{digest}"


def text(
    value: Any,
) -> str:
    if value is None:
        return ""

    if (
        isinstance(value, float)
        and math.isnan(value)
    ):
        return ""

    return str(value)


def number(
    value: Any,
    *,
    default: float = 0.0,
) -> float:
    try:
        result = float(value)
    except (
        TypeError,
        ValueError,
    ):
        return default

    return (
        result
        if math.isfinite(result)
        else default
    )


def integer(
    value: Any,
    *,
    default: int = 0,
) -> int:
    try:
        return int(float(value))
    except (
        TypeError,
        ValueError,
    ):
        return default


def boolean(
    value: Any,
) -> bool:
    if isinstance(value, bool):
        return value

    return text(value).strip().lower() in {
        "true",
        "1",
        "yes",
        "y",
    }


def utc_now() -> str:
    return datetime.now(
        UTC
    ).isoformat()


def normalize_status(
    value: Any,
) -> str:
    normalized = text(
        value
    ).strip().upper()

    aliases = {
        "APPROVED": "APPROVED_FOR_DESIGN",
        "DESIGNED": "EXPERIMENT_DESIGNED",
        "IN_VALIDATION": "VALIDATING",
        "ACCUMULATING": "EVIDENCE_ACCUMULATING",
        "PROMOTE": "PROMOTED",
        "DEFER": "DEFERRED",
        "REJECT": "REJECTED",
        "ARCHIVE": "ARCHIVED",
    }

    normalized = aliases.get(
        normalized,
        normalized,
    )

    if normalized not in PROGRAM_STATUSES:
        raise ValueError(
            f"Unknown research program status: {normalized}"
        )

    return normalized


def validate_transition(
    previous_status: str,
    new_status: str,
) -> None:
    previous = normalize_status(
        previous_status
    )

    target = normalize_status(
        new_status
    )

    if previous == target:
        return

    allowed = ALLOWED_TRANSITIONS.get(
        previous,
        set(),
    )

    if target not in allowed:
        raise ValueError(
            "Illegal research program transition: "
            f"{previous} -> {target}"
        )
