"""Reusable Atlas profile view."""

from __future__ import annotations

from typing import Any

import streamlit as st

from dashboard.ui.cards import (
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
        ("Topology Intelligence", profile.get("topology_intelligence", "")),
        ("Resonance Intelligence", profile.get("resonance_intelligence", "")),
        ("Structural Fingerprint", profile.get("fingerprint_intelligence", "")),
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
    topology = payload.get("topology", {})
    resonance = payload.get("resonance", {})
    fingerprint = payload.get("fingerprint", {})
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

    semantic_source = (
        semantic
        or payload.get("synthesis", {}).get("semantic", {})
        or payload.get("data", {}).get("synthesis", {}).get("semantic", {})
        or payload.get("reasoning", {}).get("synthesis", {}).get("semantic", {})
    )

    role = (
        semantic_source.get("structural_role")
        or semantic_source.get("role")
        or payload.get("role", "")
        or infer_role_from_payload(payload)
        or "unresolved"
    )

    civilization_role = (
        semantic_source.get("civilization_function")
        or semantic_source.get("function")
        or payload.get("civilization_role", "")
        or infer_civilization_function(payload)
        or "unresolved"
    )

    summary = (
        summary_payload.get("summary")
        or payload.get("summary")
        or semantic_source.get("cognitive_style", "")
        or lifecycle.get("human_summary")
        or ""
    )

    # Avoid duplicating the full QA markdown answer when semantic synthesis exists.
    if not summary and not semantic_source:
        summary = payload.get("answer", "")

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
        "structural_intelligence": semantic_source.get("cognitive_style", ""),
        "human_interpretation": build_human_interpretation(semantic_source),
        "topology_intelligence": build_topology_intelligence(topology),
        "resonance_intelligence": build_resonance_intelligence(resonance),
        "fingerprint_intelligence": build_fingerprint_intelligence(fingerprint),
        "vedic_behavior": payload.get("vedic_behavior", ""),
        "temporal_outlook": temporal_outlook or semantic_source.get("temporal_activation", ""),
        "civilization_function": civilization_role,
        "stress_pattern": semantic_source.get("stress_response", ""),
        "growth_path": semantic_source.get("growth_path", ""),
        "evidence": evidence if isinstance(evidence, list) else semantic_source.get("evidence", []),
        "metrics": payload.get("metrics", {}),
        "lifecycle": lifecycle,
    }


def build_topology_intelligence(topology: dict[str, Any]) -> str:
    """Build readable topology section."""
    if not isinstance(topology, dict) or topology.get("status") != "compiled":
        return ""

    parts = [
        f"Topology class: **{topology.get('topology_class', 'n/a')}**",
        f"Dominant topology axis: **{topology.get('dominant_topology_axis', 'n/a')}**",
        f"Dominant motif: **{topology.get('dominant_motif', 'n/a')}**",
        f"Motif count: **{topology.get('motif_count', 0)}**",
    ]

    summary = topology.get("summary", {})
    if isinstance(summary, dict):
        flow = summary.get("flow_pattern")
        organization = summary.get("organization_pattern")
        stability = summary.get("stability_pattern")

        if flow:
            parts.append(f"Flow pattern: **{flow}**")
        if organization:
            parts.append(f"Organization pattern: **{organization}**")
        if stability:
            parts.append(f"Stability pattern: **{stability}**")

    return "\n\n".join(parts)


def build_resonance_intelligence(resonance: dict[str, Any]) -> str:
    """Build readable resonance section."""
    if not isinstance(resonance, dict) or resonance.get("status") != "compiled":
        return ""

    parts = [
        f"Resonance class: **{resonance.get('resonance_class', 'n/a')}**",
        f"Dominant resonance axis: **{resonance.get('dominant_resonance_axis', 'n/a')}**",
    ]

    summary = resonance.get("summary", {})
    if isinstance(summary, dict):
        for label, key in [
            ("Activation pattern", "activation_pattern"),
            ("Propagation pattern", "propagation_pattern"),
            ("Damping pattern", "damping_pattern"),
        ]:
            value = summary.get(key)
            if value:
                parts.append(f"{label}: **{value}**")

    return "\n\n".join(parts)


def build_fingerprint_intelligence(fingerprint: dict[str, Any]) -> str:
    """Build readable fingerprint section."""
    if not isinstance(fingerprint, dict) or fingerprint.get("status") != "compiled":
        return ""

    summary = fingerprint.get("summary", {})
    if not isinstance(summary, dict):
        return ""

    parts = [
        f"CIG nodes: **{summary.get('cig_nodes', 0)}**",
        f"CIG edges: **{summary.get('cig_edges', 0)}**",
        f"STG nodes: **{summary.get('stg_nodes', 0)}**",
        f"STG edges: **{summary.get('stg_edges', 0)}**",
        f"Topology class: **{summary.get('topology_class', 'n/a')}**",
        f"Resonance class: **{summary.get('resonance_class', 'n/a')}**",
    ]

    return "\n\n".join(parts)


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
