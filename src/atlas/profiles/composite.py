"""Composite profile manifest builders."""

from pathlib import Path
from typing import Any

from atlas.export.json import write_json


def build_composite_profile_manifest(
    name: str,
    profile_dir: str | Path,
) -> dict[str, Any]:
    """Build a JSON-safe manifest linking composite profile outputs."""
    path = Path(profile_dir)
    profile_key = _safe_name(name)

    analyses = []

    for json_path in sorted(path.glob("*.json")):
        if json_path.name.endswith("_profile_summary.json"):
            continue

        if json_path.name.endswith("_profile_interpretation.json"):
            continue

        analyses.append(
            {
                "file": json_path.name,
                "path": json_path.as_posix(),
            }
        )

    return {
        "name": name,
        "profile_key": profile_key,
        "profile_dir": path.as_posix(),
        "composite_overlay_svg": (
            path / f"{profile_key}_composite_overlay.svg"
        ).as_posix(),
        "profile_summary_json": (
            path / f"{profile_key}_profile_summary.json"
        ).as_posix(),
        "profile_interpretation_json": (
            path / f"{profile_key}_profile_interpretation.json"
        ).as_posix(),
        "codex_report_markdown": (
            path / f"{profile_key}_codex_report.md"
        ).as_posix(),
        "analysis_files": analyses,
        "analysis_count": len(analyses),
    }


def write_composite_profile_manifest(
    name: str,
    profile_dir: str | Path,
) -> Path:
    """Write composite_profile.json into a profile directory."""
    path = Path(profile_dir)
    manifest = build_composite_profile_manifest(name, path)

    output_path = path / "composite_profile.json"
    write_json(manifest, output_path)

    return output_path


def _safe_name(name: str) -> str:
    """Create safe lowercase filename stem."""
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )