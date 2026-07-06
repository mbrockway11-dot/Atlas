
"""Service layer for Systems Engineering Report dashboard."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.library.profile_library import list_saved_profiles
from atlas.systems_report import build_systems_engineering_report


def list_systems_report_profiles() -> list[str]:
    """List available profiles for Systems Engineering Report."""
    return list_saved_profiles()


def build_systems_report_payload(profile_key: str, *, force: bool = False) -> dict[str, Any]:
    """Build Systems Engineering Report payload."""
    payload = compile_canonical_profile(profile_key, force=force)

    if not payload.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": payload.get("errors", []),
            "payload": payload,
            "report": {},
        }

    report = payload.get("systems_report") or build_systems_engineering_report(payload)

    return {
        "success": True,
        "profile_key": profile_key,
        "errors": [],
        "payload": payload,
        "report": report,
    }
