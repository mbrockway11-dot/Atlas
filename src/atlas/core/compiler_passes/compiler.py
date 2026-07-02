"""Atlas Core Compiler.

Compiles saved Atlas profile-library artifacts into a CanonicalStructuralSignature.

This module is the internal compiler orchestrator. Business logic belongs in
compiler passes. Pass execution is handled by the CompilerEngine.
"""

from __future__ import annotations

from typing import Any

from atlas.core.canonical_structural_signature import CanonicalStructuralSignature
from atlas.core.compiler_framework import CompilerContext, CompilerEngine
from atlas.core.compiler_passes import (
    CipherPass,
    IdentityPass,
    KameaPass,
    TemporalPass,
    safe_load_profile,
)


CORE_COMPILER_VERSION = "2.0"


def build_default_engine() -> CompilerEngine:
    """Build the default Atlas compiler engine."""
    engine = CompilerEngine()
    engine.register(IdentityPass())
    engine.register(CipherPass())
    engine.register(KameaPass())
    engine.register(TemporalPass())
    return engine


def compile_profile(profile_key: str) -> CanonicalStructuralSignature:
    """Compile one profile into a CanonicalStructuralSignature."""
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
    css, pass_results = engine.run(css, context)

    css.metadata.update(
        {
            "compiler_version": CORE_COMPILER_VERSION,
            "source": "atlas.core.compiler",
            "profile_loaded": bool(profile_payload),
            "pass_count": len(pass_results),
            "passes": [result.name for result in pass_results],
            "pass_results": [
                {
                    "name": result.name,
                    "success": result.success,
                    "warnings": list(result.warnings),
                    "errors": list(result.errors),
                    "elapsed_ms": result.elapsed_ms,
                }
                for result in pass_results
            ],
        }
    )

    return css


def compile_profile_payload(profile_key: str) -> dict[str, Any]:
    """Compile one profile and return a serializable payload."""
    css = compile_profile(profile_key)

    pass_results = css.metadata.get("pass_results", [])
    errors = [
        error
        for result in pass_results
        for error in result.get("errors", [])
    ]
    warnings = [
        warning
        for result in pass_results
        for warning in result.get("warnings", [])
    ]

    return {
        "success": css.identity is not None and not errors,
        "version": CORE_COMPILER_VERSION,
        "profile_key": profile_key,
        "errors": errors,
        "warnings": warnings,
        "data": {
            "canonical_structural_signature": css.to_dict(),
        },
        "metrics": build_compiler_metrics(css),
    }


def build_compiler_metrics(css: CanonicalStructuralSignature) -> dict[str, Any]:
    """Build compiler metrics."""
    return {
        "has_identity": css.identity is not None,
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
        "compiler_version": css.metadata.get("compiler_version"),
        "pass_count": css.metadata.get("pass_count", 0),
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
