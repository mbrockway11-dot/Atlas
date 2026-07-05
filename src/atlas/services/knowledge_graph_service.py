"""Service wrapper for the Atlas Intelligence Engine.

This layer is the stable dashboard/API entry point.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.intelligence.engine import build_intelligence_payload
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.services.profile_service import profile_dir, profile_exists

CACHE_DIR = Path("output/cache/intelligence")
CACHE_VERSION = "1.0"


def cache_path(profile_key: str) -> Path:
    """Return cache file path for profile intelligence payload."""
    safe_key = profile_key.replace("/", "_").replace("\\", "_")
    return CACHE_DIR / f"{safe_key}.json"


def profile_input_mtime(profile_key: str) -> float:
    """Return newest input modified time for a profile."""
    directory = profile_dir(profile_key)

    if not directory.exists():
        return 0.0

    paths = [
        directory / "profile.acf.json",
        directory / "profile.intake.json",
    ]

    mtimes = [path.stat().st_mtime for path in paths if path.exists()]
    return max(mtimes) if mtimes else 0.0


def cache_is_valid(profile_key: str) -> bool:
    """Return whether cached intelligence payload is valid."""
    path = cache_path(profile_key)

    if not path.exists():
        return False

    try:
        cached = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False

    meta = cached.get("_cache", {})
    if meta.get("version") != CACHE_VERSION:
        return False

    return path.stat().st_mtime >= profile_input_mtime(profile_key)


def load_cached_payload(profile_key: str) -> dict[str, Any] | None:
    """Load cached payload if valid."""
    if not cache_is_valid(profile_key):
        return None

    return json.loads(cache_path(profile_key).read_text(encoding="utf-8"))


def write_cached_payload(profile_key: str, payload: dict[str, Any]) -> None:
    """Write intelligence payload to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    payload = dict(payload)
    payload["_cache"] = {
        "version": CACHE_VERSION,
        "profile_key": profile_key,
    }

    cache_path(profile_key).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def get_intelligence_payload(
    profile_key: str,
    config: IntelligenceEngineConfig | None = None,
    *,
    use_cache: bool = True,
    refresh: bool = False,
) -> dict[str, Any]:
    """Return intelligence payload for a profile key."""
    if not profile_exists(profile_key):
        raise FileNotFoundError(f"Profile not found: {profile_key}")

    if use_cache and not refresh:
        cached = load_cached_payload(profile_key)
        if cached is not None:
            return cached

    payload = build_intelligence_payload(profile_dir(profile_key), config=config)

    if use_cache:
        write_cached_payload(profile_key, payload)

    return payload
