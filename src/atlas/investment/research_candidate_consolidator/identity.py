"""Research Candidate Consolidator identity and parsing."""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any

from atlas.investment.research_candidate_consolidator.config import (
    CONDITION_VALUES,
    FEATURE_FAMILIES,
)


def program_id(
    *,
    engine_id: str,
    theme: str,
    member_ids: list[str],
) -> str:
    payload = {
        "engine_id": engine_id,
        "theme": theme,
        "member_ids": sorted(
            member_ids
        ),
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:20]

    return f"RPROG-{digest}"


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


def normalized_tokens(
    value: Any,
) -> set[str]:
    normalized = re.sub(
        r"[^a-z0-9_]+",
        " ",
        text(value).lower(),
    )

    return {
        token
        for token in normalized.split()
        if len(token) >= 2
    }


def extract_feature_name(
    title: str,
) -> str:
    pattern = re.search(
        r"when\s+([a-zA-Z0-9_]+)\s+is\s+",
        text(title),
        flags=re.IGNORECASE,
    )

    if pattern:
        return pattern.group(1).lower()

    return ""


def extract_condition_value(
    title: str,
) -> str:
    pattern = re.search(
        r"\sis\s+([a-zA-Z0-9_]+)[\.\s]*$",
        text(title).strip(),
        flags=re.IGNORECASE,
    )

    if not pattern:
        return ""

    value = pattern.group(1).upper()

    return (
        value
        if value in CONDITION_VALUES
        else value
    )


def feature_family(
    feature_name: str,
    title: str = "",
) -> str:
    searchable = (
        f"{feature_name} {title}"
    ).lower()

    for family, aliases in (
        FEATURE_FAMILIES.items()
    ):
        if any(
            alias in searchable
            for alias in aliases
        ):
            return family

    return "other"


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
