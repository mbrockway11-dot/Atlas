"""Birth data normalization for Atlas Temporal Intelligence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.temporal.models import BirthData


BIRTH_ENGINE_VERSION = "1.0"


UNKNOWN_TIME_VALUES = {
    "",
    "unknown",
    "unk",
    "n/a",
    "na",
    "none",
}


def build_birth_data_from_intake(
    intake: dict[str, Any],
) -> BirthData:
    """Build BirthData from profile.intake.json dictionary."""

    birth_time = normalize_birth_time(
        intake.get("birth_time", ""),
    )

    return BirthData(
        name=normalize_text(
            intake.get("name", "Unknown"),
        ),
        birth_date=normalize_text(
            intake.get("birth_date", ""),
        ),
        birth_time=birth_time,
        birth_place=normalize_text(
            intake.get("birth_place", ""),
        ),
        latitude=normalize_optional_float(
            intake.get("latitude"),
        ),
        longitude=normalize_optional_float(
            intake.get("longitude"),
        ),
        timezone=normalize_text(
            intake.get("timezone", ""),
        ),
        source_file=normalize_text(
            intake.get("source_file", ""),
        ),
        row_number=int(
            intake.get("row_number", 0) or 0,
        ),
        time_known=is_birth_time_known(birth_time),
    )


def load_birth_data_from_profile(
    profile_dir: Path,
) -> BirthData:
    """Load BirthData from a profile directory."""

    intake_path = profile_dir / "profile.intake.json"

    if not intake_path.exists():
        return BirthData(
            name=profile_dir.name,
            birth_date="",
            birth_time="Unknown",
            birth_place="",
            source_file="",
            row_number=0,
            time_known=False,
        )

    intake = json.loads(
        intake_path.read_text(
            encoding="utf-8",
        )
    )

    return build_birth_data_from_intake(intake)


def normalize_text(
    value: Any,
) -> str:
    """Normalize text."""

    if value is None:
        return ""

    return str(value).strip()


def normalize_birth_time(
    value: Any,
) -> str:
    """Normalize birth time."""

    text = normalize_text(value)

    if text.casefold() in UNKNOWN_TIME_VALUES:
        return "Unknown"

    return text


def is_birth_time_known(
    value: Any,
) -> bool:
    """Return True if birth time is known."""

    return normalize_birth_time(value) != "Unknown"


def normalize_optional_float(
    value: Any,
) -> float | None:
    """Normalize optional float."""

    if value is None:
        return None

    text = normalize_text(value)

    if not text:
        return None

    try:
        return float(text)

    except ValueError:
        return None