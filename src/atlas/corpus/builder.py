"""Research corpus builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.corpus.export import export_corpus_rows
from atlas.corpus.schema import build_corpus_metadata
from atlas.corpus.statistics import build_corpus_statistics
from atlas.corpus.validation import (
    validate_profile_acfs,
    validate_profile_library,
    validation_result_to_dict,
)
from atlas.fusion import build_translation_fusion_report
from atlas.ive import (
    build_identity_vector,
    identity_vector_to_dict,
)
from atlas.ontology import synthesize_identity_ontology


def build_research_corpus(
    profile_library: str | Path = "output/library/profiles",
    output_directory: str | Path = "research/corpus",
    normalization_mode: str = "raw",
) -> dict[str, Any]:
    """Build a one-row-per-profile research corpus.

    Each saved profile folder must contain profile.acf.json.
    """
    profile_library_path = Path(profile_library)
    output_dir = Path(output_directory)

    library_validation = validate_profile_library(profile_library_path)

    if not library_validation.valid:
        raise ValueError(
            f"Profile library validation failed: {library_validation.errors}"
        )

    acfs = load_profile_acfs(profile_library_path)

    acf_validation = validate_profile_acfs(acfs)

    if not acf_validation.valid:
        raise ValueError(
            f"ACF validation failed: {acf_validation.errors}"
        )

    rows = []

    for acf in acfs:
        identity_vector = build_identity_vector(
            acf,
            calibration_acfs=acfs if normalization_mode != "raw" else None,
            normalization_mode=normalization_mode,
        )
        ontology = synthesize_identity_ontology(identity_vector)
        translation_fusion = build_translation_fusion_report(acf)

        rows.append(
            flatten_profile_record(
                identity_vector=identity_vector,
                ontology=ontology,
                translation_fusion=translation_fusion,
            )
        )

    metadata = build_corpus_metadata(profile_count=len(rows))
    metadata["validation"] = {
        "library": validation_result_to_dict(library_validation),
        "acfs": validation_result_to_dict(acf_validation),
    }

    export_paths = export_corpus_rows(rows, output_dir, metadata)
    statistics = build_corpus_statistics(rows, output_dir)

    return {
        "profile_count": len(rows),
        "rows": rows,
        "metadata": metadata,
        "statistics": statistics,
        "exports": export_paths,
        "validation": {
            "library": library_validation,
            "acfs": acf_validation,
        },
    }


def load_profile_acfs(profile_library: Path) -> list[dict]:
    """Load all profile.acf.json files from a profile library."""
    if not profile_library.exists():
        raise FileNotFoundError(f"Profile library not found: {profile_library}")

    acfs = []

    for profile_dir in sorted(profile_library.iterdir()):
        if not profile_dir.is_dir():
            continue

        acf_path = profile_dir / "profile.acf.json"

        if not acf_path.exists():
            continue

        acfs.append(
            json.loads(acf_path.read_text(encoding="utf-8"))
        )

    if not acfs:
        raise ValueError(f"No ACF profiles found in {profile_library}")

    return acfs


def flatten_profile_record(
    *,
    identity_vector,
    ontology: dict,
    translation_fusion=None,
) -> dict[str, Any]:
    """Flatten IdentityVector + ontology + fusion into one corpus row."""
    data = identity_vector_to_dict(identity_vector)

    row: dict[str, Any] = {
        "name": identity_vector.name,
        "identity_vector_version": identity_vector.version,
        "normalization_mode": identity_vector.quality["normalization_mode"],
    }

    for key, value in data["global_features"].items():
        row[f"global_{key}"] = value

    for key, value in data["quality"].items():
        if isinstance(value, int | float | str):
            row[f"quality_{key}"] = value

    for key, value in data["diagnostics"].items():
        if isinstance(value, int | float | str):
            row[f"diagnostic_{key}"] = value

    for planet, planet_vector in data["planets"].items():
        prefix = planet.lower()

        for feature, value in planet_vector["features"].items():
            row[f"{prefix}_{feature}"] = value

        row[f"{prefix}_source_count"] = planet_vector["source_count"]

    global_archetypes = ontology.get("global_archetypes", [])

    if global_archetypes:
        row["primary_archetype"] = global_archetypes[0]["key"]
        row["primary_archetype_label"] = global_archetypes[0]["label"]
        row["primary_archetype_score"] = global_archetypes[0]["score"]

    if len(global_archetypes) > 1:
        row["secondary_archetype"] = global_archetypes[1]["key"]
        row["secondary_archetype_label"] = global_archetypes[1]["label"]
        row["secondary_archetype_score"] = global_archetypes[1]["score"]

    for archetype in global_archetypes:
        key = archetype["key"]
        row[f"archetype_{key}"] = archetype["score"]

    if translation_fusion is not None:
        add_translation_fusion_fields(
            row=row,
            translation_fusion=translation_fusion,
        )

    return row


def add_translation_fusion_fields(
    *,
    row: dict[str, Any],
    translation_fusion,
) -> None:
    """Add translation-fusion agreement and confidence fields to corpus row."""
    row["fusion_global_agreement_score"] = (
        translation_fusion.global_agreement_score
    )
    row["fusion_global_confidence_score"] = (
        translation_fusion.global_confidence_score
    )
    row["fusion_global_completeness"] = (
        translation_fusion.global_completeness
    )

    for planet, planet_fusion in translation_fusion.planets.items():
        prefix = planet.lower()

        row[f"fusion_{prefix}_agreement_score"] = (
            planet_fusion.agreement_score
        )
        row[f"fusion_{prefix}_confidence_score"] = (
            planet_fusion.confidence_score
        )
        row[f"fusion_{prefix}_completeness"] = (
            planet_fusion.completeness
        )