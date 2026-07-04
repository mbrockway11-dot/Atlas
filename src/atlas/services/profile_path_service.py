from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_DIR = PROJECT_ROOT / "output" / "library"
PROFILES_DIR = LIBRARY_DIR / "profiles"


def resolve_profile_dir(profile_key: str) -> Path:
    """Resolve a profile directory across legacy and current library layouts."""
    clean_key = profile_key.strip()

    candidates = [
        LIBRARY_DIR / clean_key,
        PROFILES_DIR / clean_key,
    ]

    for candidate in candidates:
        if candidate.exists():
            return candidate

    return LIBRARY_DIR / clean_key


def profile_exists(profile_key: str) -> bool:
    """Return whether a profile exists in any supported location."""
    return resolve_profile_dir(profile_key).exists()


def profile_artifact_path(profile_key: str, artifact_name: str) -> Path:
    """Resolve an artifact path inside a profile directory."""
    return resolve_profile_dir(profile_key) / artifact_name
