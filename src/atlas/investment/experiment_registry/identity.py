"""Atlas Experiment Registry canonical identifiers."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def build_experiment_id(
    *,
    experiment_type: str,
    natural_key: str,
) -> str:
    payload = {
        "experiment_type": str(
            experiment_type
        ).upper(),
        "natural_key": str(
            natural_key
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:20]

    return f"EXP-{digest}"


def build_observation_id(
    *,
    experiment_id: str,
    source: str,
    evidence_hash: str,
) -> str:
    payload = (
        f"{experiment_id}|"
        f"{source}|"
        f"{evidence_hash}"
    )

    digest = hashlib.sha256(
        payload.encode("utf-8")
    ).hexdigest()[:24]

    return f"OBS-{digest}"


def hash_payload(
    payload: Any,
) -> str:
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


def first_value(
    row: dict,
    *keys: str,
    default: Any = "",
) -> Any:
    for key in keys:
        value = row.get(key)

        if text(value):
            return value

    return default
