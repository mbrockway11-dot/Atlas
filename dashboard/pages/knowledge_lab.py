
"""Knowledge Lab dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.knowledge_service import (
    build_knowledge_lab_payload,
    list_knowledge_profiles,
)


def render_knowledge_lab_page() -> None:
    """Render Knowledge Lab."""
    st.header("Knowledge Lab")
    st.caption("Knowledge interpretation, durable hypotheses, evidence graph, and discovery memory.")

    profiles = list_knowledge_profiles()

    if not profiles:
        st.warning("No saved profiles found.")
        return

    c1, c2, c3 = st.columns(3)

    with c1:
        profile_key = st.selectbox("Profile", profiles, key="knowledge_lab_profile")

    with c2:
        discovery_limit = st.slider("Discovery sample", 2, min(100, len(profiles)), min(25, len(profiles)))

    with c3:
        force = st.toggle("Force recompile profile", value=False)

    if not st.button("Build Knowledge Lab", type="primary"):
        st.info("Choose a profile and build the Knowledge Lab payload.")
        return

    with st.spinner("Building Knowledge Lab..."):
        result = build_knowledge_lab_payload(
            profile_key,
            discovery_limit=discovery_limit,
            force=force,
        )

    if not result.get("success"):
        st.error("Knowledge Lab failed.")
        st.json(result)
        return

    interpretation = result.get("knowledge_interpretation", {})
    graph = result.get("knowledge_graph", {})

    render_interpretation(interpretation)
    render_knowledge_graph(graph)
    render_raw(result)


def render_interpretation(interpretation: dict) -> None:
    """Render profile knowledge interpretation."""
    st.markdown("## Profile Knowledge Interpretation")
    st.info(interpretation.get("summary", ""))

    sections = interpretation.get("sections", {}) or {}

    tabs = st.tabs([
        "Mind",
        "Stress",
        "Learning",
        "Growth",
        "Relationship",
        "Career",
    ])

    keys = ["mind", "stress", "learning", "growth", "relationship", "career"]

    for tab, key in zip(tabs, keys):
        with tab:
            section = sections.get(key, {})
            st.markdown(f"### {key.title()} Architecture")
            st.write(section.get("summary", ""))

            rows = []
            for field, value in section.items():
                if field in {"success", "domain", "summary"}:
                    continue
                rows.append({"field": field, "value": value})

            if rows:
                st.dataframe(pd.DataFrame(rows), width="stretch")
            else:
                st.json(section)


def render_knowledge_graph(graph_payload: dict) -> None:
    """Render knowledge graph."""
    st.markdown("## Knowledge Graph")

    st.info(graph_payload.get("summary", ""))

    graph = graph_payload.get("evidence_graph", {}) or {}
    summary = graph.get("summary", {}) or {}

    c1, c2, c3 = st.columns(3)
    c1.metric("Hypotheses", summary.get("hypothesis_count", 0))
    c2.metric("Insights", summary.get("insight_count", 0))
    c3.metric("Evidence Items", summary.get("evidence_count", 0))

    tabs = st.tabs(["Nodes", "Edges", "Knowledge Base"])

    with tabs[0]:
        nodes = graph.get("nodes", [])
        if nodes:
            st.dataframe(pd.DataFrame(nodes), width="stretch")
        else:
            st.info("No graph nodes available.")

    with tabs[1]:
        edges = graph.get("edges", [])
        if edges:
            st.dataframe(pd.DataFrame(edges), width="stretch")
        else:
            st.info("No graph edges available.")

    with tabs[2]:
        st.json(graph_payload.get("knowledge_base", {}))


def render_raw(result: dict) -> None:
    """Render raw payload."""
    with st.expander("Raw Knowledge Lab JSON", expanded=False):
        st.json(result)
