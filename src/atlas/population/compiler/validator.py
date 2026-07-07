
"""Population compiler validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any


LIBRARY_ROOT = Path("output/library/profiles")


def validate_intake(profile_key: str, library_root: str | Path = LIBRARY_ROOT) -> dict[str, Any]:
    intake_path = Path(library_root) / profile_key / "profile.intake.json"

    if not intake_path.exists():
        return {
            "success": False,
            "status": "missing_intake",
            "profile_key": profile_key,
            "error": f"Missing intake: {intake_path}",
        }

    return {
        "success": True,
        "status": "valid_intake",
        "profile_key": profile_key,
        "path": str(intake_path),
    }


def payload_exists(profile_key: str, library_root: str | Path = LIBRARY_ROOT) -> bool:
    return (Path(library_root) / profile_key / "profile.payload.json").exists()
