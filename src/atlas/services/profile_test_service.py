"""Profile Test Lab service layer.

Dashboard contract:
- Dashboard calls list_profile_test_profiles()
- Dashboard calls build_profile_test_payload(profile_keys)
- Dashboard never imports atlas.research directly
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.diagnostics import audit_research_matrix
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


def list_profile_test_profiles() -> list[str]:
    """Return all saved profile keys."""
    return list_saved_profiles()


def build_profile_test_payload(profile_keys: list[str]) -> dict[str, Any]:
    """Build Profile Test Lab payload from canonical profile artifacts."""
    rows: list[dict[str, Any]] = []
    errors: list[dict[str, str]] = []

    for profile_key in profile_keys:
        profile_rows, profile_errors = build_profile_rows(profile_key)
        rows.extend(profile_rows)
        errors.extend(profile_errors)

    diagnostics = audit_research_matrix(rows)

    return {
        "success": len(errors) == 0,
        "profile_keys": profile_keys,
        "rows": rows,
        "diagnostics": diagnostics,
        "summary": {
            "profile_count": len(profile_keys),
            "row_count": len(rows),
            "expected_min_rows": len(profile_keys),
            "feature_count": len(rows[0]) if rows else 0,
            "error_count": len(errors),
        },
        "warnings": build_warnings(rows, errors),
        "errors": errors,
    }


def build_profile_rows(profile_key: str) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Build normalized diagnostic rows for one profile."""
    profile_dir = LIBRARY_DIR / profile_key
    acf_path = profile_dir / "profile.acf.json"
    intake_path = profile_dir / "profile.intake.json"

    errors: list[dict[str, str]] = []

    if not profile_dir.exists():
        return [], [{"profile": profile_key, "error": f"Missing profile directory: {profile_dir}"}]

    acf = read_json(acf_path)
    intake = read_json(intake_path)

    if acf is None:
        errors.append({"profile": profile_key, "error": f"Missing or invalid {acf_path.name}"})

    if intake is None:
        errors.append({"profile": profile_key, "error": f"Missing or invalid {intake_path.name}"})

    rows: list[dict[str, Any]] = []

    display_name = resolve_display_name(profile_key, acf, intake)

    if isinstance(acf, dict):
        rows.extend(flatten_artifact(profile_key, display_name, "acf", acf))

    if isinstance(intake, dict):
        rows.extend(flatten_artifact(profile_key, display_name, "intake", intake))

    return rows, errors


def flatten_artifact(
    profile_key: str,
    display_name: str,
    artifact: str,
    payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flatten JSON artifact into diagnostic rows."""
    rows: list[dict[str, Any]] = []

    for path, value in walk_json(payload):
        rows.append(
            {
                "profile_key": profile_key,
                "name": display_name,
                "artifact": artifact,
                "metric": path,
                "value": value,
                "value_type": type(value).__name__,
                "is_numeric": isinstance(value, int | float) and not isinstance(value, bool),
            }
        )

    return rows


def walk_json(value: Any, prefix: str = "") -> list[tuple[str, Any]]:
    """Walk JSON-like data and return leaf paths."""
    leaves: list[tuple[str, Any]] = []

    if isinstance(value, dict):
        for key, item in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            leaves.extend(walk_json(item, path))
        return leaves

    if isinstance(value, list):
        for index, item in enumerate(value):
            path = f"{prefix}[{index}]"
            leaves.extend(walk_json(item, path))
        return leaves

    leaves.append((prefix, value))
    return leaves


def read_json(path: Path) -> dict[str, Any] | None:
    """Read JSON object from path."""
    if not path.exists():
        return None

    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None

    if isinstance(value, dict):
        return value

    return None


def resolve_display_name(
    profile_key: str,
    acf: dict[str, Any] | None,
    intake: dict[str, Any] | None,
) -> str:
    """Resolve display name from intake or ACF."""
    if isinstance(intake, dict) and intake.get("name"):
        return str(intake["name"])

    if isinstance(acf, dict) and acf.get("name"):
        return str(acf["name"])

    identity = acf.get("identity") if isinstance(acf, dict) else None
    if isinstance(identity, dict) and identity.get("name"):
        return str(identity["name"])

    return profile_key.replace("_", " ").title()


def build_warnings(
    rows: list[dict[str, Any]],
    errors: list[dict[str, str]],
) -> list[str]:
    """Build human-readable warnings."""
    warnings: list[str] = []

    if not rows:
        warnings.append("No diagnostic rows were produced.")

    if errors:
        warnings.append(f"{len(errors)} profile artifact issue(s) detected.")

    return warnings