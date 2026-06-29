"""Corpus validation utilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from atlas.corpus.duplicates import (
    detect_duplicates_and_aliases,
)

EXPECTED_PLANETS = {
    "Saturn",
    "Jupiter",
    "Mars",
    "Sun",
    "Venus",
    "Mercury",
    "Moon",
}


@dataclass(frozen=True)
class CorpusValidationResult:
    """Corpus validation result."""

    valid: bool
    profile_count: int
    errors: list[str]
    warnings: list[str]


def validate_profile_acfs(
    acfs: list[dict[str, Any]],
) -> CorpusValidationResult:
    """Validate loaded ACF profiles before corpus export."""

    errors: list[str] = []
    warnings: list[str] = []

    seen_names: set[str] = set()

    for index, acf in enumerate(acfs):
        identity = acf.get("identity", {})
        name = identity.get("name")

        if not name:
            errors.append(
                f"Profile {index} is missing identity.name."
            )
            continue

        if name in seen_names:
            warnings.append(
                f"Duplicate profile name detected: {name}"
            )

        seen_names.add(name)

        invariant = acf.get("invariant_analysis", {})
        analyses = invariant.get("analyses", [])

        if len(analyses) != 21:
            errors.append(
                f"{name} has {len(analyses)} invariant analyses; expected 21."
            )

        planets = {
            analysis.get("planet")
            for analysis in analyses
        }

        missing_planets = EXPECTED_PLANETS - planets

        if missing_planets:
            errors.append(
                f"{name} is missing planets: {sorted(missing_planets)}"
            )

    duplicate_result = detect_duplicates_and_aliases(
        [
            acf.get("identity", {}).get("name", "")
            for acf in acfs
            if acf.get("identity", {}).get("name")
        ]
    )

    if duplicate_result.exact_duplicates:
        warnings.append(
            f"Exact duplicate names detected: "
            f"{duplicate_result.exact_duplicates}"
        )

    if duplicate_result.possible_aliases:
        warnings.append(
            f"Possible aliases detected: "
            f"{duplicate_result.possible_aliases}"
        )

    return CorpusValidationResult(
        valid=not errors,
        profile_count=len(acfs),
        errors=errors,
        warnings=warnings,
    )


def validate_profile_library(
    profile_library: str | Path,
) -> CorpusValidationResult:
    """Validate profile library folder structure."""

    path = Path(profile_library)

    errors: list[str] = []
    warnings: list[str] = []

    if not path.exists():
        return CorpusValidationResult(
            valid=False,
            profile_count=0,
            errors=[
                f"Profile library not found: {path}"
            ],
            warnings=[],
        )

    profile_dirs = [
        child
        for child in path.iterdir()
        if child.is_dir()
    ]

    for profile_dir in profile_dirs:
        acf_path = profile_dir / "profile.acf.json"

        if not acf_path.exists():
            errors.append(
                f"Missing profile.acf.json in {profile_dir}"
            )

    return CorpusValidationResult(
        valid=not errors,
        profile_count=len(profile_dirs),
        errors=errors,
        warnings=warnings,
    )


def validation_result_to_dict(
    result: CorpusValidationResult,
) -> dict[str, Any]:
    """Convert validation result to dictionary."""

    return {
        "valid": result.valid,
        "profile_count": result.profile_count,
        "errors": result.errors,
        "warnings": result.warnings,
    }