"""Canonical Compare Profiles service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from atlas.acf.builder import export_acf_profile
from atlas.comparison import compare_planet_agreement
from atlas.ive import (
    build_identity_vector,
    compare_identity_vectors,
    identity_similarity_to_dict,
)
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


COMPARE_PROFILES_SERVICE_VERSION = "3.0"


@dataclass(slots=True)
class CompareProfilesPayload:
    """Canonical Compare Profiles payload."""

    success: bool
    version: str
    profile_a: dict[str, Any]
    profile_b: dict[str, Any]
    normalization_mode: str
    vector_a: Any | None
    vector_b: Any | None
    comparison: Any | None
    planet_matrix: Any | None
    diagnostics: dict[str, Any]
    summary: dict[str, Any]
    warnings: list[str]
    errors: list[str]

    def to_dict(self) -> dict[str, Any]:
        """Return dictionary payload."""
        return {
            "success": self.success,
            "version": self.version,
            "profile_a": self.profile_a,
            "profile_b": self.profile_b,
            "normalization_mode": self.normalization_mode,
            "vector_a": self.vector_a,
            "vector_b": self.vector_b,
            "comparison": (
                identity_similarity_to_dict(self.comparison)
                if self.comparison is not None
                else None
            ),
            "planet_matrix": (
                planet_agreement_to_dict(self.planet_matrix)
                if self.planet_matrix is not None
                else None
            ),
            "diagnostics": self.diagnostics,
            "summary": self.summary,
            "warnings": self.warnings,
            "errors": self.errors,
        }


def build_compare_profiles_payload(
    profile_a_key: str,
    profile_b_key: str,
    *,
    normalization_mode: str = "percentile",
) -> CompareProfilesPayload:
    """Build canonical compare profiles payload."""
    warnings: list[str] = []
    errors: list[str] = []

    if profile_a_key == profile_b_key:
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error="Choose two different profiles.",
        )

    acf_a = load_or_repair_acf(profile_a_key)
    acf_b = load_or_repair_acf(profile_b_key)

    if acf_a is None or acf_b is None:
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error="Could not load one or both ACF profiles.",
        )

    calibration_acfs = (
        load_calibration_acfs()
        if normalization_mode != "raw"
        else None
    )

    try:
        vector_a = build_identity_vector(
            acf=acf_a,
            calibration_acfs=calibration_acfs,
            normalization_mode=normalization_mode,
        )
        vector_b = build_identity_vector(
            acf=acf_b,
            calibration_acfs=calibration_acfs,
            normalization_mode=normalization_mode,
        )

        comparison = compare_identity_vectors(vector_a, vector_b)
        planet_matrix = build_planet_agreement_from_vectors(vector_a, vector_b)

    except Exception as exc:  # noqa: BLE001
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error=f"Comparison failed: {exc}",
        )

    calibration_count = len(calibration_acfs or [])

    summary = {
        "profile_a_name": acf_a["identity"]["name"],
        "profile_b_name": acf_b["identity"]["name"],
        "composite_similarity": comparison.composite_similarity,
        "global_similarity": comparison.global_similarity,
        "relationship_similarity": comparison.relationship_similarity,
        "global_distance": comparison.global_distance,
        "overall_planet_agreement": planet_matrix.overall_similarity,
        "normalization_mode": normalization_mode,
        "calibration_profile_count": calibration_count,
    }

    diagnostics = {
        "identity_similarity": comparison.diagnostics,
        "planet_agreement": {
            "dominant_match": planet_matrix.dominant_match,
            "dominant_divergence": planet_matrix.dominant_divergence,
            "planet_agreement": planet_matrix.planet_agreement,
        },
        "global_feature_delta": build_global_feature_delta(vector_a, vector_b),
        "planet_feature_delta": build_planet_feature_delta(vector_a, vector_b),
    }

    return CompareProfilesPayload(
        success=True,
        version=COMPARE_PROFILES_SERVICE_VERSION,
        profile_a={
            "key": profile_a_key,
            "name": acf_a["identity"]["name"],
            "entity_type": acf_a["identity"].get("entity_type", "person"),
        },
        profile_b={
            "key": profile_b_key,
            "name": acf_b["identity"]["name"],
            "entity_type": acf_b["identity"].get("entity_type", "person"),
        },
        normalization_mode=normalization_mode,
        vector_a=vector_a,
        vector_b=vector_b,
        comparison=comparison,
        planet_matrix=planet_matrix,
        diagnostics=diagnostics,
        summary=summary,
        warnings=warnings,
        errors=errors,
    )


def failed_payload(
    *,
    profile_a_key: str,
    profile_b_key: str,
    normalization_mode: str,
    error: str,
) -> CompareProfilesPayload:
    """Build failed comparison payload."""
    return CompareProfilesPayload(
        success=False,
        version=COMPARE_PROFILES_SERVICE_VERSION,
        profile_a={"key": profile_a_key},
        profile_b={"key": profile_b_key},
        normalization_mode=normalization_mode,
        vector_a=None,
        vector_b=None,
        comparison=None,
        planet_matrix=None,
        diagnostics={},
        summary={},
        warnings=[],
        errors=[error],
    )


def load_or_repair_acf(profile_key: str) -> dict | None:
    """Load ACF and repair older exports if required."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    data = json.loads(acf_path.read_text(encoding="utf-8"))

    required_keys = {
        "identity",
        "identity_graph",
        "identity_persistence",
        "invariant_analysis",
    }

    if required_keys.issubset(data.keys()):
        return data

    name = data["identity"]["name"]
    entity_type = data["identity"].get("entity_type", "person")

    export_acf_profile(
        name=name,
        output_path=acf_path,
        entity_type=entity_type,
    )

    return json.loads(acf_path.read_text(encoding="utf-8"))


def load_calibration_acfs() -> list[dict]:
    """Load saved ACF profiles as calibration corpus."""
    calibration_acfs = []

    for profile_key in list_saved_profiles():
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.exists():
            continue

        try:
            calibration_acfs.append(
                json.loads(acf_path.read_text(encoding="utf-8"))
            )
        except json.JSONDecodeError:
            continue

    return calibration_acfs


def build_planet_agreement_from_vectors(vector_a, vector_b):
    """Build Planet Agreement Matrix from IdentityVector planet features."""
    fingerprint_a = {
        planet: vector.features
        for planet, vector in vector_a.planets.items()
    }

    fingerprint_b = {
        planet: vector.features
        for planet, vector in vector_b.planets.items()
    }

    confidence_a = {
        planet: 1.0
        for planet in vector_a.planets
    }

    confidence_b = {
        planet: 1.0
        for planet in vector_b.planets
    }

    return compare_planet_agreement(
        fingerprint_a=fingerprint_a,
        fingerprint_b=fingerprint_b,
        confidence_a=confidence_a,
        confidence_b=confidence_b,
    )


def build_global_feature_delta(vector_a, vector_b) -> list[dict[str, Any]]:
    """Build global feature delta rows."""
    rows = []

    shared_features = sorted(
        set(vector_a.global_features)
        & set(vector_b.global_features)
    )

    for feature in shared_features:
        value_a = vector_a.global_features[feature]
        value_b = vector_b.global_features[feature]

        rows.append(
            {
                "feature": feature,
                "value_a": value_a,
                "value_b": value_b,
                "absolute_difference": abs(value_a - value_b),
            }
        )

    return sorted(
        rows,
        key=lambda row: row["absolute_difference"],
        reverse=True,
    )


def build_planet_feature_delta(vector_a, vector_b) -> list[dict[str, Any]]:
    """Build planet-level feature delta rows."""
    rows = []

    shared_planets = [
        planet
        for planet in vector_a.planets
        if planet in vector_b.planets
    ]

    for planet in shared_planets:
        features_a = vector_a.planets[planet].features
        features_b = vector_b.planets[planet].features

        shared_features = sorted(
            set(features_a)
            & set(features_b)
        )

        for feature in shared_features:
            value_a = features_a[feature]
            value_b = features_b[feature]

            rows.append(
                {
                    "planet": planet,
                    "feature": feature,
                    "value_a": value_a,
                    "value_b": value_b,
                    "absolute_difference": abs(value_a - value_b),
                }
            )

    return sorted(
        rows,
        key=lambda row: row["absolute_difference"],
        reverse=True,
    )


def planet_agreement_to_dict(matrix) -> dict[str, Any]:
    """Convert Planet Agreement Matrix to JSON-safe dictionary."""
    return {
        "overall_similarity": matrix.overall_similarity,
        "planet_similarity": matrix.planet_similarity,
        "planet_confidence": matrix.planet_confidence,
        "planet_variance": matrix.planet_variance,
        "planet_agreement": matrix.planet_agreement,
        "dominant_match": matrix.dominant_match,
        "dominant_divergence": matrix.dominant_divergence,
        "rows": [
            {
                "planet": row.planet,
                "similarity": row.similarity,
                "distance": row.distance,
                "confidence": row.confidence,
                "strongest_matches": row.strongest_matches,
                "strongest_differences": row.strongest_differences,
                "feature_distances": row.feature_distances,
            }
            for row in matrix.rows
        ],
    }

