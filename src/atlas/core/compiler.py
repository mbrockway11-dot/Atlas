"""Atlas Core Compiler."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.core.canonical_structural_signature import (
    CanonicalStructuralSignature,
    IdentityLayer,
    TemporalLayer,
)
from atlas.library.profile_library import LIBRARY_DIR


CORE_COMPILER_VERSION = "1.1"


def compile_profile(profile_key: str) -> CanonicalStructuralSignature:
    """Compile one profile into a CanonicalStructuralSignature."""
    profile_payload = safe_load_profile(profile_key)

    identity = build_identity_layer(
        profile_key=profile_key,
        profile_payload=profile_payload,
    )
    temporal = build_temporal_layer(profile_payload=profile_payload)

    return CanonicalStructuralSignature(
        identity=identity,
        temporal=temporal,
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
            "has_temporal": has_temporal_data(css.temporal),
            "has_natal": bool(css.temporal.natal),
            "has_transits": bool(css.temporal.transits),
            "has_dasha": bool(css.temporal.dasha),
            "has_calibration": bool(css.temporal.calibration),
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
        or profile_payload.get("display_name")
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


def build_temporal_layer(*, profile_payload: dict[str, Any]) -> TemporalLayer:
    """Build CSS temporal layer from saved profile payload."""
    temporal = extract_temporal(profile_payload)

    birth = {
        "birth_date": profile_payload.get("birth_date"),
        "birth_time": profile_payload.get("birth_time"),
        "birth_place": profile_payload.get("birth_place"),
        "birth_location": profile_payload.get("birth_location"),
    }
    birth = {
        key: value
        for key, value in birth.items()
        if value is not None
    }

    planetary_matrix = first_dict(
        profile_payload.get("planetary_matrix"),
        profile_payload.get("profile.acf", {}).get("planetary_matrix")
        if isinstance(profile_payload.get("profile.acf"), dict)
        else None,
        profile_payload.get("profile_acf", {}).get("planetary_matrix")
        if isinstance(profile_payload.get("profile_acf"), dict)
        else None,
    )

    natal = first_dict(
        temporal.get("natal"),
        temporal.get("natal_chart"),
        profile_payload.get("natal"),
        profile_payload.get("natal_chart"),
    )

    if birth or planetary_matrix:
        natal = {
            **natal,
            "birth": birth,
            "planetary_matrix": planetary_matrix,
            "temporal_status": "seed_from_saved_profile",
        }

    transits = first_dict(
        temporal.get("transits"),
        temporal.get("transit"),
        profile_payload.get("transits"),
        profile_payload.get("transit"),
    )

    dasha = first_dict(
        temporal.get("dasha"),
        temporal.get("vimshottari_dasha"),
        temporal.get("dashas"),
        profile_payload.get("dasha"),
        profile_payload.get("vimshottari_dasha"),
        profile_payload.get("dashas"),
    )

    calibration = first_dict(
        temporal.get("calibration"),
        profile_payload.get("calibration"),
    )

    return TemporalLayer(
        natal=natal,
        transits=transits,
        dasha=dasha,
        calibration=calibration,
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
        profile_payload.get("profile.intake"),
        profile_payload.get("profile_intake_json"),
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


def extract_temporal(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract temporal-like data from known profile shapes."""
    candidates = [
        profile_payload.get("temporal"),
        profile_payload.get("temporal_data"),
        profile_payload.get("profile_temporal"),
        profile_payload.get("vedic"),
        profile_payload.get("astrology"),
        profile_payload.get("data", {}).get("temporal")
        if isinstance(profile_payload.get("data"), dict)
        else None,
        profile_payload.get("metadata", {}).get("temporal")
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
        or intake.get("birth_place")
        or birth.get("location")
        or birth.get("place")
        or birth.get("birth_location")
        or birth.get("birth_place")
        or profile_payload.get("birth_location")
        or profile_payload.get("birth_place")
    )

    return {
        "birth_date": stringify_or_none(birth_date),
        "birth_time": stringify_or_none(birth_time),
        "birth_location": stringify_or_none(birth_location),
    }


def first_dict(*values: Any) -> dict[str, Any]:
    """Return first dictionary from values."""
    for value in values:
        if isinstance(value, dict):
            return value

    return {}


def has_temporal_data(temporal: TemporalLayer) -> bool:
    """Return whether temporal layer has any data."""
    return any(
        [
            bool(temporal.natal),
            bool(temporal.transits),
            bool(temporal.dasha),
            bool(temporal.calibration),
        ]
    )


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