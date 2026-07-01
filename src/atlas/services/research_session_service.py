"""Research session service utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from atlas.research.session import build_research_session
from atlas.services.profile_service import profile_dir


def serialize_research_session(session: Any) -> Any:
    """Convert research session object to JSON-compatible structure when possible."""
    if hasattr(session, "to_dict"):
        return session.to_dict()

    if hasattr(session, "model_dump"):
        return session.model_dump()

    if hasattr(session, "__dict__"):
        return session.__dict__

    return session


def get_research_session(
    profile_key: str,
    *,
    transit_date: str = "2026-06-29",
) -> Any:
    """Build research session for a saved profile key."""
    session = build_research_session(
        profile_dir(profile_key),
        transit_date=transit_date,
    )
    return serialize_research_session(session)


def get_research_session_from_path(
    profile_path: str | Path,
    *,
    transit_date: str = "2026-06-29",
) -> Any:
    """Build research session from a profile directory path."""
    session = build_research_session(
        Path(profile_path),
        transit_date=transit_date,
    )
    return serialize_research_session(session)