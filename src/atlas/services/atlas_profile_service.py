"""Service entry point for canonical AtlasProfile payloads."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.intelligence.pipeline import run_intelligence_pipeline
from atlas.intelligence.profile import AtlasProfile
from atlas.services.profile_service import (
    profile_dir,
    profile_exists,
    resolve_profile_display_name,
)

CACHE_DIR = Path("output/cache/atlas_profile")
CACHE_VERSION = "1.0"


def atlas_profile_cache_path(profile_key: str) -> Path:
    """Return cache path for a canonical AtlasProfile payload."""
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


def atlas_profile_cache_is_valid(profile_key: str) -> bool:
    """Return whether AtlasProfile cache is valid."""
    path = atlas_profile_cache_path(profile_key)

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


def load_cached_atlas_profile(profile_key: str) -> dict[str, Any] | None:
    """Load valid cached AtlasProfile payload."""
    if not atlas_profile_cache_is_valid(profile_key):
        return None

    return json.loads(atlas_profile_cache_path(profile_key).read_text(encoding="utf-8"))


def write_cached_atlas_profile(profile_key: str, payload: dict[str, Any]) -> None:
    """Write AtlasProfile payload to cache."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    payload = dict(payload)
    payload["_cache"] = {
        "version": CACHE_VERSION,
        "profile_key": profile_key,
    }

    atlas_profile_cache_path(profile_key).write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def build_base_atlas_profile(profile_key: str) -> AtlasProfile:
    """Build base AtlasProfile without running plugins."""
    if not profile_exists(profile_key):
        raise FileNotFoundError(f"Profile not found: {profile_key}")

    directory = profile_dir(profile_key)

    return AtlasProfile(
        profile_key=profile_key,
        display_name=resolve_profile_display_name(profile_key),
        profile_dir=str(directory),
    )


def build_atlas_profile_model(
    profile_key: str,
    *,
    config: IntelligenceEngineConfig | None = None,
) -> AtlasProfile:
    """Build canonical AtlasProfile model."""
    base = build_base_atlas_profile(profile_key)
    return run_intelligence_pipeline(base, config=config)


def build_atlas_profile(
    profile_key: str,
    *,
    config: IntelligenceEngineConfig | None = None,
    use_cache: bool = True,
    refresh: bool = False,
) -> dict[str, Any]:
    """Build or load canonical AtlasProfile dictionary payload."""
    if use_cache and not refresh:
        cached = load_cached_atlas_profile(profile_key)
        if cached is not None:
            return cached

    payload = build_atlas_profile_model(profile_key, config=config).to_dict()

    if use_cache:
        write_cached_atlas_profile(profile_key, payload)

    return payload