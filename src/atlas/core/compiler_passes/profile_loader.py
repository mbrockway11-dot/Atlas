"""Profile-library loading helpers for the CSS compiler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.library.profile_library import LIBRARY_DIR


def safe_load_profile(profile_key: str) -> dict[str, Any]:
    """Load saved profile artifacts from the profile library."""
    profile_dir = Path(LIBRARY_DIR) / profile_key

    candidates = [
        profile_dir / "profile.intake.json",
        profile_dir / "profile.acf.json",
        profile_dir / "profile_summary.json",
        profile_dir / "profile_interpretation.json",
        profile_dir / f"{profile_key}_essence_graph.json",
        profile_dir / "profile.json",
        profile_dir / "atlas_profile.json",
        profile_dir / "profile_intake.json",
        profile_dir / "intake.json",
        profile_dir / "acf.json",
    ]

    merged: dict[str, Any] = {}

    for path in candidates:
        data = read_json(path)
        if data:
            merged[path.stem] = data
            merged[normalize_file_key(path.name)] = data
            merged.update(data)

    return merged


def read_json(path: Path) -> dict[str, Any]:
    """Read JSON if it exists."""
    if not path.exists():
        return {}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}

    return data if isinstance(data, dict) else {}


def normalize_file_key(filename: str) -> str:
    """Normalize file name to a payload key."""
    return filename.replace(".json", "").replace(".", "_").replace("-", "_")