"""Atlas Core Compiler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.core.canonical_structural_signature import (
    CanonicalStructuralSignature,
    IdentityLayer,
)
from atlas.library.profile_library import LIBRARY_DIR


CORE_COMPILER_VERSION = "1.0"


def compile_profile(profile_key: str) -> CanonicalStructuralSignature:
    """Compile one profile into a CanonicalStructuralSignature."""
    profile_payload = safe_load_profile(profile_key)

    identity = build_identity_layer(
        profile_key=profile_key,
        profile_payload=profile_payload,
    )

    return CanonicalStructuralSignature(
        identity=identity,
        metadata={
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
            "profile_loaded": bool(profile_payload),
        },
    )


def compile_profile_payload(profile_key: str) -> dict[str, Any]:
    """Compile one profile and return a serializable payload."""
    css = compile_profile(profile_key)

    return {
        "success": css.identity is not None,
        "version": CORE_COMPILER_VERSION,
        "profile_key": profile_key,
        "errors": [],
        "warnings": [],
        "data": {
            "canonical_structural_signature": css.to_dict(),
        },
        "metrics": {
            "has_identity": css.identity is not None,
            "has_birth_date": bool(css.identity and css.identity.birth_date),
            "has_birth_time": bool(css.identity and css.identity.birth_time),
            "has_birth_location": bool(css.identity and css.identity.birth_location),
        },
    }


def build_identity_layer(
    *,
    profile_key: str,
    profile_payload: dict[str, Any],
) -> IdentityLayer:
    """Build CSS identity layer from saved profile data."""
    intake = extract_intake(profile_payload)

    canonical_name = (
        intake.get("name")
        or intake.get("canonical_name")
        or profile_payload.get("name")
        or profile_payload.get("canonical_name")
        or profile_key.replace("_", " ").title()
    )

    aliases = normalize_aliases(
        intake.get("aliases")
        or profile_payload.get("aliases")
        or []
    )

    birth = extract_birth(intake=intake, profile_payload=profile_payload)

    return IdentityLayer(
        profile_key=profile_key,
        canonical_name=str(canonical_name),
        aliases=aliases,
        birth_date=birth.get("birth_date"),
        birth_time=birth.get("birth_time"),
        birth_location=birth.get("birth_location"),
        metadata={
            "identity_source": "profile_library",
            "has_profile_payload": bool(profile_payload),
            "has_intake": bool(intake),
        },
    )


def safe_load_profile(profile_key: str) -> dict[str, Any]:
    """Load a saved profile from the profile library."""
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
            if isinstance(data, dict):
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

    if isinstance(data, dict):
        return data

    return {}


def extract_intake(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract intake-like data from known profile shapes."""
    candidates = [
        profile_payload.get("intake"),
        profile_payload.get("profile_intake"),
        profile_payload.get("data", {}).get("intake")
        if isinstance(profile_payload.get("data"), dict)
        else None,
        profile_payload.get("metadata", {}).get("intake")
        if isinstance(profile_payload.get("metadata"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    return {}


def extract_birth(
    *,
    intake: dict[str, Any],
    profile_payload: dict[str, Any],
) -> dict[str, str | None]:
    """Extract birth fields from intake/profile payload."""
    birth = intake.get("birth")
    if not isinstance(birth, dict):
        birth = profile_payload.get("birth")

    if not isinstance(birth, dict):
        birth = {}

    birth_date = (
        intake.get("birth_date")
        or birth.get("date")
        or birth.get("birth_date")
        or profile_payload.get("birth_date")
    )

    birth_time = (
        intake.get("birth_time")
        or birth.get("time")
        or birth.get("birth_time")
        or profile_payload.get("birth_time")
    )

    birth_location = (
        intake.get("birth_location")
        or birth.get("location")
        or birth.get("birth_location")
        or profile_payload.get("birth_location")
    )

    return {
        "birth_date": stringify_or_none(birth_date),
        "birth_time": stringify_or_none(birth_time),
        "birth_location": stringify_or_none(birth_location),
    }


def normalize_aliases(value: Any) -> list[str]:
    """Normalize aliases to a list of strings."""
    if value is None:
        return []

    if isinstance(value, str):
        return [value]

    if isinstance(value, list | tuple):
        return [str(item) for item in value if item]

    return []


def stringify_or_none(value: Any) -> str | None:
    """Convert value to string or None."""
    if value is None:
        return None

    text = str(value).strip()
    return text or None