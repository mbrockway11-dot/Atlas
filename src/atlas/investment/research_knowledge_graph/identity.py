"""Knowledge Graph deterministic identifiers."""

from __future__ import annotations

import hashlib
import json
import math
from typing import Any


def node_id(
    node_type: str,
    natural_key: str,
) -> str:
    digest = hashlib.sha256(
        (
            f"{str(node_type).upper()}|"
            f"{str(natural_key)}"
        ).encode("utf-8")
    ).hexdigest()[:20]

    return f"NODE-{digest}"


def edge_id(
    source_node_id: str,
    relationship_type: str,
    target_node_id: str,
) -> str:
    payload = {
        "source": source_node_id,
        "relationship": relationship_type,
        "target": target_node_id,
    }

    digest = hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()[:24]

    return f"EDGE-{digest}"


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


def boolean(
    value: Any,
) -> bool:
    if isinstance(value, bool):
        return value

    normalized = text(
        value
    ).strip().lower()

    return normalized in {
        "true",
        "1",
        "yes",
        "y",
    }
