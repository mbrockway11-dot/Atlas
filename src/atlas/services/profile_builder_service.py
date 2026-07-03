"""Canonical Profile Builder service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.acf.builder import build_acf_profile, export_acf_profile
from atlas.database import upsert_entity
from atlas.essence.profile import build_essence_profile
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.library.profile_library import (
    LIBRARY_DIR,
    save_profile_to_library,
    safe_name,
)
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report, write_markdown_report


PROFILE_BUILDER_SERVICE_VERSION = "3.0"


@dataclass(slots=True)
class ProfileBuilderPayload:
    """Canonical Profile Builder payload."""

    success: bool
    version: str
    name: str
    entity_type: str
    profile_key: str | None
    profile_dir: Path | None
    summary: dict[str, Any] | None
    interpretation: Any | None
    acf: dict[str, Any] | None
    entity: dict[str, Any] | None
    paths: dict[str, Path]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary payload."""
        return {
            "success": self.success,
            "version": self.version,
            "name": self.name,
            "entity_type": self.entity_type,
            "profile_key": self.profile_key,
            "profile_dir": str(self.profile_dir) if self.profile_dir else None,
            "summary": self.summary,
            "interpretation": (
                profile_interpretation_to_dict(self.interpretation)
                if self.interpretation is not None
                else None
            ),
            "acf": self.acf,
            "entity": self.entity,
            "paths": {key: str(value) for key, value in self.paths.items()},
            "warnings": self.warnings,
            "errors": self.errors,
        }


def build_profile_builder_payload(
    *,
    name: str,
    entity_type: str,
    birth_confidence: str,
    tags: list[str] | None = None,
    notes: str | None = None,
    save_library: bool = True,
    export_acf: bool = True,
) -> ProfileBuilderPayload:
    """Build and index an Atlas profile through the canonical service layer."""
    clean_name = name.strip()

    if not clean_name:
        return failed_payload(
            name=name,
            entity_type=entity_type,
            error="Enter a name first.",
        )

    profile_key = safe_name(clean_name)
    profile_dir = LIBRARY_DIR / profile_key

    try:
        if save_library:
            profile_dir = save_profile_to_library(clean_name)
        else:
            profile_dir.mkdir(parents=True, exist_ok=True)

        summary = build_individual_profile_summary(clean_name)
        interpretation = interpret_profile_summary(summary)
        report = build_profile_markdown_report(summary, interpretation)

        summary_path = profile_dir / "profile_summary.json"
        interpretation_path = profile_dir / "profile_interpretation.json"
        report_path = profile_dir / "codex_report.md"

        write_json(summary_path, summary)
        write_json(
            interpretation_path,
            profile_interpretation_to_dict(interpretation),
        )
        write_markdown_report(report, report_path)

        essence_paths = build_essence_profile(clean_name, profile_dir)

        acf = build_acf_profile(
            name=clean_name,
            entity_type=entity_type,
        )

        acf_path = profile_dir / "profile.acf.json"
        if export_acf:
            export_acf_profile(
                name=clean_name,
                output_path=acf_path,
                entity_type=entity_type,
            )

        entity = upsert_entity(
            name=clean_name,
            entity_type=entity_type,
            tags=tags or [],
            birth_confidence=birth_confidence,
            notes=notes or None,
        )

    except Exception as exc:
        return failed_payload(
            name=clean_name,
            entity_type=entity_type,
            error=f"Profile build failed: {exc}",
        )

    paths = {
        "profile_dir": profile_dir,
        "summary": summary_path,
        "interpretation": interpretation_path,
        "report": report_path,
        "essence_json": essence_paths["json"],
        "essence_svg": essence_paths["svg"],
    }

    if export_acf:
        paths["acf"] = acf_path

    return ProfileBuilderPayload(
        success=True,
        version=PROFILE_BUILDER_SERVICE_VERSION,
        name=clean_name,
        entity_type=entity_type,
        profile_key=profile_key,
        profile_dir=profile_dir,
        summary=summary,
        interpretation=interpretation,
        acf=acf,
        entity=entity,
        paths=paths,
        warnings=[],
        errors=[],
    )


def failed_payload(*, name: str, entity_type: str, error: str) -> ProfileBuilderPayload:
    """Build failed Profile Builder payload."""
    return ProfileBuilderPayload(
        success=False,
        version=PROFILE_BUILDER_SERVICE_VERSION,
        name=name,
        entity_type=entity_type,
        profile_key=None,
        profile_dir=None,
        summary=None,
        interpretation=None,
        acf=None,
        entity=None,
        paths={},
        warnings=[],
        errors=[error],
    )


def write_json(path: Path, data: dict[str, Any]) -> None:
    """Write JSON data to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )