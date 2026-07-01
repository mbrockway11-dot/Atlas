"""Profile Interpretation service.

Compatibility layer for profile-level interpretation.

This service delegates to the canonical Profile Report and Narrative
Intelligence services. It does not introduce new symbolic algorithms.
"""

from __future__ import annotations

from typing import Any

from atlas.services.narrative_intelligence_service import (
    build_profile_narrative_payload,
    list_narrative_profiles,
)
from atlas.services.profile_report_service import (
    build_profile_report_payload,
    json_export,
)


def list_profile_interpretation_profiles() -> list[str]:
    """Return profiles available for interpretation."""
    return list_narrative_profiles()


def build_profile_interpretation_payload(profile_key: str) -> dict[str, Any]:
    """Build full profile interpretation payload."""
    profile_report = build_profile_report_payload(profile_key)
    narrative = build_profile_narrative_payload(profile_key)

    return {
        "success": profile_report.get("success", False) and narrative.get("success", False),
        "profile_key": profile_key,
        "errors": collect_errors(profile_report, narrative),
        "warnings": collect_warnings(profile_report, narrative),
        "data": {
            "profile_report": safe_report_summary(profile_report),
            "narrative": narrative.get("data", {}).get("narrative", {}),
        },
        "exports": {
            "profile_report_markdown": profile_report.get("exports", {}).get("markdown", ""),
            "narrative_markdown": narrative.get("exports", {}).get("markdown", ""),
            "profile_report_json": profile_report.get("exports", {}).get("report_json", {}),
            "narrative_json": narrative.get("exports", {}).get("narrative_json", {}),
        },
        "metrics": {
            "profile_report": profile_report.get("metrics", {}),
            "narrative": narrative.get("metrics", {}),
        },
    }


def safe_report_summary(payload: dict[str, Any]) -> dict[str, Any]:
    """Return circular-safe profile report summary."""
    return {
        "success": payload.get("success"),
        "profile_key": payload.get("profile_key"),
        "profile_dir": payload.get("profile_dir"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "report": payload.get("data", {}).get("report", {}),
        "interpretation": payload.get("data", {}).get("interpretation", {}),
    }


def collect_errors(*payloads: dict[str, Any]) -> list[Any]:
    """Collect errors from payloads."""
    errors: list[Any] = []

    for payload in payloads:
        errors.extend(payload.get("errors", []))

    return errors


def collect_warnings(*payloads: dict[str, Any]) -> list[str]:
    """Collect warnings from payloads."""
    warnings: list[str] = []

    for payload in payloads:
        warnings.extend(str(item) for item in payload.get("warnings", []))

    return warnings