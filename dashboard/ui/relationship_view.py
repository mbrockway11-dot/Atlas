"""Reusable Atlas relationship view."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.cards import evidence_card, raw_payload_card, relationship_card
from dashboard.ui.layout import divider, hero_panel
from dashboard.ui.metrics import metric_grid


def render_relationship_view(payload: dict[str, Any]) -> None:
    """Render a canonical Atlas relationship dossier."""
    relationship = resolve_relationship_payload(payload)

    hero_panel(
        title=relationship.get("title", "Relationship Dossier"),
        subtitle="Atlas Relationship Intelligence",
        body=relationship.get("summary", ""),
        metrics={
            "Profile A": relationship.get("profile_a", "unknown"),
            "Profile B": relationship.get("profile_b", "unknown"),
            "Confidence": relationship.get("confidence", "unknown"),
        },
    )

    relationship_card(
        profile_a=relationship.get("profile_a", "Profile A"),
        profile_b=relationship.get("profile_b", "Profile B"),
        summary=relationship.get("summary", ""),
        dynamic=relationship.get("dynamic", ""),
        confidence=relationship.get("confidence", ""),
    )

    render_relationship_sections(relationship)

    evidence_card(
        evidence=relationship.get("evidence", []),
        expanded=False,
    )

    raw_payload_card(
        payload=payload,
        title="Raw Relationship Payload",
        expanded=False,
    )


def render_relationship_sections(relationship: dict[str, Any]) -> None:
    """Render relationship sections."""
    sections = [
        ("Profile A", relationship.get("profile_a_summary", "")),
        ("Profile B", relationship.get("profile_b_summary", "")),
        ("Structural Dynamic", relationship.get("dynamic", "")),
        ("Temporal Interaction", relationship.get("temporal_interaction", "")),
        ("Civilization Function", relationship.get("civilization_function", "")),
        ("Stress Points", format_list(relationship.get("stress_points", []))),
        ("Probable Outcomes", format_list(relationship.get("probable_outcomes", []))),
        ("Growth Path", relationship.get("growth_path", "")),
    ]

    for title, body in sections:
        if body:
            divider(title)
            st.markdown(body)

    metrics = relationship.get("metrics", {})
    if metrics:
        divider("Layer Metrics")
        metric_grid(metrics)


def resolve_relationship_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize Atlas payload shapes into relationship view data."""
    synthesis = payload.get("synthesis", {})
    relationship = synthesis.get("relationship", {})

    profiles = payload.get("profiles") or synthesis.get("profiles") or []
    profile_a = synthesis.get("profile_a", {})
    profile_b = synthesis.get("profile_b", {})

    name_a = (
        profile_a.get("name")
        or first(profiles)
        or "Profile A"
    )
    name_b = (
        profile_b.get("name")
        or second(profiles)
        or "Profile B"
    )

    summary = (
        relationship.get("relationship_summary")
        or synthesis.get("summary")
        or payload.get("claim")
        or ""
    )

    evidence = payload.get("evidence", [])
    if not evidence:
        evidence = relationship.get("evidence", [])

    return {
        "title": f"{humanize(str(name_a))} ? {humanize(str(name_b))}",
        "profile_a": humanize(str(name_a)),
        "profile_b": humanize(str(name_b)),
        "profile_a_summary": summarize_profile(profile_a),
        "profile_b_summary": summarize_profile(profile_b),
        "summary": summary,
        "dynamic": relationship.get("dynamic", ""),
        "temporal_interaction": relationship.get("temporal_interaction", ""),
        "civilization_function": relationship.get("civilization_function", ""),
        "stress_points": relationship.get("stress_points", []),
        "probable_outcomes": relationship.get("probable_outcomes", []),
        "growth_path": relationship.get("growth_path", ""),
        "confidence": payload.get("confidence", ""),
        "evidence": evidence if isinstance(evidence, list) else [],
        "metrics": payload.get("metrics", {}),
    }


def summarize_profile(profile: dict[str, Any]) -> str:
    """Summarize a relationship participant."""
    if not isinstance(profile, dict) or not profile:
        return ""

    name = profile.get("name", "Profile")
    role = profile.get("structural_role", "unresolved")
    cognition = profile.get("cognitive_style", "")
    motivation = profile.get("motivational_style", "")
    civilization = profile.get("civilization_function", "")

    return f"""**{name}**  
Role: **{role}**

{cognition}

{motivation}

{civilization}
""".strip()


def format_list(items: Any) -> str:
    """Format a list as markdown."""
    if not isinstance(items, list) or not items:
        return ""

    return "\n".join(f"- {item}" for item in items if item)


def first(values: Any) -> Any:
    """Return first item from list-like value."""
    if isinstance(values, list) and values:
        return values[0]
    return None


def second(values: Any) -> Any:
    """Return second item from list-like value."""
    if isinstance(values, list) and len(values) > 1:
        return values[1]
    return None


def humanize(value: str) -> str:
    """Humanize profile keys."""
    return str(value).replace("_", " ").title()
