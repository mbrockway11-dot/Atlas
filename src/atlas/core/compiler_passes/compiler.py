"""Atlas Core Compiler.

Compiles saved Atlas profile-library artifacts into a CanonicalStructuralSignature.

This module is the internal compiler orchestrator. Business logic belongs in
compiler passes. Pass execution is handled by the CompilerEngine.
"""

from __future__ import annotations

from time import perf_counter
from typing import Any

from atlas.core.canonical_structural_signature import CanonicalStructuralSignature
from atlas.core.compiler_framework import (
    CompilationReport,
    CompilerContext,
    CompilerEngine,
    build_compilation_report,
)
from atlas.core.compiler_passes import (
    CipherPass,
    IdentityPass,
    KameaPass,
    AstronomyPass,
    StructuralMeasurementPass,
    TemporalPass,
    safe_load_profile,
)


CORE_COMPILER_VERSION = "3.0"


def build_default_engine() -> CompilerEngine:
    """Build the default Atlas compiler engine."""
    engine = CompilerEngine()
    engine.register(IdentityPass())
    engine.register(AstronomyPass())
    engine.register(CipherPass())
    engine.register(KameaPass())
    engine.register(StructuralMeasurementPass())
    engine.register(TemporalPass())
    return engine


def compile_profile(profile_key: str) -> CanonicalStructuralSignature:
    """Compile one profile into a CanonicalStructuralSignature."""
    css, _report = compile_profile_with_report(profile_key)
    return css


def compile_profile_with_report(
    profile_key: str,
) -> tuple[CanonicalStructuralSignature, CompilationReport]:
    """Compile one profile and return CSS plus compilation report."""
    profile_payload = safe_load_profile(profile_key)

    context = CompilerContext(
        profile_key=profile_key,
        profile_payload=profile_payload,
        metadata={
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
        },
    )

    css = CanonicalStructuralSignature(
        metadata={
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
            "profile_loaded": bool(profile_payload),
        }
    )

    engine = build_default_engine()
    start = perf_counter()
    css, pass_results = engine.run(css, context)
    total_elapsed_ms = (perf_counter() - start) * 1000

    report = build_compilation_report(
        compiler_version=CORE_COMPILER_VERSION,
        pass_results=pass_results,
        total_elapsed_ms=total_elapsed_ms,
    )

    css.metadata.update(
        {
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
            "profile_loaded": bool(profile_payload),
            "pass_count": report.pass_count,
            "passes": list(report.passes),
            "pass_results": report.to_dict()["pass_results"],
            "compilation_report": report.to_dict(),
        }
    )

    return css, report


def compile_profile_payload(profile_key: str) -> dict[str, Any]:
    """Compile one profile and return a serializable payload."""
    css, report = compile_profile_with_report(profile_key)

    return {
        "success": css.identity is not None and report.success,
        "version": CORE_COMPILER_VERSION,
        "profile_key": profile_key,
        "errors": list(report.errors),
        "warnings": list(report.warnings),
        "data": {
            "canonical_structural_signature": css.to_dict(),
        },
        "metrics": build_compiler_metrics(css),
        "compilation_report": report.to_dict(),
    }


def build_compiler_metrics(css: CanonicalStructuralSignature) -> dict[str, Any]:
    """Build compiler metrics."""
    return {
        "has_identity": css.identity is not None,
        "has_astronomy": bool(css.astronomy.measurements),
        "has_physical_planet_graph": bool(css.astronomy.planet_graph),
        "has_birth_date": bool(css.identity and css.identity.birth_date),
        "has_birth_time": bool(css.identity and css.identity.birth_time),
        "has_birth_location": bool(css.identity and css.identity.birth_location),
        "has_cipher": has_cipher_data(css),
        "has_kamea": has_kamea_data(css),
        "has_temporal": has_temporal_data(css),
        "has_natal": bool(css.temporal.natal),
        "has_transits": bool(css.temporal.transits),
        "has_dasha": bool(css.temporal.dasha),
        "has_calibration": bool(css.temporal.calibration),
        "has_topology": bool(css.kamea.topology),
        "has_planetary_graphs": bool(css.kamea.planetary_graphs),
        "has_resonance": bool(css.kamea.resonance),
        "has_graph_metrics": bool(css.kamea.graph_metrics),
        "has_fingerprint": bool(css.kamea.fingerprint),
        "has_normalized_kamea_graphs": bool(css.kamea.normalized_graphs),
        "has_structural_measurements": bool(css.kamea.structural_metrics),
        "has_master_graph": bool(css.structural_measurement.master_graph),
        "has_structural_feature_vector": bool(
            css.structural_measurement.feature_vector
        ),
        "compiler_version": css.metadata.get("compiler_version"),
        "pass_count": css.metadata.get("pass_count", 0),
        "report_success": css.metadata.get("compilation_report", {}).get("success"),
        "total_elapsed_ms": css.metadata.get("compilation_report", {}).get("total_elapsed_ms"),
    }


def has_cipher_data(css: CanonicalStructuralSignature) -> bool:
    """Return whether cipher layer has any data."""
    return any(
        [
            bool(css.cipher.ordinal),
            bool(css.cipher.hebrew_phonetic),
            bool(css.cipher.hebrew_transliteration),
            bool(css.cipher.gematria),
        ]
    )


def has_kamea_data(css: CanonicalStructuralSignature) -> bool:
    """Return whether Kamea layer has any data."""
    return any(
        [
            bool(css.kamea.topology),
            bool(css.kamea.planetary_graphs),
            bool(css.kamea.resonance),
            bool(css.kamea.graph_metrics),
            bool(css.kamea.fingerprint),
        ]
    )


def has_temporal_data(css: CanonicalStructuralSignature) -> bool:
    """Return whether temporal layer has any data."""
    return any(
        [
            bool(css.temporal.natal),
            bool(css.temporal.transits),
            bool(css.temporal.dasha),
            bool(css.temporal.calibration),
        ]
    )
