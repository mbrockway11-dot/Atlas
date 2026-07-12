"""Adaptive Research Prioritizer utilities."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any


def candidate_id(
    natural_key: str,
) -> str:
    digest = hashlib.sha256(
        str(natural_key).encode(
            "utf-8"
        )
    ).hexdigest()[:20]

    return f"RCAND-{digest}"


def evidence_hash(
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


def normalized_tokens(
    value: Any,
) -> set[str]:
    normalized = re.sub(
        r"[^a-z0-9]+",
        " ",
        text(value).lower(),
    )

    return {
        token
        for token in normalized.split()
        if len(token) >= 3
    }


def jaccard_similarity(
    left: Any,
    right: Any,
) -> float:
    left_tokens = normalized_tokens(
        left
    )

    right_tokens = normalized_tokens(
        right
    )

    if (
        not left_tokens
        or not right_tokens
    ):
        return 0.0

    return len(
        left_tokens
        & right_tokens
    ) / len(
        left_tokens
        | right_tokens
    )
