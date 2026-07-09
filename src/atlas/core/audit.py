
"""Atlas Core audit log."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

AUDIT_JSONL = Path("output/atlas_core/atlas_core_audit.jsonl")


def append_audit_event(event: dict[str, Any]) -> None:
    AUDIT_JSONL.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_JSONL.open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
