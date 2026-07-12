"""Research Experiment Execution identities and utilities."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def stable_id(
    prefix: str,
    payload: Any,
    *,
    length: int = 20,
) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=str,
    ).encode("utf-8")

    digest = hashlib.sha256(
        encoded
    ).hexdigest()[:length]

    return f"{prefix}-{digest}"


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


def clamp(
    value: float,
    minimum: float = 0.0,
    maximum: float = 1.0,
) -> float:
    return max(
        minimum,
        min(
            maximum,
            number(value),
        ),
    )
