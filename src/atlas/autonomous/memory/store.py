
"""Research Memory storage."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.autonomous.memory.memory import create_research_memory


DEFAULT_MEMORY_PATH = Path("output/research_memory.json")


def load_research_memory(path: str | Path = DEFAULT_MEMORY_PATH) -> dict[str, Any]:
    """Load research memory from disk."""
    target = Path(path)

    if not target.exists():
        return create_research_memory()

    try:
        return json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return create_research_memory()


def save_research_memory(
    memory: dict[str, Any],
    path: str | Path = DEFAULT_MEMORY_PATH,
) -> dict[str, Any]:
    """Save research memory to disk."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(memory, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "success": True,
        "path": str(target),
        "experiment_count": len(memory.get("experiments", {})),
        "evidence_count": len(memory.get("evidence", {})),
        "hypothesis_count": len(memory.get("hypotheses", {})),
    }
