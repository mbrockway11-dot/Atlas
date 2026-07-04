"""Atlas interpretation synthesis.

Synthesis coordinates deterministic outputs and semantic interpretation.

It should not contain heavy interpretation logic itself. That belongs in
semantic_engine.py. This module is the orchestration bridge used by QA,
reports, and future reasoning kernels.
"""

from __future__ import annotations

from typing import Any

from atlas.interpretation.semantic_engine import (
    build_semantic_profile,
    build_semantic_relationship,
)


SYNTHESIS_VERSION = "2.0"


def synthesize_profile(
    *,
    profile_key: str,
    graph_pattern: str = "",
    temporal_overlay: str = "",
    natal_context: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
    role: str = "",
) -> dict[str, Any]:
    """Synthesize a single profile into semantic interpretation."""
    semantic = build_semantic_profile(
        profile_key=profile_key,
        role=role,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
        natal_context=natal_context,
        evidence=evidence or [],
    )

    return {
        "success": True,
        "version": SYNTHESIS_VERSION,
        "kind": "profile",
        "profile_key": profile_key,
        "semantic": semantic,
    }


def synthesize_relationship(
    *,
    profile_a: str,
    profile_b: str,
    graph_pattern: str = "",
    temporal_overlay: str = "",
    natal_context_a: dict[str, Any] | None = None,
    natal_context_b: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Synthesize a relationship into semantic interpretation."""
    evidence = evidence or []

    semantic_a = build_semantic_profile(
        profile_key=profile_a,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
        natal_context=natal_context_a or {},
        evidence=evidence,
    )

    semantic_b = build_semantic_profile(
        profile_key=profile_b,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
        natal_context=natal_context_b or {},
        evidence=evidence,
    )

    relationship = build_semantic_relationship(
        profile_a=semantic_a,
        profile_b=semantic_b,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
        evidence=evidence,
    )

    return {
        "success": True,
        "version": SYNTHESIS_VERSION,
        "kind": "relationship",
        "profiles": [profile_a, profile_b],
        "profile_a": semantic_a,
        "profile_b": semantic_b,
        "relationship": relationship,
        "summary": relationship.get("relationship_summary", ""),
    }


def synthesize_relationship_interpretation(
    *,
    profile_a: str,
    profile_b: str,
    graph_pattern: str,
    temporal_overlay: str,
    claim: str = "",
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Backward-compatible relationship synthesis API.

    atlas_qa_service currently calls this function. Keep this adapter so
    existing services continue working while synthesis moves toward the
    semantic engine.
    """
    synthesis = synthesize_relationship(
        profile_a=profile_a,
        profile_b=profile_b,
        graph_pattern=graph_pattern or claim,
        temporal_overlay=temporal_overlay,
        evidence=evidence or [],
    )

    semantic_a = synthesis["profile_a"]
    semantic_b = synthesis["profile_b"]
    relationship = synthesis["relationship"]

    return {
        "success": True,
        "version": SYNTHESIS_VERSION,
        "profiles": [profile_a, profile_b],
        "title": f"{humanize(profile_a)} and {humanize(profile_b)}",
        "summary": relationship.get("relationship_summary", ""),
        "profile_a": {
            "name": semantic_a.get("name", humanize(profile_a)),
            "working_classification": semantic_a.get("structural_role", "unknown"),
            "structural_role": semantic_a.get("structural_role", "unknown"),
            "structural_description": semantic_a.get("cognitive_style", ""),
            "likely_expression": semantic_a.get("motivational_style", ""),
            "emotional_style": semantic_a.get("emotional_style", ""),
            "relational_style": semantic_a.get("relational_style", ""),
            "stress_response": semantic_a.get("stress_response", ""),
            "growth_path": semantic_a.get("growth_path", ""),
            "civilization_role": semantic_a.get("civilization_function", "unknown"),
            "probable_behavior": semantic_a.get("probable_behavior", []),
        },
        "profile_b": {
            "name": semantic_b.get("name", humanize(profile_b)),
            "working_classification": semantic_b.get("structural_role", "unknown"),
            "structural_role": semantic_b.get("structural_role", "unknown"),
            "structural_description": semantic_b.get("cognitive_style", ""),
            "likely_expression": semantic_b.get("motivational_style", ""),
            "emotional_style": semantic_b.get("emotional_style", ""),
            "relational_style": semantic_b.get("relational_style", ""),
            "stress_response": semantic_b.get("stress_response", ""),
            "growth_path": semantic_b.get("growth_path", ""),
            "civilization_role": semantic_b.get("civilization_function", "unknown"),
            "probable_behavior": semantic_b.get("probable_behavior", []),
        },
        "structural_relationship": relationship.get("dynamic", ""),
        "temporal_overlay": relationship.get("temporal_interaction", ""),
        "civilization_function": relationship.get("civilization_function", ""),
        "probable_outcomes": relationship.get("probable_outcomes", []),
        "stress_points": relationship.get("stress_points", []),
        "relationship_growth_path": relationship.get("growth_path", ""),
        "evidence": evidence or [],
        "raw": synthesis,
    }


def humanize(profile_key: str) -> str:
    """Humanize profile keys."""
    return str(profile_key).replace("_", " ").title()