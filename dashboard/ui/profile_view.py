"""Reusable Atlas canonical profile dossier view."""

from __future__ import annotations

from typing import Any

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile

import streamlit as st

from dashboard.ui.cards import evidence_card
from dashboard.ui.layout import divider, hero_panel
from dashboard.ui.metrics import metric_grid
from dashboard.ui.components.executive_summary import render_executive_summary
from dashboard.ui.components.classification_card import render_classification_card
from dashboard.ui.components.vedic_section import render_vedic_section
from dashboard.ui.dossier.semantic_section import render_semantic_section


def render_profile_view(payload: dict[str, Any]) -> None:
    """Render a full canonical Atlas profile dossier."""
    canonical = resolve_canonical_payload(payload)

    identity = canonical.get("identity", {})
    classification = canonical.get("classification", {})
    metrics = canonical.get("metrics", {})

    name = (
        identity.get("display_name")
        or identity.get("name")
        or canonical.get("profile_key")
        or "Unknown Profile"
    )

    role = classification.get("structural_role", "unresolved")
    function = classification.get("civilization_function", "unresolved")
    confidence = format_confidence(classification.get("confidence"))

    hero_panel(
        title=humanize(str(name)),
        subtitle="Atlas Canonical Profile Dossier",
        body=classification.get("cognitive_style", "") or build_executive_summary(canonical),
        metrics={
            "Role": role,
            "Function": function,
            "Confidence": confidence,
        },
    )

    render_executive_summary(canonical)

    render_semantic_section(canonical)

    render_identity_section(canonical)
    render_classification_card(canonical)
    render_vedic_section(canonical)
    render_temporal_section(canonical)
    render_graph_section(canonical)
    render_topology_section(canonical)
    render_resonance_section(canonical)
    render_fingerprint_section(canonical)
    render_diagnostics_section(canonical)

    evidence = canonical.get("evidence", [])
    if evidence:
        evidence_card(evidence=evidence, expanded=False)

    if metrics:
        divider("Layer Metrics")
        metric_grid(metrics)
def resolve_canonical_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Resolve canonical payload from direct payload, Atlas AI, QA, or profile key."""
    if "identity" in payload and "classification" in payload:
        return payload

    # Atlas AI direct wrapper.
    services = payload.get("data", {}).get("services", {})
    profile_report = services.get("profile_report", {})
    data = profile_report.get("data", {})
    if isinstance(data, dict) and "identity" in data and "classification" in data:
        return data

    # QA / reasoning wrapper.
    reasoning = payload.get("reasoning", {})
    services = reasoning.get("data", {}).get("services", {})
    profile_report = services.get("profile_report", {})
    data = profile_report.get("data", {})
    if isinstance(data, dict) and "identity" in data and "classification" in data:
        return data

    # If this is a question-answer payload, compile the detected profile directly.
    profile_key = resolve_profile_key(payload)
    if profile_key:
        try:
            compiled = compile_canonical_profile(profile_key, force=True)
            if isinstance(compiled, dict) and compiled.get("success"):
                return compiled
        except Exception as exc:  # noqa: BLE001
            fallback = dict(payload)
            fallback.setdefault("diagnostics", {})
            fallback["diagnostics"] = {
                "compiler": "canonical_profile_compiler",
                "warnings": [],
                "errors": [f"Canonical dossier fallback failed: {exc}"],
            }
            return fallback

    return payload


def resolve_profile_key(payload: dict[str, Any]) -> str:
    """Resolve profile key from wrapper payloads."""
    profiles = payload.get("profiles")
    if isinstance(profiles, list) and profiles:
        return str(profiles[0])

    reasoning = payload.get("reasoning", {})
    profiles = reasoning.get("profiles")
    if isinstance(profiles, list) and profiles:
        return str(profiles[0])

    profile_key = payload.get("profile_key")
    if profile_key:
        return str(profile_key)

    subject = payload.get("subject")
    if subject:
        return str(subject)

    return ""


def render_identity_section(payload: dict[str, Any]) -> None:
    """Render identity and lifecycle section."""
    identity = payload.get("identity", {})
    birth = payload.get("birth", {})
    death = payload.get("death", {})
    lifecycle = payload.get("lifecycle", {})

    divider("Identity")

    col1, col2, col3 = st.columns(3)
    col1.metric("Profile Key", identity.get("profile_key", payload.get("profile_key", "unknown")))
    col2.metric("Birth Date", birth.get("date", "missing"))
    col3.metric("Birth Time", birth.get("time", "missing"))

    st.markdown(f"**Full Name:** {identity.get('full_name', 'unknown')}")
    st.markdown(f"**Birth Place:** {birth.get('place', 'missing')}")
    st.markdown(f"**Lifecycle Status:** {death.get('lifecycle_status') or lifecycle.get('status', 'unknown')}")

    notes = lifecycle.get("notes")
    if notes:
        st.markdown(f"**Notes:** {notes}")


def render_classification_section(payload: dict[str, Any]) -> None:
    """Render structural classification section."""
    classification = payload.get("classification", {})
    if not classification:
        return

    divider("Structural Classification")

    col1, col2 = st.columns(2)
    col1.metric("Structural Role", classification.get("structural_role", "unresolved"))
    col2.metric("Confidence", format_confidence(classification.get("confidence")))

    function = classification.get("civilization_function")
    if function:
        st.markdown(f"**Civilization Function:** {function}")

    cognitive = classification.get("cognitive_style")
    if cognitive:
        st.markdown(f"**Cognitive Style:** {cognitive}")

    basis = classification.get("basis", {})
    if isinstance(basis, dict) and basis:
        st.markdown("**Classification Basis**")
        metric_grid(flatten_simple_dict(basis))


def render_temporal_section(payload: dict[str, Any]) -> None:
    """Render temporal intelligence section."""
    temporal = payload.get("temporal", {})
    if not isinstance(temporal, dict):
        return

    divider("Temporal Intelligence")

    status = temporal.get("status", "unknown")
    summary = temporal.get("summary", {})
    natal = temporal.get("natal", {})
    ephemeris = natal.get("ephemeris", {}) if isinstance(natal, dict) else {}

    col1, col2, col3 = st.columns(3)
    col1.metric("Temporal Status", status)
    col2.metric("Ephemeris", "compiled" if ephemeris else "missing")
    col3.metric("Planet Count", safe_get(summary, "planet_count", 0))

    if isinstance(summary, dict) and summary:
        metric_grid(flatten_simple_dict(summary))

    warnings = temporal.get("warnings", [])
    errors = temporal.get("errors", [])
    render_warning_error_blocks(warnings, errors)


def render_graph_section(payload: dict[str, Any]) -> None:
    """Render graph intelligence section."""
    graph = payload.get("graph", {})
    if not isinstance(graph, dict):
        return

    divider("Graph Intelligence")

    summary = graph.get("summary", {})
    fingerprint = payload.get("fingerprint", {}).get("summary", {})

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Graph Status", graph.get("status", "unknown"))
    col2.metric("CIG Nodes", fingerprint.get("cig_nodes", 0))
    col3.metric("CIG Edges", fingerprint.get("cig_edges", 0))
    col4.metric("STG Nodes", fingerprint.get("stg_nodes", 0))

    if isinstance(summary, dict) and summary:
        with st.expander("Graph Summary", expanded=False):
            st.json(summary)


def render_topology_section(payload: dict[str, Any]) -> None:
    """Render topology section."""
    topology = payload.get("topology", {})
    if not isinstance(topology, dict):
        return

    divider("Topology Intelligence")

    summary = topology.get("summary", {})

    col1, col2, col3 = st.columns(3)
    col1.metric("Topology Class", topology.get("topology_class", "n/a"))
    col2.metric("Dominant Axis", topology.get("dominant_topology_axis", "n/a"))
    col3.metric("Motif Count", topology.get("motif_count", 0))

    if isinstance(summary, dict):
        flow = summary.get("flow_pattern")
        organization = summary.get("organization_pattern")
        stability = summary.get("stability_pattern")

        if flow:
            st.markdown(f"**Flow Pattern:** {flow}")
        if organization:
            st.markdown(f"**Organization Pattern:** {organization}")
        if stability:
            st.markdown(f"**Stability Pattern:** {stability}")

        vector = summary.get("topology_vector")
        if isinstance(vector, dict) and vector:
            st.markdown("**Topology Vector**")
            metric_grid(flatten_simple_dict(vector))


def render_resonance_section(payload: dict[str, Any]) -> None:
    """Render resonance section."""
    resonance = payload.get("resonance", {})
    if not isinstance(resonance, dict):
        return

    divider("Resonance Intelligence")

    summary = resonance.get("summary", {})

    col1, col2 = st.columns(2)
    col1.metric("Resonance Class", resonance.get("resonance_class", "n/a"))
    col2.metric("Dominant Axis", resonance.get("dominant_resonance_axis", "n/a"))

    if isinstance(summary, dict):
        for label, key in [
            ("Activation Pattern", "activation_pattern"),
            ("Propagation Pattern", "propagation_pattern"),
            ("Damping Pattern", "damping_pattern"),
        ]:
            value = summary.get(key)
            if value:
                st.markdown(f"**{label}:** {value}")

        vector = summary.get("resonance_vector")
        if isinstance(vector, dict) and vector:
            st.markdown("**Resonance Vector**")
            metric_grid(flatten_simple_dict(vector))


def render_fingerprint_section(payload: dict[str, Any]) -> None:
    """Render structural fingerprint section."""
    fingerprint = payload.get("fingerprint", {})
    if not isinstance(fingerprint, dict):
        return

    divider("Structural Fingerprint")

    summary = fingerprint.get("summary", {})
    if isinstance(summary, dict) and summary:
        metric_grid(flatten_simple_dict(summary))


def render_diagnostics_section(payload: dict[str, Any]) -> None:
    """Render diagnostics section."""
    diagnostics = payload.get("diagnostics", {})
    if not isinstance(diagnostics, dict):
        return

    divider("Diagnostics")

    col1, col2, col3 = st.columns(3)
    col1.metric("Compiler", diagnostics.get("compiler", "unknown"))
    col2.metric("Warnings", len(diagnostics.get("warnings", [])))
    col3.metric("Errors", len(diagnostics.get("errors", [])))

    created_at = diagnostics.get("created_at")
    if created_at:
        st.markdown(f"**Created At:** {created_at}")

    render_warning_error_blocks(
        diagnostics.get("warnings", []),
        diagnostics.get("errors", []),
    )


def render_warning_error_blocks(warnings: list[Any], errors: list[Any]) -> None:
    """Render warning and error lists."""
    if warnings:
        with st.expander("Warnings", expanded=False):
            for warning in warnings:
                st.warning(str(warning))

    if errors:
        with st.expander("Errors", expanded=False):
            for error in errors:
                st.error(str(error))


def build_executive_summary(payload: dict[str, Any]) -> str:
    """Build fallback executive summary."""
    classification = payload.get("classification", {})
    identity = payload.get("identity", {})
    name = identity.get("display_name") or identity.get("name") or payload.get("profile_key", "This profile")
    role = classification.get("structural_role", "an unresolved structural role")
    function = classification.get("civilization_function", "")

    if function:
        return f"{name} is compiled as **{role}**. {function}"

    return f"{name} is compiled as **{role}** through the Atlas canonical profile pipeline."


def format_confidence(confidence: Any) -> str:
    """Format confidence object."""
    if isinstance(confidence, dict):
        label = confidence.get("label", "unknown")
        percent = confidence.get("percent")
        if percent is not None:
            return f"{percent}% {label}"
        return str(label)

    if confidence:
        return str(confidence)

    return "unknown"


def flatten_simple_dict(values: dict[str, Any]) -> dict[str, Any]:
    """Flatten simple dictionary values for metric rendering."""
    flat: dict[str, Any] = {}

    for key, value in values.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            flat[humanize(str(key))] = "n/a" if value is None else value

    return flat


def safe_get(values: Any, key: str, default: Any = None) -> Any:
    """Safely get key from dict."""
    if isinstance(values, dict):
        return values.get(key, default)
    return default


def humanize(value: str) -> str:
    """Humanize keys."""
    return str(value).replace("_", " ").title()
