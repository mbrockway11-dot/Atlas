
"""Population compiler checkpointing."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any


DEFAULT_CHECKPOINT_PATH = Path("output/population_compiler/checkpoint.json")


def load_checkpoint(path: str | Path = DEFAULT_CHECKPOINT_PATH) -> dict[str, Any]:
    target = Path(path)
    if not target.exists():
        return create_checkpoint()
    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return create_checkpoint()


def create_checkpoint() -> dict[str, Any]:
    return {
        "success": True,
        "compiled_keys": [],
        "skipped_keys": [],
        "failed": {},
        "updated_at": "",
    }


def save_checkpoint(checkpoint: dict[str, Any], path: str | Path = DEFAULT_CHECKPOINT_PATH) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    checkpoint["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    target.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False), encoding="utf-8")


def mark_compiled(checkpoint: dict[str, Any], profile_key: str) -> dict[str, Any]:
    checkpoint.setdefault("compiled_keys", [])
    if profile_key not in checkpoint["compiled_keys"]:
        checkpoint["compiled_keys"].append(profile_key)
    checkpoint.get("failed", {}).pop(profile_key, None)
    return checkpoint


def mark_skipped(checkpoint: dict[str, Any], profile_key: str) -> dict[str, Any]:
    checkpoint.setdefault("skipped_keys", [])
    if profile_key not in checkpoint["skipped_keys"]:
        checkpoint["skipped_keys"].append(profile_key)
    return checkpoint


def mark_failed(checkpoint: dict[str, Any], profile_key: str, error: dict[str, Any]) -> dict[str, Any]:
    checkpoint.setdefault("failed", {})[profile_key] = error
    return checkpoint
