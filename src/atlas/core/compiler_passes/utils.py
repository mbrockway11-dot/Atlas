"""Shared helpers for CSS compiler passes."""

from __future__ import annotations

from typing import Any


def extract_acf(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract ACF data from known profile shapes."""
    candidates = [
        profile_payload.get("profile.acf"),
        profile_payload.get("profile_acf"),
        profile_payload.get("acf"),
        profile_payload.get("atlas_profile"),
        profile_payload.get("data", {}).get("acf")
        if isinstance(profile_payload.get("data"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    if any(
        key in profile_payload
        for key in [
            "analyses",
            "cipher_matrix",
            "essence",
            "identity",
            "identity_graph",
            "identity_persistence",
            "invariant_analysis",
            "planetary_matrix",
        ]
    ):
        return profile_payload

    return {}


def extract_essence_graph(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract saved essence graph data."""
    candidates = [
        profile_payload.get("essence_graph"),
        profile_payload.get("nikola_tesla_essence_graph"),
        profile_payload.get("data", {}).get("essence_graph")
        if isinstance(profile_payload.get("data"), dict)
        else None,
    ]

    for candidate in candidates:
        if isinstance(candidate, dict):
            return candidate

    if "graph" in profile_payload and "signature" in profile_payload:
        return profile_payload

    return {}


def extract_intake(profile_payload: dict[str, Any]) -> dict[str, Any]:
    """Extract intake-like data from known profile shapes."""
    candidates = [
        profile_payload.get("profile.intake"),
        profile_payload.get("profile_intake"),
        profile_payload.get("profile_intake_json"),
        profile_payload.get("intake"),
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

    if any(key in profile_payload for key in ["birth_date", "birth_place", "birth_time", "name"]):
        return profile_payload

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