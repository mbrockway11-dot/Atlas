
"""Service layer for Discovery Engine."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.discovery import build_discovery_report
from atlas.library.profile_library import list_saved_profiles


def list_discovery_profiles() -> list[str]:
    """List saved profiles available for discovery scans."""
    return list_saved_profiles()


def build_discovery_records(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    """Compile profiles into discovery-ready records."""
    selected = profile_keys or list_saved_profiles()

    if limit is not None:
        selected = selected[:limit]

    records = []

    for key in selected:
        payload = compile_canonical_profile(key, force=force)

        if payload.get("success"):
            records.append(payload)

    return records


def build_discovery_payload(
    profile_keys: list[str] | None = None,
    *,
    limit: int | None = None,
    force: bool = False,
    extra_questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build service-backed Discovery Engine payload."""
    records = build_discovery_records(
        profile_keys,
        limit=limit,
        force=force,
    )

    report = build_discovery_report(
        records,
        extra_questions=extra_questions,
    )

    return {
        "success": True,
        "record_count": len(records),
        "profile_keys": [record.get("profile_key") for record in records],
        "records": records,
        "discovery": report,
        "summary": report.get("summary", ""),
        "hypotheses": report.get("hypotheses", []),
        "ranked_evidence": report.get("ranked_evidence", []),
        "correlation_scans": report.get("correlation_scans", []),
    }
