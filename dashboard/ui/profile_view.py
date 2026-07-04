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

    # Canonical profile.payload.json support.
    identity = payload.get("identity", {})
    lifecycle = payload.get("lifecycle", {})
    temporal = payload.get("temporal", {})
    interpretation = payload.get("interpretation", {})
    summary_payload = payload.get("summary", {})

    if not semantic and isinstance(interpretation, dict):
        semantic = interpretation.get("semantic", {}) or {}

    evidence = payload.get("evidence", [])
    if not evidence and isinstance(semantic, dict):
        evidence = semantic.get("evidence", [])

    name = (
        semantic.get("name")
        or identity.get("display_name")
        or identity.get("full_name")
        or summary_payload.get("name")
        or payload.get("name")
        or payload.get("profile_key")
        or first(payload.get("profiles", []))
        or "Unknown Profile"
    )

    role = (
        semantic.get("structural_role")
        or payload.get("role", "")
        or infer_role_from_payload(payload)
    )

    civilization_role = (
        semantic.get("civilization_function")
        or payload.get("civilization_role", "")
        or infer_civilization_function(payload)
    )

    summary = (
        payload.get("answer")
        or summary_payload.get("summary")
        or payload.get("summary")
        or lifecycle.get("human_summary")
        or semantic.get("cognitive_style")
        or ""
    )

    temporal_outlook = (
        semantic.get("temporal_activation", "")
        or temporal.get("runtime", {}).get("temporal_status", "")
        or lifecycle.get("human_summary", "")
    )

    return {
        "name": humanize(str(name)),
        "role": role,
        "civilization_role": civilization_role,
        "confidence": payload.get("confidence", ""),
        "summary": clean_summary(str(summary)),
        "structural_intelligence": semantic.get("cognitive_style", ""),
        "human_interpretation": build_human_interpretation(semantic),
        "vedic_behavior": payload.get("vedic_behavior", ""),
        "temporal_outlook": temporal_outlook,
        "civilization_function": civilization_role,
        "stress_pattern": semantic.get("stress_response", ""),
        "growth_path": semantic.get("growth_path", ""),
        "evidence": evidence if isinstance(evidence, list) else [],
        "metrics": payload.get("metrics", {}),
        "lifecycle": lifecycle,
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


def infer_role_from_payload(payload: dict[str, Any]) -> str:
    """Infer role from canonical payload when semantic role is unavailable."""
    graph = payload.get("graph", {})
    topology = graph.get("topology", {}) if isinstance(graph, dict) else {}

    for key in ("role", "structural_role", "classification", "topology_class"):
        value = topology.get(key)
        if value:
            return str(value)

    return ""


def infer_civilization_function(payload: dict[str, Any]) -> str:
    """Infer civilization function from payload when available."""
    interpretation = payload.get("interpretation", {})

    if isinstance(interpretation, dict):
        value = interpretation.get("civilization_function")
        if value:
            return str(value)

    return ""
