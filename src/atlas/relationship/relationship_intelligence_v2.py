
"""Relationship Intelligence v2.

Compares two canonical Atlas profiles using structural vectors, topology,
resonance, rarity, impact, and graph-density behavior.
"""

from __future__ import annotations

from typing import Any

from atlas.population.structural_neighbors_v2 import (
    build_population_vectors,
    build_structural_vector,
    compare_vectors,
)
from atlas.population.structural_rarity import build_structural_rarity_report
from atlas.population.structural_impact import build_structural_impact_report
from atlas.compiler.canonical_profile_compiler import compile_canonical_profile


RELATIONSHIP_INTELLIGENCE_VERSION = "2.0"


def compare_relationship_v2(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Compare two profiles through Relationship Intelligence v2."""

    payload_a = compile_canonical_profile(profile_a, force=False)
    payload_b = compile_canonical_profile(profile_b, force=False)

    if not payload_a.get("success"):
        return failure(profile_a, payload_a.get("errors", []))

    if not payload_b.get("success"):
        return failure(profile_b, payload_b.get("errors", []))

    vector_a = build_structural_vector(payload_a)
    vector_b = build_structural_vector(payload_b)

    comparison = compare_vectors(vector_a, vector_b)

    rarity = build_structural_rarity_report()
    impact = build_structural_impact_report()

    rarity_map = {
        item["profile_key"]: item
        for item in rarity.get("profiles", [])
    }

    impact_map = {
        item["profile_key"]: item
        for item in impact.get("profiles", [])
    }

    rarity_a = rarity_map.get(profile_a, {})
    rarity_b = rarity_map.get(profile_b, {})

    impact_a = impact_map.get(profile_a, {})
    impact_b = impact_map.get(profile_b, {})

    compatibility = build_compatibility(comparison, vector_a, vector_b)

    return {
        "success": True,
        "version": RELATIONSHIP_INTELLIGENCE_VERSION,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "vector_a": vector_a,
        "vector_b": vector_b,
        "structural_similarity": comparison,
        "compatibility": compatibility,
        "complementarity": build_complementarity(vector_a, vector_b, rarity_a, rarity_b, impact_a, impact_b),
        "friction": build_friction(vector_a, vector_b, comparison),
        "shared_strengths": build_shared_strengths(vector_a, vector_b, comparison),
        "relationship_summary": build_relationship_summary(vector_a, vector_b, comparison, compatibility),
        "rarity": {
            profile_a: compact_rarity(rarity_a),
            profile_b: compact_rarity(rarity_b),
        },
        "impact": {
            profile_a: compact_impact(impact_a),
            profile_b: compact_impact(impact_b),
        },
    }


def build_compatibility(
    comparison: dict[str, Any],
    vector_a: dict[str, Any],
    vector_b: dict[str, Any],
) -> dict[str, Any]:
    """Build compatibility interpretation."""

    similarity = float(comparison.get("similarity") or 0)
    breakdown = comparison.get("breakdown", {})

    score = (
        similarity * 0.55
        + float(breakdown.get("topology", 0)) * 0.15
        + float(breakdown.get("resonance", 0)) * 0.10
        + float(breakdown.get("numeric", 0)) * 0.20
    )

    return {
        "score": round(score, 6),
        "percent": round(score * 100, 2),
        "label": compatibility_label(score),
        "shared": comparison.get("shared", []),
        "differences": comparison.get("differences", []),
    }


def build_complementarity(
    vector_a: dict[str, Any],
    vector_b: dict[str, Any],
    rarity_a: dict[str, Any],
    rarity_b: dict[str, Any],
    impact_a: dict[str, Any],
    impact_b: dict[str, Any],
) -> dict[str, Any]:
    """Build complementarity report."""

    role_a = vector_a.get("role")
    role_b = vector_b.get("role")

    complementary = []

    if role_a != role_b:
        complementary.append(f"Different roles: {role_a} / {role_b}")

    if vector_a.get("axis") != vector_b.get("axis"):
        complementary.append(
            f"Different dominant axes: {vector_a.get('axis')} / {vector_b.get('axis')}"
        )

    if abs(float(vector_a.get("truth_density") or 0) - float(vector_b.get("truth_density") or 0)) >= 0.35:
        complementary.append("Different truth-density behavior may create useful contrast.")

    if abs(float(impact_a.get("impact_score") or 0) - float(impact_b.get("impact_score") or 0)) >= 0.15:
        complementary.append("One profile may act as the stronger structural impact carrier.")

    if not complementary:
        complementary.append("Complementarity is mostly similarity-based rather than contrast-based.")

    return {
        "signals": complementary,
        "summary": " ".join(complementary),
    }


def build_friction(
    vector_a: dict[str, Any],
    vector_b: dict[str, Any],
    comparison: dict[str, Any],
) -> dict[str, Any]:
    """Build likely friction report."""

    friction = []

    if vector_a.get("role") != vector_b.get("role"):
        friction.append("Different structural roles may prioritize different forms of coherence.")

    if vector_a.get("topology") != vector_b.get("topology"):
        friction.append("Different topology classes may organize pressure and information differently.")

    if vector_a.get("axis") != vector_b.get("axis"):
        friction.append("Different dominant axes may create timing, priority, or interpretation mismatches.")

    if abs(float(vector_a.get("motif_richness") or 0) - float(vector_b.get("motif_richness") or 0)) >= 0.25:
        friction.append("Motif richness gap may cause one profile to see recurring patterns faster than the other.")

    if abs(float(vector_a.get("truth_density") or 0) - float(vector_b.get("truth_density") or 0)) >= 0.35:
        friction.append("Truth-density gap may create different thresholds for what feels structurally important.")

    if not friction:
        friction.append("Primary friction is likely subtle because the structural profiles are highly aligned.")

    return {
        "signals": friction,
        "summary": " ".join(friction),
    }


def build_shared_strengths(
    vector_a: dict[str, Any],
    vector_b: dict[str, Any],
    comparison: dict[str, Any],
) -> list[str]:
    """Build shared strengths."""

    strengths = []

    for item in comparison.get("shared", []):
        strengths.append(f"Shared {item}")

    if vector_a.get("role") == vector_b.get("role"):
        strengths.append(f"Both profiles operate through {vector_a.get('role')} structure.")

    if vector_a.get("topology") == vector_b.get("topology"):
        strengths.append(f"Shared topology: {vector_a.get('topology')}.")

    if vector_a.get("resonance") == vector_b.get("resonance"):
        strengths.append(f"Shared resonance: {vector_a.get('resonance')}.")

    if not strengths:
        strengths.append("Shared strengths are currently inferred from numeric similarity rather than identical labels.")

    return strengths


def build_relationship_summary(
    vector_a: dict[str, Any],
    vector_b: dict[str, Any],
    comparison: dict[str, Any],
    compatibility: dict[str, Any],
) -> str:
    """Build readable relationship synthesis."""

    similarity_percent = comparison.get("similarity_percent", 0)
    compatibility_percent = compatibility.get("percent", 0)
    compatibility_label = compatibility.get("label", "unknown")

    return f"""
Relationship Intelligence v2 compares these profiles through graph-native structural vectors.

The pair currently scores **{similarity_percent}% structural similarity** and **{compatibility_percent}% compatibility** ({compatibility_label}).

Profile A resolves as **{vector_a.get('role')}** with **{vector_a.get('topology')}** topology.

Profile B resolves as **{vector_b.get('role')}** with **{vector_b.get('topology')}** topology.

This comparison should be read as structural interaction rather than simple compatibility. It describes how two identity graphs may align, contrast, reinforce, or create friction through topology, resonance, motif behavior, density, and role expression.
""".strip()


def compact_rarity(record: dict[str, Any]) -> dict[str, Any]:
    """Compact rarity record."""
    return {
        "overall_rarity_score": record.get("overall_rarity_score"),
        "outlier_label": record.get("outlier_label"),
        "outlier_reasons": record.get("outlier_reasons", []),
    }


def compact_impact(record: dict[str, Any]) -> dict[str, Any]:
    """Compact impact record."""
    return {
        "impact_score": record.get("impact_score"),
        "impact_percent": record.get("impact_percent"),
        "impact_label": record.get("impact_label"),
        "impact_reasons": record.get("impact_reasons", []),
    }


def compatibility_label(score: float) -> str:
    """Return compatibility label."""
    if score >= 0.85:
        return "very_high_structural_alignment"
    if score >= 0.70:
        return "high_structural_alignment"
    if score >= 0.55:
        return "moderate_structural_alignment"
    if score >= 0.40:
        return "mixed_structural_alignment"
    return "low_structural_alignment"


def failure(profile_key: str, errors: list[Any]) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": RELATIONSHIP_INTELLIGENCE_VERSION,
        "profile_key": profile_key,
        "errors": errors,
    }
