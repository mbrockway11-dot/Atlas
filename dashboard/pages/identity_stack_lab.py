"""Identity Stack Lab page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.graph_service import (
    build_graph_figure,
    build_identity_stack_payload,
    get_cig_graph,
    get_stg_graph,
    has_graph_data,
    json_export,
    list_graph_profiles,
    safe_filename,
)


def render_identity_stack_lab_page() -> None:
    """Render Identity Stack Lab page."""
    st.header("Identity Stack Lab")
    st.caption(
        "Build the complete graph-native identity stack: CIG, STG, motifs, "
        "genome, topology, resonance, audit, and exports."
    )

    profiles = list_graph_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    selected_profile = st.selectbox(
        "Profile",
        profiles,
        key="identity_stack_lab_profile",
    )

    graph_mode = st.selectbox(
        "Graph View",
        ["Both CIG and STG", "Structural Truth Graph only", "No graph"],
        key="identity_stack_graph_mode",
    )

    graph_layout = st.selectbox(
        "Graph Layout",
        ["spring", "kamada_kawai", "circular", "shell"],
        key="identity_stack_graph_layout",
    )

    if not st.button("Build Identity Stack", type="primary"):
        st.info("Select a profile and build the identity stack.")
        return

    with st.spinner("Building identity graph stack..."):
        payload = build_identity_stack_payload(selected_profile)

    if not payload.get("success"):
        st.error("Identity Stack build failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(payload)
        return

    stack_data = payload["data"]["stack_data"]
    audit_data = payload["data"]["audit_data"]

    render_stack_summary(payload, stack_data)
    render_stack_audit(audit_data)

    if graph_mode != "No graph":
        render_graph_visualizations(stack_data, graph_layout, graph_mode)

    render_cig_summary(stack_data)
    render_stg_summary(stack_data)
    render_motif_summary(stack_data)
    render_genome_summary(stack_data)
    render_topology_summary(stack_data)
    render_resonance_summary(stack_data)
    render_download_exports(payload)


def render_stack_summary(payload: dict[str, Any], stack_data: dict[str, Any]) -> None:
    """Render top-level stack summary."""
    st.markdown("## Stack Summary")

    metrics = payload.get("metrics", {})
    summary = stack_data.get("summary", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Name", metrics.get("name", "n/a"))
    c2.metric("Version", metrics.get("version", "n/a"))
    c3.metric("Audit Status", metrics.get("audit_status", "unknown"))
    c4.metric("Motifs", metrics.get("motif_count", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("CIG Nodes", metrics.get("cig_nodes", 0))
    c6.metric("CIG Edges", metrics.get("cig_edges", 0))
    c7.metric("STG Nodes", metrics.get("stg_nodes", 0))
    c8.metric("STG Edges", metrics.get("stg_edges", 0))

    with st.expander("Raw Stack Summary", expanded=False):
        st.json(summary)


def render_stack_audit(audit_data: dict[str, Any]) -> None:
    """Render Stack Audit dashboard."""
    st.markdown("## Stack Audit")

    status = audit_data.get("status", "unknown")
    warnings = audit_data.get("warnings", [])
    errors = audit_data.get("errors", [])

    c1, c2, c3 = st.columns(3)
    c1.metric("Status", status)
    c2.metric("Warnings", len(warnings))
    c3.metric("Errors", len(errors))

    if status == "passed":
        st.success("Stack audit passed. No structural issues detected.")
    elif errors:
        st.error("Stack audit found errors. Fix before trusting downstream analysis.")
    elif warnings:
        st.warning("Stack audit found warnings. Review before treating output as final.")
    else:
        st.info("Stack audit status unknown.")

    if warnings:
        with st.expander("Warnings", expanded=False):
            st.json(warnings)

    if errors:
        with st.expander("Errors", expanded=False):
            st.json(errors)

    with st.expander("Raw Audit JSON", expanded=False):
        st.json(audit_data)


def render_graph_visualizations(
    stack_data: dict[str, Any],
    graph_layout: str,
    graph_mode: str,
) -> None:
    """Render CIG and STG graph visualizations."""
    st.markdown("## Graph Visualizations")

    if graph_mode == "Both CIG and STG":
        tab_cig, tab_stg = st.tabs(
            ["Canonical Identity Graph", "Structural Truth Graph"]
        )

        with tab_cig:
            render_cig_graph(stack_data, graph_layout)

        with tab_stg:
            render_stg_graph(stack_data, graph_layout)
    else:
        render_stg_graph(stack_data, graph_layout)


def render_cig_graph(stack_data: dict[str, Any], graph_layout: str) -> None:
    """Render Canonical Identity Graph visualization."""
    cig_graph = get_cig_graph(stack_data)

    if not has_graph_data(cig_graph):
        st.info("No CIG graph data available.")
        return

    st.caption("Canonical Identity Graph shows the full canonical attractor graph.")

    figure = build_graph_figure(
        cig_graph,
        title="Canonical Identity Graph",
        layout=graph_layout,
    )

    st.plotly_chart(figure, width="stretch")


def render_stg_graph(stack_data: dict[str, Any], graph_layout: str) -> None:
    """Render Structural Truth Graph visualization."""
    stg_graph = get_stg_graph(stack_data)

    if not has_graph_data(stg_graph):
        st.info("No STG graph data available.")
        return

    st.caption("Structural Truth Graph shows compressed identity structure.")

    figure = build_graph_figure(
        stg_graph,
        title="Structural Truth Graph",
        layout=graph_layout,
    )

    st.plotly_chart(figure, width="stretch")


def render_cig_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Canonical Identity Graph")
    render_dict_summary(stack_data.get("cig", {}).get("summary", {}))


def render_stg_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Structural Truth Graph")
    render_dict_summary(stack_data.get("stg", {}).get("summary", {}))


def render_motif_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Motifs")
    render_dict_summary(stack_data.get("motifs", {}).get("summary", {}))


def render_genome_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Identity Genome")
    render_dict_summary(stack_data.get("genome", {}).get("summary", {}))


def render_topology_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Identity Topology")
    render_dict_summary(stack_data.get("topology", {}).get("summary", {}))


def render_resonance_summary(stack_data: dict[str, Any]) -> None:
    st.markdown("## Identity Resonance")
    render_dict_summary(stack_data.get("resonance", {}).get("summary", {}))


def render_dict_summary(data: dict[str, Any]) -> None:
    """Render dictionary summary as table and JSON."""
    if not data:
        st.info("No summary data available.")
        return

    dataframe = pd.DataFrame(
        [{"metric": key, "value": format_table_value(value)} for key, value in data.items()]
    )

    st.dataframe(dataframe, width="stretch")

    with st.expander("Raw JSON", expanded=False):
        st.json(data)


def render_download_exports(payload: dict[str, Any]) -> None:
    """Render download buttons."""
    st.markdown("## Exports")

    exports = payload.get("exports", {})
    stack_data = exports.get("full_stack", {})
    name = str(stack_data.get("name", "identity_stack"))
    safe_name = safe_filename(name)

    c1, c2, c3, c4 = st.columns(4)

    c1.download_button(
        label="Download compact stack JSON",
        data=json_export(exports.get("compact", {})),
        file_name=f"{safe_name}_identity_stack_compact.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download summary JSON",
        data=json_export(exports.get("summary", {})),
        file_name=f"{safe_name}_identity_stack_summary.json",
        mime="application/json",
    )

    c3.download_button(
        label="Download audit JSON",
        data=json_export(exports.get("audit", {})),
        file_name=f"{safe_name}_identity_stack_audit.json",
        mime="application/json",
    )

    c4.download_button(
        label="Download full stack JSON",
        data=json_export(exports.get("full_stack", {})),
        file_name=f"{safe_name}_identity_stack_full.json",
        mime="application/json",
    )


def format_table_value(value: Any) -> str:
    """Format table values safely."""
    if isinstance(value, float):
        return f"{value:.4f}"

    if isinstance(value, (list, dict)):
        return json_export(value)

    return str(value)
