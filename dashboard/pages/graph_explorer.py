"""Graph Explorer dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.graph_service import (
    build_graph_figure,
    build_identity_stack_payload,
    build_morphology_payload,
    get_cig_graph,
    get_stg_graph,
    json_export,
    list_graph_profiles,
)
from atlas.services.graph_reasoning_service import (
    build_profile_graph_reasoning_payload,
    build_relationship_graph_reasoning_payload,
    json_export as graph_reasoning_json_export,
)


def render_graph_explorer_page() -> None:
    """Render Graph Explorer."""
    st.header("Graph Explorer")
    st.caption(
        "Inspect Canonical Identity Graphs, Structural Truth Graphs, topology, "
        "resonance, and morphology comparisons."
    )

    profiles = list_graph_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    tabs = st.tabs(
    [
            "Identity Graph",
            "Truth Graph",
            "Topology",
            "Morphology",
            "Graph Reasoning",
            "Diagnostics",
        ]
    )

    with tabs[0]:
        render_identity_graph_tab(profiles)

    with tabs[1]:
        render_truth_graph_tab(profiles)

    with tabs[2]:
        render_topology_tab(profiles)

    with tabs[3]:
        render_morphology_tab(profiles)

    with tabs[4]:
        render_graph_reasoning_tab(profiles)

    with tabs[5]:
        render_diagnostics_tab(profiles)


def render_identity_graph_tab(profiles: list[str]) -> None:
    """Render CIG graph tab."""
    st.markdown("## Canonical Identity Graph")

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="graph_explorer_identity_profile",
    )

    layout = st.selectbox(
        "Layout",
        ["spring", "circular", "kamada_kawai", "shell"],
        key="graph_explorer_identity_layout",
    )

    with st.spinner("Building identity graph stack..."):
        payload = build_identity_stack_payload(profile_key)

    if not payload.get("success"):
        render_errors(payload)
        return

    render_stack_metrics(payload)

    stack_data = payload.get("data", {}).get("stack_data", {})
    graph = get_cig_graph(stack_data)

    render_graph_visualization(
        graph=graph,
        title=f"{profile_key} Canonical Identity Graph",
        layout=layout,
    )

    render_graph_tables(graph)

    with st.expander("Raw CIG Graph", expanded=False):
        st.json(graph)


def render_truth_graph_tab(profiles: list[str]) -> None:
    """Render STG graph tab."""
    st.markdown("## Structural Truth Graph")

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="graph_explorer_truth_profile",
    )

    layout = st.selectbox(
        "Layout",
        ["spring", "circular", "kamada_kawai", "shell"],
        key="graph_explorer_truth_layout",
    )

    with st.spinner("Building structural truth graph..."):
        payload = build_identity_stack_payload(profile_key)

    if not payload.get("success"):
        render_errors(payload)
        return

    render_stack_metrics(payload)

    stack_data = payload.get("data", {}).get("stack_data", {})
    graph = get_stg_graph(stack_data)

    render_graph_visualization(
        graph=graph,
        title=f"{profile_key} Structural Truth Graph",
        layout=layout,
    )

    render_graph_tables(graph)

    with st.expander("Raw STG Graph", expanded=False):
        st.json(graph)


def render_topology_tab(profiles: list[str]) -> None:
    """Render topology and resonance summary."""
    st.markdown("## Topology & Resonance")

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="graph_explorer_topology_profile",
    )

    with st.spinner("Building topology payload..."):
        payload = build_identity_stack_payload(profile_key)

    if not payload.get("success"):
        render_errors(payload)
        return

    stack_data = payload.get("data", {}).get("stack_data", {})
    summary = stack_data.get("summary", {})
    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Raw Nodes", metrics.get("cig_nodes", 0))
    c2.metric("Raw Edges", metrics.get("cig_edges", 0))
    c3.metric("Truth Nodes", metrics.get("stg_nodes", 0))
    c4.metric("Truth Edges", metrics.get("stg_edges", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Motif Richness", format_number(metrics.get("motif_count", 0)))
    c6.metric("Dominant Motif", metrics.get("dominant_motif", "n/a"))
    c7.metric("Topology", metrics.get("topology_class", "n/a"))
    c8.metric("Resonance", metrics.get("resonance_class", "n/a"))

    st.markdown("### Stack Summary")
    st.json(summary)

    compact = payload.get("exports", {}).get("compact", {})

    with st.expander("Compact Stack Export", expanded=False):
        st.json(compact)

    render_summary_tables(compact)


def render_morphology_tab(profiles: list[str]) -> None:
    """Render morphology comparison tab."""
    st.markdown("## Morphology Comparison")

    col_a, col_b = st.columns(2)

    with col_a:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            index=0,
            key="graph_explorer_morphology_a",
        )

    with col_b:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="graph_explorer_morphology_b",
        )

    if profile_a == profile_b:
        st.warning("Select two different profiles.")
        return

    with st.spinner("Building morphology comparison..."):
        payload = build_morphology_payload(profile_a, profile_b)

    if not payload.get("success"):
        render_errors(payload)
        return

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Morphology Class", metrics.get("morphology_class", "n/a"))
    c2.metric("Similarity", format_number(metrics.get("similarity", 0)))
    c3.metric("Distance", format_number(metrics.get("distance", 0)))
    c4.metric("Mutation", format_number(metrics.get("mutation_score", 0)))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Node Overlap", format_number(metrics.get("node_overlap", 0)))
    c6.metric("Edge Overlap", format_number(metrics.get("edge_overlap", 0)))
    c7.metric("Shared Nodes", metrics.get("shared_node_count", 0))
    c8.metric("Shared Edges", metrics.get("shared_edge_count", 0))

    st.markdown("### Edit Summary")

    edit_rows = [
        {"change": "Added nodes", "count": metrics.get("added_node_count", 0)},
        {"change": "Removed nodes", "count": metrics.get("removed_node_count", 0)},
        {"change": "Added edges", "count": metrics.get("added_edge_count", 0)},
        {"change": "Removed edges", "count": metrics.get("removed_edge_count", 0)},
    ]

    st.dataframe(pd.DataFrame(edit_rows), width="stretch")

    st.markdown("### Mutation Layers")

    mutation_rows = [
        {"layer": "Motif", "score": metrics.get("motif_mutation", 0)},
        {"layer": "Genome", "score": metrics.get("genome_mutation", 0)},
        {"layer": "Topology", "score": metrics.get("topology_mutation", 0)},
        {"layer": "Resonance", "score": metrics.get("resonance_mutation", 0)},
    ]

    st.dataframe(pd.DataFrame(mutation_rows), width="stretch")

    morphology_data = payload.get("data", {}).get("morphology_data", {})

    with st.expander("Morphology Summary", expanded=False):
        st.json(morphology_data.get("summary", {}))

    with st.expander("Raw Morphology Data", expanded=False):
        st.json(morphology_data)

    render_morphology_exports(payload)

def render_graph_reasoning_tab(profiles: list[str]) -> None:
    """Render graph reasoning tab."""
    st.markdown("## Graph Reasoning")
    st.caption(
        "Deterministic reasoning over graph stack and morphology metrics."
    )

    mode = st.radio(
        "Reasoning scope",
        ["Profile", "Relationship"],
        horizontal=True,
        key="graph_reasoning_scope",
    )

    if mode == "Profile":
        profile_key = st.selectbox(
            "Profile",
            profiles,
            key="graph_reasoning_profile",
        )

        if not st.button("Build Profile Graph Reasoning", type="primary"):
            st.info("Select a profile and build graph reasoning.")
            return

        with st.spinner("Building profile graph reasoning..."):
            payload = build_profile_graph_reasoning_payload(profile_key)

    else:
        col_a, col_b = st.columns(2)

        with col_a:
            profile_a = st.selectbox(
                "Profile A",
                profiles,
                index=0,
                key="graph_reasoning_profile_a",
            )

        with col_b:
            profile_b = st.selectbox(
                "Profile B",
                profiles,
                index=1 if len(profiles) > 1 else 0,
                key="graph_reasoning_profile_b",
            )

        if profile_a == profile_b:
            st.warning("Select two different profiles.")
            return

        if not st.button("Build Relationship Graph Reasoning", type="primary"):
            st.info("Select two profiles and build graph reasoning.")
            return

        with st.spinner("Building relationship graph reasoning..."):
            payload = build_relationship_graph_reasoning_payload(
                profile_a,
                profile_b,
            )

    render_graph_reasoning_payload(payload)


def render_graph_reasoning_payload(payload: dict) -> None:
    """Render graph reasoning payload."""
    if not payload.get("success"):
        render_errors(payload)
        return

    metrics = payload.get("metrics", {})
    reasoning = payload.get("data", {}).get("reasoning", {})
    confidence = reasoning.get("confidence", {})
    sections = reasoning.get("sections", [])

    st.markdown("### Reasoning Health")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sections", metrics.get("section_count", 0))
    c2.metric("Claims", metrics.get("claim_count", 0))
    c3.metric("Evidence Items", metrics.get("evidence_count", 0))
    c4.metric(
        "Overall Confidence",
        format_confidence(metrics.get("overall_confidence", {})),
    )

    if confidence:
        st.markdown("### Confidence Model")
        confidence_rows = []

        for key, record in confidence.items():
            if isinstance(record, dict) and "percent" in record:
                confidence_rows.append(
                    {
                        "layer": key,
                        "label": record.get("label", "unknown"),
                        "percent": record.get("percent", 0),
                        "score": record.get("score", 0),
                    }
                )

        if confidence_rows:
            st.dataframe(pd.DataFrame(confidence_rows), width="stretch")

    markdown = payload.get("exports", {}).get("markdown", "")

    if markdown:
        st.markdown("### Reasoning Report")
        st.markdown(markdown)

    st.markdown("### Structured Reasoning")

    if not sections:
        st.info("No reasoning sections available.")
    else:
        for section in sections:
            with st.expander(section.get("title", "Untitled Section"), expanded=False):
                summary = section.get("summary", "")
                details = section.get("details", [])
                claims = section.get("claims", [])
                cautions = section.get("cautions", [])

                if summary:
                    st.write(summary)

                if details:
                    st.markdown("#### Details")
                    for detail in details:
                        st.write(f"- {detail}")

                if claims:
                    st.markdown("#### Claims")
                    for item in claims:
                        item_confidence = item.get("confidence", {})
                        st.write(
                            f"- **{item.get('claim', '')}** "
                            f"({item_confidence.get('label', 'unknown')}, "
                            f"{item_confidence.get('percent', 0)}%)"
                        )

                        for evidence in item.get("evidence", []):
                            st.write(f"  - Evidence: {evidence}")

                if cautions:
                    st.markdown("#### Cautions")
                    for caution in cautions:
                        st.warning(caution)

                st.json(section)

    st.markdown("### Exports")

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Markdown",
        data=payload.get("exports", {}).get("markdown", ""),
        file_name="graph_reasoning.md",
        mime="text/markdown",
    )

    c2.download_button(
        "Download Reasoning JSON",
        data=graph_reasoning_json_export(
            payload.get("exports", {}).get("reasoning_json", {}),
        ),
        file_name="graph_reasoning.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Full Payload JSON",
        data=graph_reasoning_json_export(build_safe_graph_reasoning_payload(payload)),
        file_name="graph_reasoning_payload.json",
        mime="application/json",
    )

    with st.expander("Raw Graph Reasoning Payload", expanded=False):
        st.json(build_safe_graph_reasoning_payload(payload))


def build_safe_graph_reasoning_payload(payload: dict) -> dict:
    """Build circular-safe graph reasoning payload."""
    return {
        "success": payload.get("success"),
        "version": payload.get("version"),
        "scope": payload.get("scope"),
        "profile_key": payload.get("profile_key"),
        "profile_a": payload.get("profile_a"),
        "profile_b": payload.get("profile_b"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "reasoning": payload.get("data", {}).get("reasoning", {}),
        "source_summary": payload.get("data", {}).get("source_summary", {}),
    }


def format_confidence(record: dict) -> str:
    """Format confidence record."""
    if not isinstance(record, dict):
        return "n/a"

    return f"{record.get('percent', 0)}% {record.get('label', 'unknown')}"


def render_diagnostics_tab(profiles: list[str]) -> None:
    """Render graph diagnostics."""
    st.markdown("## Diagnostics")

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="graph_explorer_diagnostics_profile",
    )

    with st.spinner("Building diagnostics..."):
        payload = build_identity_stack_payload(profile_key)

    if not payload.get("success"):
        render_errors(payload)
        return

    metrics = payload.get("metrics", {})
    audit = payload.get("exports", {}).get("audit", {})

    c1, c2, c3 = st.columns(3)
    c1.metric("Audit Status", metrics.get("audit_status", "unknown"))
    c2.metric("Audit Errors", metrics.get("audit_errors", 0))
    c3.metric("Audit Warnings", metrics.get("audit_warnings", 0))

    if payload.get("warnings"):
        for warning in payload.get("warnings", []):
            st.warning(warning)

    if payload.get("errors"):
        for error in payload.get("errors", []):
            st.error(error)

    with st.expander("Audit JSON", expanded=True):
        st.json(audit)

    with st.expander("Metrics JSON", expanded=False):
        st.json(metrics)

    with st.expander("Full Stack JSON", expanded=False):
        st.json(payload.get("exports", {}).get("full_stack", {}))

    render_stack_exports(payload)


def render_stack_metrics(payload: dict) -> None:
    """Render core stack metrics."""
    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("CIG Nodes", metrics.get("cig_nodes", 0))
    c2.metric("CIG Edges", metrics.get("cig_edges", 0))
    c3.metric("STG Nodes", metrics.get("stg_nodes", 0))
    c4.metric("STG Edges", metrics.get("stg_edges", 0))

    c5, c6, c7 = st.columns(3)
    c5.metric("Dominant Motif", metrics.get("dominant_motif", "n/a"))
    c6.metric("Topology", metrics.get("topology_class", "n/a"))
    c7.metric("Resonance", metrics.get("resonance_class", "n/a"))


def render_graph_visualization(
    *,
    graph: dict,
    title: str,
    layout: str,
) -> None:
    """Render graph figure if graph data exists."""
    if not graph or not graph.get("nodes"):
        st.info("No graph nodes available for visualization.")
        return

    try:
        figure = build_graph_figure(
            graph,
            title=title,
            layout=layout,
        )
        st.plotly_chart(figure, width="stretch")
    except Exception as exc:
        st.warning(f"Graph visualization failed: {exc}")


def render_graph_tables(graph: dict) -> None:
    """Render graph node and edge tables."""
    nodes = normalize_nodes(graph.get("nodes", {}))
    edges = normalize_edges(graph.get("edges", {}))

    st.markdown("### Nodes")
    if nodes:
        st.dataframe(pd.DataFrame(nodes), width="stretch")
    else:
        st.info("No node table available.")

    st.markdown("### Edges")
    if edges:
        st.dataframe(pd.DataFrame(edges), width="stretch")
    else:
        st.info("No edge table available.")


def normalize_nodes(nodes) -> list[dict]:
    """Normalize node structures for dataframe display."""
    if isinstance(nodes, dict):
        rows = []
        for node_id, payload in nodes.items():
            if isinstance(payload, dict):
                rows.append({"id": node_id, **payload})
            else:
                rows.append({"id": node_id, "value": payload})
        return rows

    if isinstance(nodes, list):
        rows = []
        for node in nodes:
            if isinstance(node, dict):
                rows.append(node)
            else:
                rows.append({"id": str(node)})
        return rows

    return []


def normalize_edges(edges) -> list[dict]:
    """Normalize edge structures for dataframe display."""
    if isinstance(edges, dict):
        rows = []
        for edge_id, payload in edges.items():
            if isinstance(payload, dict):
                rows.append({"id": edge_id, **payload})
            else:
                rows.append({"id": edge_id, "value": payload})
        return rows

    if isinstance(edges, list):
        rows = []
        for edge in edges:
            if isinstance(edge, dict):
                rows.append(edge)
            elif isinstance(edge, (list, tuple)) and len(edge) >= 2:
                rows.append({"source": edge[0], "target": edge[1]})
            else:
                rows.append({"edge": str(edge)})
        return rows

    return []


def render_summary_tables(compact: dict) -> None:
    """Render compact stack summaries."""
    summaries = []

    for key, value in compact.items():
        if key.endswith("_summary") and isinstance(value, dict):
            row = {"layer": key.replace("_summary", "")}
            row.update(value)
            summaries.append(row)

    if summaries:
        st.markdown("### Layer Summaries")
        st.dataframe(pd.DataFrame(summaries), width="stretch")


def render_stack_exports(payload: dict) -> None:
    """Render stack export downloads."""
    st.markdown("## Exports")

    profile_key = payload.get("profile_key", "profile")
    exports = payload.get("exports", {})

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        "Download Full Stack JSON",
        data=json_export(exports.get("full_stack", {})),
        file_name=f"{profile_key}_identity_stack.json",
        mime="application/json",
    )

    c2.download_button(
        "Download Compact Stack JSON",
        data=json_export(exports.get("compact", {})),
        file_name=f"{profile_key}_identity_stack_compact.json",
        mime="application/json",
    )

    c3.download_button(
        "Download Audit JSON",
        data=json_export(exports.get("audit", {})),
        file_name=f"{profile_key}_identity_stack_audit.json",
        mime="application/json",
    )


def render_morphology_exports(payload: dict) -> None:
    """Render morphology export downloads."""
    st.markdown("## Exports")

    profile_a = payload.get("profile_a", "profile_a")
    profile_b = payload.get("profile_b", "profile_b")

    c1, c2 = st.columns(2)

    c1.download_button(
        "Download Morphology JSON",
        data=json_export(payload.get("exports", {}).get("morphology", {})),
        file_name=f"{profile_a}_to_{profile_b}_morphology.json",
        mime="application/json",
    )

    c2.download_button(
        "Download Metrics JSON",
        data=json_export(payload.get("metrics", {})),
        file_name=f"{profile_a}_to_{profile_b}_morphology_metrics.json",
        mime="application/json",
    )


def render_errors(payload: dict) -> None:
    """Render payload errors and warnings."""
    for warning in payload.get("warnings", []):
        st.warning(warning)

    for error in payload.get("errors", []):
        st.error(error)


def format_number(value) -> str:
    """Format numbers safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"