"""Persistent Atlas profile library."""

from pathlib import Path
from typing import Any

from atlas.export.json import write_json
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report, write_markdown_report


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ROOT_LIBRARY_DIR = PROJECT_ROOT / "output" / "library"
LIBRARY_DIR = ROOT_LIBRARY_DIR / "profiles"


def save_profile_to_library(name: str) -> Path:
    """Build and save a complete profile library entry."""
    profile_dir = LIBRARY_DIR / safe_name(name)
    profile_dir.mkdir(parents=True, exist_ok=True)

    summary = build_individual_profile_summary(name)
    interpretation = interpret_profile_summary(summary)
    report = build_profile_markdown_report(summary, interpretation)

    write_json(summary, profile_dir / "profile_summary.json")
    write_json(
        profile_interpretation_to_dict(interpretation),
        profile_dir / "profile_interpretation.json",
    )
    write_markdown_report(report, profile_dir / "codex_report.md")

    return profile_dir


def list_saved_profiles() -> list[str]:
    """List saved profile names from legacy and canonical library layouts."""
    profiles: set[str] = set()

    for base_dir in [ROOT_LIBRARY_DIR, LIBRARY_DIR]:
        if not base_dir.exists():
            continue

        for path in base_dir.iterdir():
            if not path.is_dir():
                continue

            if path.name == "profiles":
                continue

            has_artifact = any(
                (path / artifact).exists()
                for artifact in [
                    "profile.intake.json",
                    "profile.payload.json",
                    "profile_summary.json",
                    "profile_interpretation.json",
                ]
            )

            if has_artifact:
                profiles.add(path.name)

    return sorted(profiles)


def load_profile_summary(profile_key: str) -> dict[str, Any]:
    """Load saved profile summary JSON."""
    import json

    path = LIBRARY_DIR / profile_key / "profile_summary.json"

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_profile_interpretation(profile_key: str) -> dict[str, Any]:
    """Load saved profile interpretation JSON."""
    import json

    path = LIBRARY_DIR / profile_key / "profile_interpretation.json"

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def profile_exists(profile_key: str) -> bool:
    """Return whether a profile exists in any supported library layout."""
    for base_dir in [ROOT_LIBRARY_DIR, LIBRARY_DIR]:
        profile_dir = base_dir / profile_key
        if any(
            (profile_dir / artifact).exists()
            for artifact in [
                "profile.intake.json",
                "profile.payload.json",
                "profile_summary.json",
                "profile_interpretation.json",
            ]
        ):
            return True

    return False


def safe_name(name: str) -> str:
    """Create safe lowercase filename stem."""
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )
