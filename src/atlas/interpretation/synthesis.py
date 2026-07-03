"""Atlas interpretation synthesis.

Turns deterministic Atlas outputs into human-readable meaning.

This is the bridge between:
- graph structure
- temporal overlay
- natal/temperamental context
- role classification
- relationship dynamics
- civilization function
"""

from __future__ import annotations

from typing import Any


SYNTHESIS_VERSION = "1.0"


def synthesize_relationship_interpretation(
    *,
    profile_a: str,
    profile_b: str,
    graph_pattern: str,
    temporal_overlay: str,
    claim: str,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Build a rich relationship interpretation."""
    evidence = evidence or []

    role_a = infer_role(profile_a, claim, graph_pattern)
    role_b = infer_role(profile_b, claim, graph_pattern)

    return {
        "success": True,
        "version": SYNTHESIS_VERSION,
        "profiles": [profile_a, profile_b],
        "title": f"{humanize(profile_a)} and {humanize(profile_b)}",
        "summary": build_relationship_summary(
            profile_a=profile_a,
            profile_b=profile_b,
            role_a=role_a,
            role_b=role_b,
        ),
        "profile_a": build_profile_frame(profile_a, role_a),
        "profile_b": build_profile_frame(profile_b, role_b),
        "structural_relationship": build_structural_relationship(
            profile_a=profile_a,
            profile_b=profile_b,
            role_a=role_a,
            role_b=role_b,
            graph_pattern=graph_pattern,
        ),
        "temporal_overlay": build_temporal_overlay_text(temporal_overlay),
        "civilization_function": build_civilization_function(role_a, role_b),
        "probable_outcomes": build_probable_outcomes(role_a, role_b),
        "evidence": evidence[:8],
    }


def infer_role(profile_key: str, claim: str, graph_pattern: str) -> str:
    """Infer a simple Atlas role from known profile patterns and available text."""
    key = profile_key.lower()
    text = f"{claim} {graph_pattern}".lower()

    if "tesla" in key:
        return "Driver-Amplifier"

    if "edison" in key:
        return "Amplifier-Regulator"

    if "limited" in text or "friction" in text:
        return "Contrast Catalyst"

    if "transformation" in text:
        return "Transformation Agent"

    return "Unclassified Structural Actor"


def build_profile_frame(profile_key: str, role: str) -> dict[str, str]:
    """Build individual interpretive frame."""
    name = humanize(profile_key)

    if "Tesla" in name:
        return {
            "name": name,
            "working_classification": role,
            "structural_description": (
                "Tesla reads as a pathway-opening structure. He is less oriented toward "
                "refining an existing machine and more oriented toward discovering the "
                "principle beneath the machine."
            ),
            "likely_expression": (
                "He tends toward abstraction, resonance, invisible systems, long-range "
                "integration, and radical possibility."
            ),
            "civilization_role": "Knowledge Pioneer",
        }

    if "Edison" in name:
        return {
            "name": name,
            "working_classification": role,
            "structural_description": (
                "Edison reads as a system-strengthening structure. He is less oriented "
                "toward pure abstraction and more oriented toward repeatability, production, "
                "and deployment."
            ),
            "likely_expression": (
                "He tends toward iteration, commercialization, infrastructure, organization, "
                "and practical control."
            ),
            "civilization_role": "Institution Builder",
        }

    return {
        "name": name,
        "working_classification": role,
        "structural_description": (
            "Atlas has enough structure to describe a probable operating role, but not "
            "enough specialized interpretation to assign a highly specific archetype yet."
        ),
        "likely_expression": (
            "Behavior should be interpreted through the available graph, temporal, and "
            "natal layers."
        ),
        "civilization_role": "To be resolved",
    }


def build_relationship_summary(
    *,
    profile_a: str,
    profile_b: str,
    role_a: str,
    role_b: str,
) -> str:
    """Build direct summary."""
    return (
        f"{humanize(profile_a)} and {humanize(profile_b)} are best read as complementary "
        f"functions in tension: {role_a} meeting {role_b}. The relationship is not primarily "
        "smooth similarity. It is a pressure field where possibility, execution, control, "
        "and implementation test each other."
    )


def build_structural_relationship(
    *,
    profile_a: str,
    profile_b: str,
    role_a: str,
    role_b: str,
    graph_pattern: str,
) -> str:
    """Describe graph relationship as human interaction."""
    return (
        f"{humanize(profile_a)} appears to open or redirect pathways, while "
        f"{humanize(profile_b)} appears to consolidate, test, and operationalize them. "
        "This explains why the relationship can feel productive and adversarial at the same time. "
        f"Graph signal: {graph_pattern}"
    )


def build_temporal_overlay_text(temporal_overlay: str) -> str:
    """Translate temporal overlay into behavior."""
    return (
        "The temporal layer should be treated as the activation layer. It does not replace "
        "the graph; it shows when the graph becomes louder. Under temporal pressure, each "
        f"person is likely to exaggerate their native role. {temporal_overlay}"
    )


def build_civilization_function(role_a: str, role_b: str) -> str:
    """Describe broader system function."""
    return (
        "At the civilization level, this pairing represents discovery meeting deployment. "
        "One function expands the possible future; the other turns selected possibilities "
        "into infrastructure. Neither function is sufficient alone."
    )


def build_probable_outcomes(role_a: str, role_b: str) -> list[str]:
    """Build likely outcomes."""
    return [
        "High alignment: breakthrough ideas gain practical form.",
        "Moderate stress: implementation pressures constrain vision, while vision destabilizes existing systems.",
        "Low alignment: the relationship becomes a contest over method, credit, authority, or legitimacy.",
        "Growth path: treat the pair as a transformation engine rather than a harmony match.",
    ]


def humanize(profile_key: str) -> str:
    """Humanize profile key."""
    return str(profile_key).replace("_", " ").title()