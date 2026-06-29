"""Dashboard IO helpers."""

from pathlib import Path
import json


def write_json(path: Path, data: dict) -> None:
    """Write JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def read_json(path: Path) -> dict:
    """Read JSON file."""
    return json.loads(path.read_text(encoding="utf-8"))