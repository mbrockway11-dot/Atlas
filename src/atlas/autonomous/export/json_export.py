
"""JSON export helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def write_json(path: str | Path, payload: dict[str, Any]) -> str:
    """Write JSON file with safe slimming for huge Atlas payloads."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(slim_for_json(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    return str(target)


def slim_for_json(value: Any, *, depth: int = 0) -> Any:
    """Prevent huge nested graph/profile payloads from exhausting memory."""
    if depth > 8:
        return "[truncated: max depth]"

    if isinstance(value, dict):
        blocked = {
            "raw_graph",
            "kamea",
            "path_views",
            "analysis_path",
            "construction_passes",
            "visit_history",
            "visits",
            "train",
            "holdout",
            "raw_signal",
            "payload",
        }

        result = {}
        for key, item in value.items():
            if key in blocked:
                result[key] = "[truncated: large payload]"
            else:
                result[key] = slim_for_json(item, depth=depth + 1)
        return result

    if isinstance(value, list):
        if len(value) > 100:
            return [slim_for_json(item, depth=depth + 1) for item in value[:100]] + [
                f"[truncated: {len(value) - 100} additional item(s)]"
            ]
        return [slim_for_json(item, depth=depth + 1) for item in value]

    return value
