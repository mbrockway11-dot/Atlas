"""Person intake service.

Creates a new Atlas profile directory from user-entered identity and birth data.
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PERSON_INTAKE_SERVICE_VERSION = "1.0"

PROJECT_ROOT = Path(__file__).resolve().parents[3]
LIBRARY_DIR = PROJECT_ROOT / "output" / "library"


def create_person_profile(
    *,
    full_name: str,
    birth_date: str = "",
    birth_time: str = "",
    birth_place: str = "",
    death_date: str = "",
    death_place: str = "",
    major_events: list[dict[str, Any]] | None = None,
    notes: str = "",
    overwrite: bool = False,
) -> dict[str, Any]:
    """Create a new person profile intake folder."""
    clean_name = full_name.strip()

    if not clean_name:
        return failure_payload("Full name is required.")

    profile_key = slugify(clean_name)
    profile_dir = LIBRARY_DIR / profile_key
    intake_path = profile_dir / "profile.intake.json"

    if profile_dir.exists() and intake_path.exists() and not overwrite:
        return {
            "success": False,
            "version": PERSON_INTAKE_SERVICE_VERSION,
            "profile_key": profile_key,
            "profile_dir": str(profile_dir),
            "created_files": [],
            "warnings": [
                "Profile already exists. Use overwrite=True to replace profile.intake.json."
            ],
            "errors": [],
        }

    profile_dir.mkdir(parents=True, exist_ok=True)

    intake = build_intake_payload(
        profile_key=profile_key,
        full_name=clean_name,
        birth_date=birth_date,
        birth_time=birth_time,
        birth_place=birth_place,
        death_date=death_date,
        death_place=death_place,
        major_events=major_events or [],
        notes=notes,
    )

    write_json(intake_path, intake)

    return {
        "success": True,
        "version": PERSON_INTAKE_SERVICE_VERSION,
        "profile_key": profile_key,
        "profile_dir": str(profile_dir),
        "created_files": [str(intake_path)],
        "warnings": build_warnings(intake),
        "errors": [],
        "next_steps": [
            "Run the Atlas profile compiler for this profile.",
            "Generate profile.acf.json.",
            "Refresh the profile library index.",
        ],
        "intake": intake,
    }


def build_intake_payload(
    *,
    profile_key: str,
    full_name: str,
    birth_date: str,
    birth_time: str,
    birth_place: str,
    death_date: str,
    death_place: str,
    major_events: list[dict[str, Any]],
    notes: str,
) -> dict[str, Any]:
    """Build profile intake JSON."""
    return {
        "version": PERSON_INTAKE_SERVICE_VERSION,
        "profile_key": profile_key,
        "identity": {
            "full_name": full_name,
            "display_name": full_name,
            "profile_key": profile_key,
        },
        "birth": {
            "date": birth_date.strip(),
            "time": birth_time.strip(),
            "place": birth_place.strip(),
            "date_status": "provided" if birth_date.strip() else "missing",
            "time_status": "provided" if birth_time.strip() else "missing",
            "place_status": "provided" if birth_place.strip() else "missing",
        },
        "death": {
            "date": death_date.strip(),
            "place": death_place.strip(),
            "date_status": "provided" if death_date.strip() else "open_or_missing",
            "place_status": "provided" if death_place.strip() else "missing",
            "lifecycle_status": (
                "closed_historical_lifecycle"
                if death_date.strip()
                else "open_lifecycle"
            ),
        },
        "major_events": major_events,
        "notes": notes.strip(),
        "source": {
            "created_by": "person_intake_service",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        "status": {
            "intake_complete": bool(full_name.strip()),
            "has_birth_date": bool(birth_date.strip()),
            "has_birth_time": bool(birth_time.strip()),
            "has_birth_place": bool(birth_place.strip()),
            "has_death_date": bool(death_date.strip()),
            "has_major_events": bool(major_events),
            "ready_for_compile": bool(full_name.strip()),
        },
    }


def build_warnings(intake: dict[str, Any]) -> list[str]:
    """Build intake warnings."""
    warnings: list[str] = []

    birth = intake.get("birth", {})

    if not birth.get("date"):
        warnings.append("Birth date missing. Temporal and natal layers will be limited.")

    if not birth.get("time"):
        warnings.append("Birth time missing. Houses, lagna, and timing-sensitive layers will be limited.")

    if not birth.get("place"):
        warnings.append("Birth place missing. Natal and temporal precision will be limited.")

    return warnings


def slugify(value: str) -> str:
    """Create Atlas-safe profile key."""
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "_", value)
    value = re.sub(r"_+", "_", value)
    return value.strip("_")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    """Write JSON with stable formatting."""
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def failure_payload(error: str) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": PERSON_INTAKE_SERVICE_VERSION,
        "profile_key": "",
        "profile_dir": "",
        "created_files": [],
        "warnings": [],
        "errors": [error],
    }