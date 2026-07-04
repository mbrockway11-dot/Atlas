"""Reusable Atlas profile view."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.cards import (
    executive_summary_card,
    evidence_card,
    raw_payload_card,
)
from dashboard.ui.layout import hero_panel, divider
from dashboard.ui.metrics import metric_grid


def render_profile_view(payload: dict[str, Any]) -> None:
    """Render a canonical Atlas profile dossier."""
    profile = resolve_profile_payload(payload)

    name = profile.get("name", "Unknown Profile")
    role = profile.get("role", "")
    civilization_role = profile.get("civilization_role", "")
    confidence = profile.get("confidence", "")
    summary = profile.get("summary", "")

    hero_panel(
        title=name,
        subtitle="Atlas Profile Dossier",
        body=summary,
        metrics={
            "Role": role or "unresolved",
            "Function": civilization_role or "unresolved",
            "Confidence": confidence or "unknown",
        },
    )

    executive_summary_card(
        title=name,
        role=role,
        civilization_role=civilization_role,
        confidence=confidence,
        summary=summary,
    )

    render_profile_sections(profile)

    evidence_card(
        evidence=profile.get("evidence", []),
        expanded=False,
    )

    raw_payload_card(
        payload=payload,
        expanded=False,
    )


def render_profile_sections(profile: dict[str, Any]) -> None:
    """Render profile interpretation sections."""
    sections = [
        ("Structural Intelligence", profile.get("structural_intelligence", "")),
        ("Human Interpretation", profile.get("human_interpretation", "")),
        ("Vedic / Natal Behavior", profile.get("vedic_behavior", "")),
        ("Temporal Outlook", profile.get("temporal_outlook", "")),
        ("Civilization Function", profile.get("civilization_function", "")),
        ("Stress Pattern", profile.get("stress_pattern", "")),
        ("Growth Path", profile.get("growth_path", "")),
    ]

    for title, body in sections:
        if body:
            divider(title)
            st.markdown(body)

    metrics = profile.get("metrics", {})
    if metrics:
        divider("Layer Metrics")
        metric_grid(metrics)


def resolve_profile_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize multiple Atlas payload shapes into profile view data."""
    synthesis = payload.get("synthesis", {})
    semantic = synthesis.get("semantic", {})

    if not semantic and "semantic" in payload:
        semantic = payload.get("semantic", {})

    evidence = payload.get("evidence", [])
    if not evidence and isinstance(semantic, dict):
        evidence = semantic.get("evidence", [])

    name = (
        semantic.get("name")
        or payload.get("name")
        or payload.get("profile_key")
        or first(payload.get("profiles", []))
        or "Unknown Profile"
    )

    role = semantic.get("structural_role") or payload.get("role", "")
    civilization_role = (
        semantic.get("civilization_function")
        or payload.get("civilization_role", "")
    )

    summary = (
        payload.get("answer")
        or payload.get("summary")
        or semantic.get("cognitive_style")
        or ""
    )

    return {
        "name": humanize(str(name)),
        "role": role,
        "civilization_role": civilization_role,
        "confidence": payload.get("confidence", ""),
        "summary": clean_summary(summary),
        "structural_intelligence": semantic.get("cognitive_style", ""),
        "human_interpretation": build_human_interpretation(semantic),
        "vedic_behavior": payload.get("vedic_behavior", ""),
        "temporal_outlook": semantic.get("temporal_activation", ""),
        "civilization_function": civilization_role,
        "stress_pattern": semantic.get("stress_response", ""),
        "growth_path": semantic.get("growth_path", ""),
        "evidence": evidence if isinstance(evidence, list) else [],
        "metrics": payload.get("metrics", {}),
    }


def build_human_interpretation(semantic: dict[str, Any]) -> str:
    """Build readable interpretation from semantic fields."""
    parts = [
        semantic.get("motivational_style", ""),
        semantic.get("emotional_style", ""),
        semantic.get("relational_style", ""),
    ]

    return "\n\n".join(part for part in parts if part)


def clean_summary(value: str) -> str:
    """Clean long markdown answer into shorter summary text."""
    text = str(value or "").strip()

    if not text:
        return ""

    if "### Evidence" in text:
        text = text.split("### Evidence", 1)[0].strip()

    return text


def first(values: Any) -> Any:
    """Return first item from list-like value."""
    if isinstance(values, list) and values:
        return values[0]
    return None


def humanize(value: str) -> str:
    """Humanize profile keys."""
    return str(value).replace("_", " ").title()
