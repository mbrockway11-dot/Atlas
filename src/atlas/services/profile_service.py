"""Profile service utilities."""

from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


def list_profile_keys() -> list[str]:
    """Return saved profile keys."""
    return list_saved_profiles()


def profile_dir(profile_key: str) -> Path:
    """Return profile directory path."""
    return LIBRARY_DIR / profile_key


def profile_exists(profile_key: str) -> bool:
    """Return whether a profile exists."""
    return profile_dir(profile_key).exists()


def load_profile_acf(profile_key: str) -> dict[str, Any]:
    """Load profile.acf.json for a saved profile."""
    path = profile_dir(profile_key) / "profile.acf.json"

    if not path.exists():
        raise FileNotFoundError(f"Missing profile.acf.json: {path}")

    return json.loads(path.read_text(encoding="utf-8"))


def resolve_profile_display_name(profile_key: str) -> str:
    """Resolve display name for a profile."""
    try:
        acf = load_profile_acf(profile_key)
    except FileNotFoundError:
        return profile_key

    for key in ["name", "full_name", "display_name"]:
        value = acf.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()

    identity = acf.get("identity")
    if isinstance(identity, dict):
        for key in ["name", "full_name", "display_name"]:
            value = identity.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()

    return profile_key