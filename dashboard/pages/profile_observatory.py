"""Profile Observatory page.

This page is partially service-backed. Direct ACF, overlay, resonance, and
research-matrix calls are routed through atlas.services.profile_observatory_service.
"""

from __future__ import annotations

import json
from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.profile_payload_service import build_profile_payload
from atlas.services.profile_observatory_service import (
    build_current_profile_matrix_rows,
    build_profile_overlay,
    build_profile_resonance_field,
    list_observatory_profiles,
    load_or_repair_profile_acf,
)
from atlas.services.single_profile_intelligence_service import (
    build_single_profile_intelligence_payload,
)
from dashboard.ui.profile_view import render_profile_view
from dashboard.ui.timeline import render_timeline
from components.ive_panel import render_ive_panel
from components.observatory.calibration import render_calibration_view
from components.observatory.functional_role_v2 import render_functional_role_v2
from components.observatory.graph_evolution_3d import render_graph_evolution_3d
from components.observatory.header import render_observatory_header


def render_profile_observatory_page() -> None:
    """Render Profile Observatory page."""
    st.header("Profile Observatory")

    profiles = list_observatory_profiles()

    if not profiles:
        st.info("No saved profiles yet. Build a profile first.")
        return

    selected = st.selectbox("Profile", profiles)
    acf = load_or_repair_profile_acf(selected)

    if acf is None:
        st.error(f"No ACF found for `{selected}`. Rebuild this profile first.")
        return

    safe_section("Header", lambda: render_observatory_header(acf))

    intelligence_payload = build_single_profile_intelligence_payload(selected)
    canonical_payload = build_profile_payload(selected)

    tab_dossier, tab_integrated, tab_identity, tab_graph, tab_emanations, tab_overlay, tab_resonance, tab_layers, tab_calibration, tab_matrix, tab_debug = st.tabs(
        [
            "Profile Dossier",
            "Integrated Intelligence",
            "Identity",
            "Graph 3D",
            "21 Emanations",
            "Composite Overlay",
            "Resonance Field",
            "Historical Layers",
            "Calibration",
            "Research Matrix",
            "Legacy Debug",
        ]
    )

    with tab_dossier:
        safe_section(
            "Profile Dossier",
            lambda: render_profile_dossier(canonical_payload),
        )

    with tab_integrated:
        safe_section(
            "Integrated Intelligence",
            lambda: render_integrated_intelligence(intelligence_payload),
        )

    with tab_dossier:
        safe_section(
            "Profile Dossier",
            lambda: render_profile_dossier(canonical_payload),
        )

    with tab_integrated:
        safe_section(
            "Integrated Intelligence",
            lambda: render_integrated_intelligence(intelligence_payload),
        )

    with tab_identity:
        safe_section("Identity Vector", lambda: render_ive_panel(acf))
        safe_section("Identity Fingerprint", lambda: render_identity_fingerprint(acf))

    with tab_graph:
        safe_section("Graph Evolution 3D", lambda: render_graph_evolution_3d(acf))

    with tab_emanations:
        safe_section("21 Emanations", lambda: render_emanation_summary(acf))

    with tab_overlay:
        safe_section("Composite Overlay", lambda: render_composite_overlay(acf))

    with tab_resonance:
        safe_section("Resonance Field", lambda: render_resonance_field(acf))

    with tab_layers:
        safe_section("Historical Layers", lambda: render_layer_explorer(acf))

    with tab_calibration:
        safe_section("Calibration", lambda: render_calibration_view(acf))

    with tab_matrix:
        safe_section("Research Matrix", lambda: render_research_matrix(acf))

    with tab_debug:
        safe_section("Legacy Debug", lambda: render_legacy_debug(acf))



def render_profile_dossier(payload: dict[str, Any]) -> None:
    """Render canonical profile dossier."""
    if not payload.get("success"):
        st.error("Canonical profile payload failed.")
        st.json(payload)
        return

    render_profile_view(payload)

    lifecycle = payload.get("lifecycle", {})
    timeline = lifecycle.get("timeline", []) if isinstance(lifecycle, dict) else []

    if timeline:
        st.markdown("## Lifecycle Timeline")
        render_timeline(
            timeline,
            title="Lifecycle Timeline",
            subtitle=lifecycle.get("observed_lifespan", "Historical lifecycle"),
        )


def safe_section(name: str, render_fn) -> None:
    """Render a section safely."""
    try:
        render_fn()
    except Exception as exc:
        st.error(f"{name} failed.")
        st.exception(exc)


def render_identity_fingerprint(acf: dict[str, Any]) -> None:
    """Render identity fingerprint summary."""
    st.markdown("## Identity Fingerprint")

    overlay = build_profile_overlay(acf)
    resonance_field = build_profile_resonance_field(acf)
    resonance_core = build_resonance_core_from_field(resonance_field)

    c1, c2, c3 = st.columns(3)
    c1.metric("Overlay keys", len(overlay) if isinstance(overlay, dict) else 0)
    c2.metric("Resonance keys", len(resonance_field) if isinstance(resonance_field, dict) else 0)
    c3.metric("Core keys", len(resonance_core) if isinstance(resonance_core, dict) else 0)

    st.markdown("### Functional Role")
    render_functional_role_v2(acf)

    with st.expander("Overlay", expanded=False):
        st.json(overlay)

    with st.expander("Resonance core", expanded=False):
        st.json(resonance_core)


def render_emanation_summary(acf: dict[str, Any]) -> None:
    """Render 21-layer emanation summary."""
    st.markdown("## 21 Emanations")

    rows = build_current_profile_matrix_rows(acf)

    if not rows:
        st.info("No matrix rows available.")
        return

    df = clean_display_dataframe(pd.DataFrame(rows))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Rows", len(df))
    c2.metric("Ciphers", df["cipher"].nunique() if "cipher" in df else 0)
    c3.metric("Planets", df["planet"].nunique() if "planet" in df else 0)
    c4.metric("Numeric metrics", len(df.select_dtypes(include="number").columns))

    preview_columns = [
        column
        for column in [
            "name",
            "cipher",
            "planet",
            "kamea",
            "grid_size",
            "sequence_length",
            "unique_nodes",
            "node_coverage",
            "unique_edges",
            "max_node_weight",
        ]
        if column in df.columns
    ]

    if preview_columns:
        st.dataframe(df[preview_columns], width="stretch")
    else:
        st.dataframe(df, width="stretch")

    with st.expander("Full 21-layer matrix", expanded=False):
        st.dataframe(df, width="stretch")


def render_composite_overlay(acf: dict[str, Any]) -> None:
    """Render composite overlay."""
    st.markdown("## Composite Overlay")

    overlay = build_profile_overlay(acf)

    if not isinstance(overlay, dict):
        st.write(overlay)
        return

    st.markdown("### Overlay Summary")
    summary = {
        key: type(value).__name__
        for key, value in overlay.items()
    }
    st.dataframe(dict_table(summary, "key", "type"), width="stretch")

    st.markdown("### Overlay JSON")
    st.json(overlay)


def render_resonance_field(acf: dict[str, Any]) -> None:
    """Render resonance field."""
    st.markdown("## Resonance Field")

    resonance_field = build_profile_resonance_field(acf)

    if not isinstance(resonance_field, dict):
        st.write(resonance_field)
        return

    resonance_core = build_resonance_core_from_field(resonance_field)

    c1, c2 = st.columns(2)
    c1.metric("Field keys", len(resonance_field))
    c2.metric("Core keys", len(resonance_core))

    st.markdown("### Resonance Core")
    st.json(resonance_core)

    with st.expander("Full resonance field", expanded=False):
        st.json(resonance_field)


def render_layer_explorer(acf: dict[str, Any]) -> None:
    """Render profile layer explorer."""
    st.markdown("## Historical Layers")

    if not isinstance(acf, dict):
        st.info("ACF is not dictionary-like.")
        return

    layer_candidates = {}

    for key in [
        "identity",
        "layers",
        "classification",
        "essence",
        "fingerprint",
        "paths",
        "path_views",
        "metadata",
    ]:
        if key in acf:
            layer_candidates[key] = acf[key]

    if not layer_candidates:
        st.info("No known layer fields found.")
        st.json(acf)
        return

    selected_layer = st.selectbox("Layer", sorted(layer_candidates))
    st.json(layer_candidates[selected_layer])


def render_research_matrix(acf: dict[str, Any]) -> None:
    """Render research matrix rows from current ACF."""
    st.markdown("## Current Profile Research Matrix")

    rows = build_current_profile_matrix_rows(acf)
    df = clean_display_dataframe(pd.DataFrame(rows))

    st.dataframe(df, width="stretch")

    st.download_button(
        "Download current_profile_matrix.csv",
        data=df.to_csv(index=False).encode("utf-8"),
        file_name="current_profile_matrix.csv",
        mime="text/csv",
    )


def render_legacy_debug(acf: dict[str, Any]) -> None:
    """Render legacy debug information."""
    st.markdown("## Legacy Debug")

    render_legacy_classification_expander(acf)

    with st.expander("Raw ACF", expanded=False):
        st.json(acf)


def render_legacy_classification_expander(acf: dict[str, Any]) -> None:
    """Render legacy classification data when present."""
    classification_keys = [
        "classification",
        "role",
        "functional_role",
        "archetype",
        "metadata",
    ]

    found = {
        key: acf[key]
        for key in classification_keys
        if key in acf
    }

    if not found:
        st.info("No legacy classification fields found.")
        return

    with st.expander("Legacy classification", expanded=True):
        st.json(found)


def build_resonance_core_from_field(resonance_field: dict[str, Any]) -> dict[str, Any]:
    """Build compact resonance core from resonance field."""
    if not isinstance(resonance_field, dict):
        return {}

    core = {}

    for key, value in resonance_field.items():
        if isinstance(value, (int, float, str, bool)) or value is None:
            core[key] = value
        elif isinstance(value, dict):
            numeric_values = {
                subkey: subvalue
                for subkey, subvalue in value.items()
                if isinstance(subvalue, (int, float))
            }
            if numeric_values:
                core[key] = numeric_values
            else:
                core[key] = {"type": "dict", "keys": list(value.keys())[:25]}
        elif isinstance(value, list):
            core[key] = {
                "type": "list",
                "length": len(value),
            }
        else:
            core[key] = {
                "type": type(value).__name__,
            }

    return core


def clean_display_dataframe(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Clean dataframe values for Streamlit display."""
    if dataframe.empty:
        return dataframe

    cleaned = dataframe.copy()

    for column in cleaned.columns:
        cleaned[column] = cleaned[column].map(clean_display_value)

    return cleaned


def clean_display_value(value):
    """Clean a display value."""
    if isinstance(value, (dict, list, tuple)):
        return json.dumps(value, default=str)

    return value


def dict_table(data: dict, key_name: str, value_name: str) -> pd.DataFrame:
    """Convert dictionary to two-column dataframe."""
    return pd.DataFrame(
        [
            {
                key_name: key,
                value_name: value,
            }
            for key, value in data.items()
        ]
    )


def format_float(value) -> str:
    """Format float-like values."""
    try:
        return f"{float(value):.4f}"
    except Exception:
        return str(value)

def render_integrated_intelligence(payload: dict[str, Any]) -> None:
    """Render integrated single-profile intelligence payload."""
    st.markdown("## Integrated Intelligence")

    if not payload.get("success"):
        st.error("Single profile intelligence payload failed.")
        st.json(
            {
                "warnings": payload.get("warnings", []),
                "errors": payload.get("errors", []),
            }
        )
        return

    runtime = payload.get("temporal_runtime", {})
    forecast = payload.get("forecast", {})
    graph_metrics = payload.get("graph_metrics", {})
    activation = payload.get("graph_activation", {})
    propagation = payload.get("graph_propagation", {})
    fingerprint = payload.get("structural_fingerprint", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Runtime", "yes" if runtime.get("success") else "no")
    c2.metric("Graph nodes", graph_metrics.get("node_count", 0))
    c3.metric("Graph edges", graph_metrics.get("edge_count", 0))
    c4.metric("Forecast days", forecast.get("count", 0))

    activation_summary = activation.get("summary", {})
    propagation_summary = propagation.get("summary", {})

    c5, c6, c7, c8 = st.columns(4)
    c5.metric(
        "Activation center",
        activation_summary.get("activation_center", "n/a"),
    )
    c6.metric(
        "Top propagated node",
        propagation_summary.get("top_node", "n/a"),
    )
    c7.metric(
        "Max activation",
        format_float(activation_summary.get("max_node_activation", 0.0)),
    )
    c8.metric(
        "Propagation total",
        format_float(propagation_summary.get("total_score", 0.0)),
    )

    st.markdown("### Structural Fingerprint")
    if fingerprint:
        st.code(fingerprint.get("structural_hash", ""), language="text")

        vector = fingerprint.get("vector", {})
        if isinstance(vector, dict) and vector:
            st.dataframe(
                dict_table(vector, "feature", "value"),
                width="stretch",
            )

    tabs = st.tabs(
        [
            "Runtime",
            "Forecast",
            "Graph Metrics",
            "Activation",
            "Propagation",
            "Fingerprint",
            "Raw Payload",
        ]
    )

    with tabs[0]:
        st.json(runtime)

    with tabs[1]:
        st.json(forecast)

    with tabs[2]:
        st.json(graph_metrics)

    with tabs[3]:
        st.json(activation)

    with tabs[4]:
        st.json(propagation)

    with tabs[5]:
        st.json(fingerprint)

    with tabs[6]:
        st.json(payload)
