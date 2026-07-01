"""Functional Role Calibration service layer."""

from __future__ import annotations

import json
from typing import Any

from atlas.classification.role_calibration import calibrate_functional_roles_v2
from atlas.classification.role_diagnostics import audit_functional_roles_v2
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.research import build_profile_matrix_rows


def list_role_calibration_profiles() -> list[str]:
    """Return available profile keys."""
    return list_saved_profiles()


def load_role_calibration_matrix_rows(profile_keys: list[str]) -> list[dict[str, Any]]:
    """Load matrix rows for selected profiles."""
    rows: list[dict[str, Any]] = []

    for profile_key in profile_keys:
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            rows.append(
                {
                    "profile": profile_key,
                    "error": f"Missing profile.acf.json: {acf_path}",
                }
            )
            continue

        try:
            acf = json.loads(acf_path.read_text(encoding="utf-8"))
            rows.extend(build_profile_matrix_rows(acf))
        except Exception as exc:
            rows.append(
                {
                    "profile": profile_key,
                    "error": str(exc),
                }
            )

    return rows


def build_role_calibration_payload(profile_keys: list[str]) -> dict[str, Any]:
    """Build role calibration and diagnostics payload."""
    rows = load_role_calibration_matrix_rows(profile_keys)

    valid_rows = [row for row in rows if "error" not in row]
    errors = [row for row in rows if "error" in row]

    if not valid_rows:
        return {
            "success": False,
            "profile_keys": profile_keys,
            "rows": rows,
            "calibration": {},
            "diagnostics": {},
            "errors": errors,
            "warnings": ["No valid matrix rows available."],
            "metrics": {
                "profile_count": len(profile_keys),
                "row_count": len(rows),
                "valid_row_count": 0,
                "error_count": len(errors),
            },
        }

    calibration = calibrate_functional_roles_v2(valid_rows)
    diagnostics = audit_functional_roles_v2(valid_rows)

    return {
        "success": True,
        "profile_keys": profile_keys,
        "rows": valid_rows,
        "calibration": calibration,
        "diagnostics": diagnostics,
        "errors": errors,
        "warnings": [],
        "metrics": {
            "profile_count": len(profile_keys),
            "row_count": len(rows),
            "valid_row_count": len(valid_rows),
            "error_count": len(errors),
        },
    }