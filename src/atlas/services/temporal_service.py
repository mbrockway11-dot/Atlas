"""Temporal service utilities."""

from __future__ import annotations

from typing import Any

from atlas.services.research_session_service import get_research_session_from_path


TEMPORAL_KEYS = (
    "temporal",
    "temporal_payload",
    "temporal_intelligence",
    "birth",
    "natal",
    "transits",
    "dasha",
)


def extract_temporal_section(session: Any) -> dict[str, Any]:
    """Extract temporal data from a research session when available."""
    if not isinstance(session, dict):
        return {
            "available": False,
            "reason": "Research session is not dictionary-like.",
            "type": type(session).__name__,
        }

    extracted: dict[str, Any] = {}

    for key in TEMPORAL_KEYS:
        if key in session:
            extracted[key] = session[key]

    identity = session.get("identity")
    if isinstance(identity, dict):
        for key in TEMPORAL_KEYS:
            if key in identity:
                extracted[f"identity.{key}"] = identity[key]

    if extracted:
        extracted["available"] = True
        return extracted

    return {
        "available": False,
        "reason": "No known temporal keys found in research session.",
        "session_keys": sorted(session.keys()),
    }


def get_temporal_section_from_path(
    profile_path: str,
    *,
    transit_date: str = "2026-06-29",
) -> dict[str, Any]:
    """Build temporal section from a profile directory path."""
    session = get_research_session_from_path(
        profile_path,
        transit_date=transit_date,
    )
    return extract_temporal_section(session)