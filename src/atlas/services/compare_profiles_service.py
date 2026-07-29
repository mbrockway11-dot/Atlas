"""Canonical Compare Profiles service."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from atlas.acf.builder import export_acf_profile
from atlas.compiled.calibration import CalibrationStatisticsArtifact
from atlas.compiled.identity_vector_artifact import (
    CompiledIdentityVectorArtifact,
)
from atlas.compiled.runtime import (
    MODES_REQUIRING_CALIBRATION,
    CompiledRuntimeError,
    build_runtime_identity_vector,
    load_runtime_statistics,
    runtime_provenance,
)
from atlas.comparison import compare_planet_agreement
from atlas.ive import (
    build_identity_vector,
    compare_identity_vectors,
    identity_similarity_to_dict,
)
from atlas.library.profile_library import LIBRARY_DIR


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
    """Build canonical compare profiles payload.

    Pairwise comparison defaults to ``"percentile"`` (population-normalized).
    Raw self-normalized vectors saturate -- every pair scores ~0.95 similar
    (measured sd 0.015 vs percentile sd 0.069 over the corpus), so raw does not
    discriminate people. The single-profile representation stays raw
    (``build_identity_vector``); only *comparison* needs the population frame.
    Percentile loads the precomputed calibration statistics; if none are
    available it falls back to raw with a warning rather than collapsing every
    feature to 0.5. This default (distinct from the builder's raw default) is
    locked by ``tests/test_normalization_default.py``.
    """
    warnings: list[str] = []
    errors: list[str] = []

    if profile_a_key == profile_b_key:
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error="Choose two different profiles.",
        )

    statistics = None
    if normalization_mode in MODES_REQUIRING_CALIBRATION:
        try:
            statistics = load_runtime_statistics()
        except CompiledRuntimeError:
            warnings.append(
                f"No calibration available; {normalization_mode} comparison "
                "would collapse every feature to 0.5. Falling back to raw -- "
                "note raw comparison saturates (~0.95 for every pair) and does "
                "not discriminate."
            )
            normalization_mode = "raw"

    try:
        vector_a, artifact_a = resolve_runtime_identity_vector(
            profile_a_key,
            normalization_mode=normalization_mode,
            statistics=statistics,
        )
        vector_b, artifact_b = resolve_runtime_identity_vector(
            profile_b_key,
            normalization_mode=normalization_mode,
            statistics=statistics,
        )
    except CompiledRuntimeError as exc:
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error=str(exc),
        )

    try:
        comparison = compare_identity_vectors(vector_a, vector_b)
        planet_matrix = build_planet_agreement_from_vectors(vector_a, vector_b)

    except Exception as exc:  # noqa: BLE001
        return failed_payload(
            profile_a_key=profile_a_key,
            profile_b_key=profile_b_key,
            normalization_mode=normalization_mode,
            error=f"Comparison failed: {exc}",
        )

    calibration_count = statistics.profile_count if statistics else 0

    summary = {
        "profile_a_name": artifact_a.profile_name,
        "profile_b_name": artifact_b.profile_name,
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
        "compiled_runtime": {
            "profile_a": runtime_provenance(artifact_a),
            "profile_b": runtime_provenance(artifact_b),
            "calibration": (
                {
                    "source_manifest_hash": statistics.source_manifest_hash,
                    "profile_count": statistics.profile_count,
                    "vector_count": statistics.vector_count,
                    "compiler_version": statistics.compiler_version,
                }
                if statistics is not None
                else None
            ),
        },
    }

    return CompareProfilesPayload(
        success=True,
        version=COMPARE_PROFILES_SERVICE_VERSION,
        profile_a={
            "key": profile_a_key,
            "name": artifact_a.profile_name,
            "entity_type": artifact_a.entity_type,
        },
        profile_b={
            "key": profile_b_key,
            "name": artifact_b.profile_name,
            "entity_type": artifact_b.entity_type,
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


def resolve_runtime_identity_vector(
    profile_key: str,
    *,
    normalization_mode: str,
    statistics: CalibrationStatisticsArtifact | None,
) -> tuple[Any, CompiledIdentityVectorArtifact]:
    """Build one identity vector from the compiled runtime.

    The happy path never opens the source ACF. If the artifact cannot be
    resolved -- typically an older export missing ``identity_graph`` -- the
    ACF is repaired once and the compile retried. A second failure is a
    controlled service error, not a fall back to reparsing the corpus.
    """
    try:
        return build_runtime_identity_vector(
            profile_key,
            normalization_mode=normalization_mode,
            statistics=statistics,
        )
    except CompiledRuntimeError:
        if load_or_repair_acf(profile_key) is None:
            raise CompiledRuntimeError(
                f"Could not load ACF profile {profile_key!r}."
            ) from None

    return build_runtime_identity_vector(
        profile_key,
        normalization_mode=normalization_mode,
        statistics=statistics,
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
