"""Atlas Semantic Interpretation Engine.

Transforms deterministic Atlas outputs into human-understanding models.
"""

from __future__ import annotations

from typing import Any


SEMANTIC_ENGINE_VERSION = "1.0"


def build_semantic_profile(
    *,
    profile_key: str,
    role: str = "",
    graph_pattern: str = "",
    temporal_overlay: str = "",
    natal_context: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Build a semantic profile from Atlas outputs."""
    natal_context = natal_context or {}
    evidence = evidence or []

    inferred_role = role or infer_role(profile_key, graph_pattern)

    return {
        "success": True,
        "version": SEMANTIC_ENGINE_VERSION,
        "profile_key": profile_key,
        "name": humanize(profile_key),
        "structural_role": inferred_role,
        "cognitive_style": cognitive_style(profile_key, inferred_role),
        "motivational_style": motivational_style(profile_key, inferred_role),
        "emotional_style": emotional_style(profile_key, inferred_role),
        "relational_style": relational_style(profile_key, inferred_role),
        "stress_response": stress_response(profile_key, inferred_role),
        "growth_path": growth_path(profile_key, inferred_role),
        "civilization_function": civilization_function(profile_key, inferred_role),
        "temporal_activation": temporal_activation(temporal_overlay, inferred_role),
        "probable_behavior": probable_behavior(profile_key, inferred_role),
        "evidence": evidence[:8],
    }


def build_semantic_relationship(
    *,
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    graph_pattern: str = "",
    temporal_overlay: str = "",
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Build a semantic relationship interpretation."""
    evidence = evidence or []

    return {
        "success": True,
        "version": SEMANTIC_ENGINE_VERSION,
        "profiles": [
            profile_a.get("name", "Profile A"),
            profile_b.get("name", "Profile B"),
        ],
        "relationship_summary": relationship_summary(profile_a, profile_b),
        "dynamic": relationship_dynamic(profile_a, profile_b, graph_pattern),
        "temporal_interaction": relationship_temporal_overlay(
            profile_a,
            profile_b,
            temporal_overlay,
        ),
        "probable_outcomes": relationship_outcomes(profile_a, profile_b),
        "stress_points": relationship_stress_points(profile_a, profile_b),
        "growth_path": relationship_growth_path(profile_a, profile_b),
        "civilization_function": relationship_civilization_function(profile_a, profile_b),
        "evidence": evidence[:8],
    }


def infer_role(profile_key: str, graph_pattern: str = "") -> str:
    """Infer a semantic role."""
    key = profile_key.lower()
    text = graph_pattern.lower()

    if "tesla" in key:
        return "Driver-Amplifier"

    if "edison" in key:
        return "Amplifier-Regulator"

    if "driver" in text:
        return "Driver"

    if "amplifier" in text:
        return "Amplifier"

    if "regulator" in text:
        return "Regulator"

    if "limited" in text or "friction" in text:
        return "Contrast Catalyst"

    if "transformation" in text:
        return "Transformation Agent"

    return "Unclassified Structural Actor"


def cognitive_style(profile_key: str, role: str) -> str:
    name = humanize(profile_key)

    if "Tesla" in name:
        return (
            "Abstract, field-oriented, and systems-seeking. This mind looks for invisible "
            "principles, long-range patterns, resonance, and possibility before practical closure."
        )

    if "Edison" in name:
        return (
            "Iterative, applied, and optimization-focused. This mind tests, adjusts, repeats, "
            "and converts ideas into usable systems."
        )

    if "Driver" in role:
        return "Initiating and directional. This profile tends to move first and organize later."

    if "Regulator" in role:
        return "Structured and constraint-aware. This profile tends to stabilize before expanding."

    if "Amplifier" in role:
        return "Signal-sensitive and expressive. This profile tends to intensify what is already present."

    return "Not enough deterministic evidence to classify cognitive style with confidence."


def motivational_style(profile_key: str, role: str) -> str:
    name = humanize(profile_key)

    if "Tesla" in name:
        return "Motivated by discovery, hidden order, elegance, and the future implied by unseen forces."

    if "Edison" in name:
        return "Motivated by utility, adoption, proof, productivity, and the conversion of ideas into infrastructure."

    if "Driver" in role:
        return "Motivated by movement, breakthrough, and initiating change."

    if "Regulator" in role:
        return "Motivated by stability, mastery, responsibility, and durability."

    if "Amplifier" in role:
        return "Motivated by expression, resonance, influence, and signal expansion."

    return "Motivation remains provisional until more layers are available."


def emotional_style(profile_key: str, role: str) -> str:
    if "Driver" in role and "Amplifier" in role:
        return (
            "Emotion may intensify around possibility and obstruction. The profile can feel most alive "
            "when opening a new path, and most pressured when constrained too early."
        )

    if "Amplifier" in role and "Regulator" in role:
        return (
            "Emotion may be managed through productivity, structure, and repeatable results. "
            "The profile may prefer proof over ambiguity."
        )

    if "Regulator" in role:
        return "Emotion is often contained through control, pacing, responsibility, and structure."

    if "Amplifier" in role:
        return "Emotion tends to intensify whatever field the person enters."

    return "Emotional style is not yet fully resolved."


def relational_style(profile_key: str, role: str) -> str:
    if "Driver" in role:
        return "Relationally, this profile may push others toward change, even when they are not ready."

    if "Regulator" in role:
        return "Relationally, this profile may stabilize others, but can also feel restrictive under stress."

    if "Amplifier" in role:
        return "Relationally, this profile magnifies shared themes, emotions, ideas, or tensions."

    return "Relational style remains provisional."


def stress_response(profile_key: str, role: str) -> str:
    if "Driver" in role and "Amplifier" in role:
        return "Under stress, this profile may become more radical, impatient, isolated, or visionary."

    if "Amplifier" in role and "Regulator" in role:
        return "Under stress, this profile may become controlling, competitive, overproductive, or dismissive of ambiguity."

    if "Regulator" in role:
        return "Under stress, this profile may tighten, delay, restrict, or over-control."

    if "Amplifier" in role:
        return "Under stress, this profile may intensify emotion, meaning, urgency, or conflict."

    return "Stress response cannot be strongly classified yet."


def growth_path(profile_key: str, role: str) -> str:
    if "Driver" in role and "Amplifier" in role:
        return "Growth comes from grounding vision without killing its originality."

    if "Amplifier" in role and "Regulator" in role:
        return "Growth comes from allowing innovation without reducing everything to utility."

    if "Driver" in role:
        return "Growth comes from learning when to pause, listen, and integrate."

    if "Regulator" in role:
        return "Growth comes from allowing controlled disruption."

    if "Amplifier" in role:
        return "Growth comes from learning what to amplify and what to leave untouched."

    return "Growth path remains provisional."


def civilization_function(profile_key: str, role: str) -> str:
    name = humanize(profile_key)

    if "Tesla" in name:
        return "Knowledge Pioneer: opens conceptual pathways and expands the possible future."

    if "Edison" in name:
        return "Institution Builder: converts selected possibilities into repeatable infrastructure."

    if "Driver" in role:
        return "Catalyst: initiates movement in a system."

    if "Regulator" in role:
        return "Stabilizer: makes systems durable and repeatable."

    if "Amplifier" in role:
        return "Signal Expander: increases reach, meaning, and intensity."

    return "Civilization function unresolved."


def temporal_activation(temporal_overlay: str, role: str) -> str:
    if not temporal_overlay:
        return "No specific temporal overlay is available yet."

    return (
        f"Temporal pressure is interpreted as activation of the native role. For {role}, "
        f"this means the person's default pattern may become louder, more visible, or harder to regulate. "
        f"{temporal_overlay}"
    )


def probable_behavior(profile_key: str, role: str) -> list[str]:
    if "Driver" in role and "Amplifier" in role:
        return [
            "Pursues possibility before consensus.",
            "Sees systems where others see isolated objects.",
            "May resist practical constraints until the vision is clear.",
            "Can inspire major breakthroughs but may struggle with adoption systems.",
        ]

    if "Amplifier" in role and "Regulator" in role:
        return [
            "Tests ideas through repeated application.",
            "Builds systems around what proves useful.",
            "May prefer ownership, scale, and control over open-ended possibility.",
            "Can turn concepts into infrastructure but may constrain disruptive originality.",
        ]

    return [
        "Behavior depends on the active graph, natal, and temporal layers.",
    ]


def relationship_summary(profile_a: dict[str, Any], profile_b: dict[str, Any]) -> str:
    return (
        f"{profile_a.get('name')} and {profile_b.get('name')} represent "
        f"{profile_a.get('structural_role')} meeting {profile_b.get('structural_role')}. "
        "This is a relationship of functional contrast, not simple sameness."
    )


def relationship_dynamic(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    graph_pattern: str,
) -> str:
    return (
        f"{profile_a.get('name')} tends to express: {profile_a.get('cognitive_style')} "
        f"{profile_b.get('name')} tends to express: {profile_b.get('cognitive_style')} "
        "Together, the interaction produces a field where possibility and implementation test each other. "
        f"Graph context: {graph_pattern}"
    )


def relationship_temporal_overlay(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    temporal_overlay: str,
) -> str:
    return (
        "The temporal overlay shows when the relationship pattern becomes active. "
        "Under pressure, each person is likely to exaggerate their native role: "
        f"{profile_a.get('name')} intensifies as {profile_a.get('structural_role')}, while "
        f"{profile_b.get('name')} intensifies as {profile_b.get('structural_role')}. "
        f"{temporal_overlay}"
    )


def relationship_outcomes(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> list[str]:
    return [
        "High alignment: vision gains implementation and implementation gains originality.",
        "Moderate stress: one side feels constrained while the other feels destabilized.",
        "Low alignment: the relationship becomes a contest over method, credit, authority, or control.",
        "Best path: treat the contrast as a transformation engine rather than forcing harmony.",
    ]


def relationship_stress_points(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> list[str]:
    return [
        "Different definitions of success.",
        "Different tolerance for ambiguity.",
        "Different relationship to ownership, proof, and timing.",
        "Different pacing between vision and implementation.",
    ]


def relationship_growth_path(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> str:
    return (
        "Growth comes from recognizing that the relationship is not meant to erase difference. "
        "It works best when one function opens possibility and the other function gives it form."
    )


def relationship_civilization_function(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
) -> str:
    return (
        "At the civilization level, this relationship represents discovery meeting deployment. "
        "One role expands the future; the other turns selected futures into infrastructure."
    )


def humanize(profile_key: str) -> str:
    return str(profile_key).replace("_", " ").title()