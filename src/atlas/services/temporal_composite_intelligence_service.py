"""Temporal Composite Intelligence Service.

Combines semantic profile interpretation, Vedic behavior, graph structure,
and temporal activation into human-readable future-facing intelligence.

This service does not calculate charts or transits directly. It interprets
available profile, relationship, graph, natal, Vedic, and temporal payloads.
"""

from __future__ import annotations

from typing import Any

from atlas.interpretation import (
    build_semantic_profile,
    build_semantic_relationship,
    interpret_vedic_behavior,
)


TEMPORAL_COMPOSITE_INTELLIGENCE_VERSION = "1.0"


def build_temporal_composite_intelligence(
    *,
    profiles: list[str],
    date_window: str = "",
    graph_payload: dict[str, Any] | None = None,
    temporal_payloads: dict[str, dict[str, Any]] | None = None,
    natal_payloads: dict[str, dict[str, Any]] | None = None,
    relationship_payload: dict[str, Any] | None = None,
    evidence: list[str] | None = None,
) -> dict[str, Any]:
    """Build temporal composite intelligence for one or more profiles."""
    graph_payload = graph_payload or {}
    temporal_payloads = temporal_payloads or {}
    natal_payloads = natal_payloads or {}
    relationship_payload = relationship_payload or {}
    evidence = evidence or []

    clean_profiles = [profile for profile in profiles if profile]

    semantic_profiles = [
        build_profile_state(
            profile_key=profile,
            date_window=date_window,
            graph_payload=graph_payload,
            natal_payload=natal_payloads.get(profile, {}),
            temporal_payload=temporal_payloads.get(profile, {}),
            evidence=evidence,
        )
        for profile in clean_profiles
    ]

    composite = build_composite_state(
        semantic_profiles=semantic_profiles,
        date_window=date_window,
        graph_payload=graph_payload,
        relationship_payload=relationship_payload,
        evidence=evidence,
    )

    return {
        "success": True,
        "version": TEMPORAL_COMPOSITE_INTELLIGENCE_VERSION,
        "date_window": date_window or "unspecified",
        "profiles": clean_profiles,
        "profile_states": semantic_profiles,
        "composite": composite,
        "human_summary": compose_human_summary(composite),
        "probable_outcomes": composite.get("probable_outcomes", []),
        "stress_points": composite.get("stress_points", []),
        "supportive_conditions": composite.get("supportive_conditions", []),
        "timing_cautions": composite.get("timing_cautions", []),
        "confidence": resolve_confidence(
            profiles=clean_profiles,
            natal_payloads=natal_payloads,
            temporal_payloads=temporal_payloads,
            graph_payload=graph_payload,
        ),
        "missing_requirements": missing_requirements(
            profiles=clean_profiles,
            natal_payloads=natal_payloads,
            temporal_payloads=temporal_payloads,
            graph_payload=graph_payload,
        ),
        "evidence": evidence[:10],
    }


def build_profile_state(
    *,
    profile_key: str,
    date_window: str,
    graph_payload: dict[str, Any],
    natal_payload: dict[str, Any],
    temporal_payload: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build one profile's temporal-semantic state."""
    graph_pattern = extract_graph_pattern(graph_payload, profile_key)
    temporal_overlay = extract_temporal_overlay(temporal_payload, date_window)

    semantic = build_semantic_profile(
        profile_key=profile_key,
        graph_pattern=graph_pattern,
        temporal_overlay=temporal_overlay,
        natal_context=natal_payload,
        evidence=evidence,
    )

    vedic = interpret_vedic_behavior(
        profile_key=profile_key,
        natal_payload=natal_payload,
        temporal_payload=temporal_payload,
    )

    return {
        "profile_key": profile_key,
        "name": humanize(profile_key),
        "date_window": date_window or "unspecified",
        "semantic": semantic,
        "vedic_behavior": vedic,
        "graph_pattern": graph_pattern,
        "temporal_overlay": temporal_overlay,
        "activated_role": semantic.get("structural_role", "unknown"),
        "likely_behavior": build_likely_behavior(semantic, vedic),
        "stress_response": build_temporal_stress_response(semantic, vedic),
        "growth_path": build_temporal_growth_path(semantic, vedic),
    }


def build_composite_state(
    *,
    semantic_profiles: list[dict[str, Any]],
    date_window: str,
    graph_payload: dict[str, Any],
    relationship_payload: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build group or relationship temporal composite state."""
    if len(semantic_profiles) == 1:
        return build_single_composite(
            profile_state=semantic_profiles[0],
            date_window=date_window,
            evidence=evidence,
        )

    if len(semantic_profiles) == 2:
        return build_relationship_composite(
            profile_a=semantic_profiles[0],
            profile_b=semantic_profiles[1],
            date_window=date_window,
            graph_payload=graph_payload,
            relationship_payload=relationship_payload,
            evidence=evidence,
        )

    return build_group_composite(
        profile_states=semantic_profiles,
        date_window=date_window,
        graph_payload=graph_payload,
        evidence=evidence,
    )


def build_single_composite(
    *,
    profile_state: dict[str, Any],
    date_window: str,
    evidence: list[str],
) -> dict[str, Any]:
    """Build single-profile temporal composite."""
    semantic = profile_state.get("semantic", {})
    vedic = profile_state.get("vedic_behavior", {})

    return {
        "kind": "single_profile",
        "title": f"{profile_state.get('name')} temporal state",
        "date_window": date_window or "unspecified",
        "structural_baseline": semantic.get("structural_role", "unknown"),
        "temporal_activation": semantic.get("temporal_activation", ""),
        "vedic_behavior": vedic.get("behavioral_summary", ""),
        "human_interpretation": (
            f"{profile_state.get('name')} should be read as a baseline structure entering "
            "a temporary activation window. The graph shows the repeating pattern, the Vedic "
            "layer explains behavioral style, and the temporal layer shows which parts of the "
            "pattern are likely to become louder."
        ),
        "probable_outcomes": [
            "Supportive timing: the profile expresses its native role with more clarity.",
            "Stress timing: the profile exaggerates its default defenses or pressure patterns.",
            "Growth timing: the person can consciously redirect the activated pattern.",
        ],
        "stress_points": [profile_state.get("stress_response", "")],
        "supportive_conditions": [profile_state.get("growth_path", "")],
        "timing_cautions": [
            "Precise timing requires verified natal data and current transit/dasha payloads.",
        ],
        "evidence": evidence[:8],
    }


def build_relationship_composite(
    *,
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    date_window: str,
    graph_payload: dict[str, Any],
    relationship_payload: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build two-profile temporal composite."""
    semantic_a = profile_a.get("semantic", {})
    semantic_b = profile_b.get("semantic", {})

    relationship = build_semantic_relationship(
        profile_a=semantic_a,
        profile_b=semantic_b,
        graph_pattern=extract_relationship_graph_pattern(graph_payload, relationship_payload),
        temporal_overlay=extract_relationship_temporal_overlay(profile_a, profile_b, date_window),
        evidence=evidence,
    )

    return {
        "kind": "relationship",
        "title": f"{profile_a.get('name')} ↔ {profile_b.get('name')}",
        "date_window": date_window or "unspecified",
        "relationship": relationship,
        "structural_baseline": relationship.get("relationship_summary", ""),
        "temporal_activation": relationship.get("temporal_interaction", ""),
        "human_interpretation": (
            f"During {date_window or 'the selected window'}, {profile_a.get('name')} and "
            f"{profile_b.get('name')} should be read as two activated systems interacting. "
            "The graph shows their baseline fit or friction. The Vedic layer describes how each "
            "person behaves under pressure. The temporal layer shows when those behaviors become "
            "more visible. The likely outcome depends on whether their activated roles reinforce, "
            "stabilize, or provoke each other."
        ),
        "probable_outcomes": relationship.get("probable_outcomes", []),
        "stress_points": relationship.get("stress_points", []),
        "supportive_conditions": [
            relationship.get("growth_path", ""),
            "Name the active roles consciously instead of treating the pressure as random.",
        ],
        "timing_cautions": [
            "Relationship timing requires verified birth metadata for both profiles.",
            "If one profile has missing temporal payloads, the composite should remain provisional.",
        ],
        "evidence": evidence[:8],
    }


def build_group_composite(
    *,
    profile_states: list[dict[str, Any]],
    date_window: str,
    graph_payload: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build group/founding/civilization temporal composite."""
    names = [profile.get("name", "Unknown") for profile in profile_states]
    roles = [
        profile.get("semantic", {}).get("structural_role", "unknown")
        for profile in profile_states
    ]

    return {
        "kind": "group_or_civilization",
        "title": "Composite temporal field",
        "date_window": date_window or "unspecified",
        "members": names,
        "roles": roles,
        "structural_baseline": build_group_baseline(names, roles),
        "temporal_activation": (
            "The group should be read as a composite field. During the selected window, "
            "each member's activated temporal state contributes pressure to the larger system."
        ),
        "human_interpretation": (
            "A founding group or civilization can be modeled as a composite of its influential "
            "members. Drivers push the system into motion, Amplifiers spread signal and meaning, "
            "Regulators stabilize institutions, and Catalyst roles introduce mutation. The temporal "
            "overlay shows which parts of the founding field become active at a given time."
        ),
        "probable_outcomes": build_group_outcomes(roles),
        "stress_points": build_group_stress_points(roles),
        "supportive_conditions": build_group_supportive_conditions(roles),
        "timing_cautions": [
            "Group forecasts require complete member metadata and a defined founding/event date.",
            "Civilization-scale interpretation should remain scenario-based, not deterministic.",
        ],
        "evidence": evidence[:8],
    }


def build_likely_behavior(
    semantic: dict[str, Any],
    vedic: dict[str, Any],
) -> str:
    """Combine semantic and Vedic behavior."""
    behavior = semantic.get("probable_behavior", [])
    active = vedic.get("active_temporal_state", "")

    if behavior:
        return f"{' '.join(behavior[:2])} {active}".strip()

    return active or "Likely behavior remains provisional."


def build_temporal_stress_response(
    semantic: dict[str, Any],
    vedic: dict[str, Any],
) -> str:
    """Combine stress patterns."""
    return " ".join(
        item
        for item in [
            semantic.get("stress_response", ""),
            vedic.get("stress_behavior", ""),
        ]
        if item
    ) or "Stress response remains provisional."


def build_temporal_growth_path(
    semantic: dict[str, Any],
    vedic: dict[str, Any],
) -> str:
    """Combine growth patterns."""
    return " ".join(
        item
        for item in [
            semantic.get("growth_path", ""),
            vedic.get("growth_path", ""),
        ]
        if item
    ) or "Growth path remains provisional."


def build_group_baseline(names: list[str], roles: list[str]) -> str:
    """Describe group baseline."""
    return (
        f"The composite includes {len(names)} profiles. Its baseline field is shaped by "
        f"the role distribution: {', '.join(roles)}."
    )


def build_group_outcomes(roles: list[str]) -> list[str]:
    """Build group outcomes."""
    outcomes = [
        "High alignment: roles differentiate cleanly and the group becomes more coherent.",
        "Moderate stress: Drivers accelerate faster than Regulators can stabilize.",
        "Low alignment: Amplifiers spread unresolved pressure through the whole field.",
    ]

    if any("Driver" in role for role in roles) and any("Regulator" in role for role in roles):
        outcomes.append(
            "Best case: Driver energy creates movement while Regulator energy builds durability."
        )

    return outcomes


def build_group_stress_points(roles: list[str]) -> list[str]:
    """Build group stress points."""
    stress = [
        "Conflicting definitions of success.",
        "Different pacing between vision, adoption, and institutionalization.",
        "Role confusion under pressure.",
    ]

    if roles.count("unknown") or any(role == "unknown" for role in roles):
        stress.append("Some member roles are unresolved, reducing confidence.")

    return stress


def build_group_supportive_conditions(roles: list[str]) -> list[str]:
    """Build group supportive conditions."""
    return [
        "Clear role differentiation.",
        "Shared timing awareness.",
        "Enough structure to contain Driver pressure.",
        "Enough flexibility to prevent Regulator rigidity.",
    ]


def compose_human_summary(composite: dict[str, Any]) -> str:
    """Compose short human-facing summary."""
    return (
        f"{composite.get('title', 'Temporal composite')} — "
        f"{composite.get('human_interpretation', '')}"
    )


def extract_graph_pattern(
    graph_payload: dict[str, Any],
    profile_key: str,
) -> str:
    """Extract profile graph pattern from flexible payloads."""
    if not graph_payload:
        return ""

    profile_graph = graph_payload.get(profile_key, {})
    if isinstance(profile_graph, dict):
        for key in ("summary", "graph_pattern", "structural_pattern", "morphology"):
            value = profile_graph.get(key)
            if value:
                return str(value)

    for key in ("summary", "graph_pattern", "structural_pattern", "morphology"):
        value = graph_payload.get(key)
        if value:
            return str(value)

    return ""


def extract_relationship_graph_pattern(
    graph_payload: dict[str, Any],
    relationship_payload: dict[str, Any],
) -> str:
    """Extract relationship graph pattern."""
    for payload in (relationship_payload, graph_payload):
        for key in ("summary", "graph_pattern", "structural_pattern", "relationship_graph"):
            value = payload.get(key)
            if value:
                return str(value)

    return "Relationship graph pattern is available only provisionally."


def extract_temporal_overlay(
    temporal_payload: dict[str, Any],
    date_window: str,
) -> str:
    """Extract temporal overlay text."""
    if not temporal_payload:
        return (
            f"No explicit temporal payload is available for {date_window or 'the selected window'}."
        )

    for key in ("summary", "temporal_overlay", "active_state", "transit_summary"):
        value = temporal_payload.get(key)
        if value:
            return str(value)

    return f"Temporal payload is available for {date_window or 'the selected window'}."


def extract_relationship_temporal_overlay(
    profile_a: dict[str, Any],
    profile_b: dict[str, Any],
    date_window: str,
) -> str:
    """Build relationship temporal overlay."""
    return (
        f"During {date_window or 'the selected window'}, "
        f"{profile_a.get('name')} activates as {profile_a.get('activated_role')}, while "
        f"{profile_b.get('name')} activates as {profile_b.get('activated_role')}."
    )


def resolve_confidence(
    *,
    profiles: list[str],
    natal_payloads: dict[str, dict[str, Any]],
    temporal_payloads: dict[str, dict[str, Any]],
    graph_payload: dict[str, Any],
) -> str:
    """Resolve confidence."""
    if not profiles:
        return "none"

    natal_count = sum(1 for profile in profiles if natal_payloads.get(profile))
    temporal_count = sum(1 for profile in profiles if temporal_payloads.get(profile))
    has_graph = bool(graph_payload)

    if natal_count == len(profiles) and temporal_count == len(profiles) and has_graph:
        return "high"

    if natal_count and temporal_count:
        return "moderate"

    if natal_count or temporal_count or has_graph:
        return "low-moderate"

    return "provisional"


def missing_requirements(
    *,
    profiles: list[str],
    natal_payloads: dict[str, dict[str, Any]],
    temporal_payloads: dict[str, dict[str, Any]],
    graph_payload: dict[str, Any],
) -> list[str]:
    """List missing requirements."""
    missing: list[str] = []

    if not graph_payload:
        missing.append("graph_payload")

    for profile in profiles:
        if not natal_payloads.get(profile):
            missing.append(f"{profile}: natal_payload")

        if not temporal_payloads.get(profile):
            missing.append(f"{profile}: temporal_payload")

    return missing


def humanize(profile_key: str) -> str:
    """Humanize profile keys."""
    return str(profile_key).replace("_", " ").title()