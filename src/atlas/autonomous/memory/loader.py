
"""Research Memory loader helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.autonomous.memory.store import load_research_memory, save_research_memory


def ensure_research_memory(path: str | Path | None = None) -> dict[str, Any]:
    """Load or create research memory."""
    if path is None:
        return load_research_memory()

    return load_research_memory(path)


def persist_research_memory(memory: dict[str, Any], path: str | Path | None = None) -> dict[str, Any]:
    """Persist research memory."""
    if path is None:
        return save_research_memory(memory)

    return save_research_memory(memory, path)
