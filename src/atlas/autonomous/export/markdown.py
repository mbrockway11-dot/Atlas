
"""Markdown export helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_markdown(path: str | Path, content: str) -> str:
    """Write markdown file."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content.strip() + "\n", encoding="utf-8")
    return str(target)


def metric_lines(metrics: dict[str, Any]) -> list[str]:
    """Render metrics as markdown bullets."""
    return [f"- {key}: `{value}`" for key, value in metrics.items()]
