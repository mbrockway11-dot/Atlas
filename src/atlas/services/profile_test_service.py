"""Profile Test Lab service layer."""

from __future__ import annotations

from typing import Any

from atlas.diagnostics import audit_research_matrix
from atlas.library.profile_library import list_saved_profiles
from atlas.research import build_profile_matrix_rows


def list_profile_test_profiles() -> list[str]:
    """Return profiles available for profile testing."""
    return list_saved_profiles()


def build_profile_test_payload(profile_keys: list[str]) -> dict[str, Any]:
    """Build Profile Test Lab payload behind the service layer."""
    rows: list[dict[str, Any]] = []

    for profile_key in profile_keys:
        try:
            rows.extend(build_profile_matrix_rows(profile_key))
        except Exception as exc:
            rows.append(
                {
                    "profile": profile_key,
                    "error": str(exc),
                }
            )

    diagnostics = audit_research_matrix(rows)

    return {
        "success": True,
        "profile_keys": profile_keys,
        "rows": rows,
        "diagnostics": diagnostics,
        "summary": {
            "profile_count": len(profile_keys),
            "row_count": len(rows),
            "expected_rows": len(profile_keys) * 21,
            "feature_count": len(rows[0]) if rows else 0,
        },
        "warnings": [],
        "errors": [],
    }