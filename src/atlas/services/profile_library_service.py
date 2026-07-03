from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


def list_profile_library_profiles() -> list[str]:
    """Return saved profile keys available in the profile library."""
    return list_saved_profiles()


def read_json_if_exists(path: Path) -> Any | None:
    """Read JSON from disk if it exists, otherwise return None."""
    if not path.exists():
        return None

    return json.loads(path.read_text(encoding="utf-8"))


def load_profile_library_payload(profile_key: str) -> dict[str, Any]:
    """Load all available profile-library artifacts without crashing on missing files."""
    profile_dir = LIBRARY_DIR / profile_key

    files = {
                "acf": profile_dir / "profile.acf.json",
        "intake": profile_dir / "profile.intake.json",    }

    payload: dict[str, Any] = {
        "profile_key": profile_key,
        "profile_dir": str(profile_dir),
        "exists": profile_dir.exists(),
        "missing": [],
        "available": [],
        "interpretation": None,
        "acf": None,
        "intake": None,
        "research_session": None,
    }

    for key, path in files.items():
        if path.exists():
            payload[key] = read_json_if_exists(path)
            payload["available"].append(path.name)
        else:
            payload["missing"].append(path.name)

    return payload

