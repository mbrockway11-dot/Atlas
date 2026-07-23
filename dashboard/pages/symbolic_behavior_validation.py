"""Symbolic feature and documented-behavior association dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

from atlas.services.symbolic_behavior_service import build_symbolic_behavior_dashboard_payload


def render_symbolic_behavior_validation_page() -> None:
    st.title("Symbolic–Behavior Validation")
    st.caption("Research only. Symbolic features are deterministic transforms; behavioral claims require independent documented evidence.")
    initial = build_symbolic_behavior_dashboard_payload()
    if not initial.get("success"):
        st.warning("Run scripts/run_symbolic_behavior_validation.py first.")
        st.json(initial)
        return
    behavior_options = ["All", *initial["filters"]["behavior_options"]]
    family_options = ["All", *initial["filters"]["feature_family_options"]]
    left, right = st.columns(2)
    selected_behavior = left.selectbox("Behavior", behavior_options)
    selected_family = right.selectbox("Symbolic feature family", family_options)
    payload = build_symbolic_behavior_dashboard_payload(
        behavior_id=None if selected_behavior == "All" else selected_behavior,
        feature_family=None if selected_family == "All" else selected_family,
    )
    metrics = payload["metrics"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", metrics.get("profiles", 0))
    c2.metric("Observations", metrics.get("behavior_observations", 0))
    c3.metric("Associations Tested", metrics.get("tested_associations", 0))
    c4.metric("Retained Findings", metrics.get("retained_findings", 0))
    st.error("A symbolic match is not behavioral evidence. Name numerology, Gematria, and Kamea share one dependency family and never count as three confirmations.")

    overview, population, observations, features, statistics, independence, quality, sources, downloads = st.tabs([
        "Overview", "Population Index", "Behavior Evidence", "Feature Matrix", "Statistics", "Independence Audit", "Quality", "Sources", "Downloads"
    ])
    data = payload["data"]
    with overview:
        st.subheader("Behavior taxonomy")
        st.dataframe(pd.DataFrame(data.get("taxonomy", [])), use_container_width=True, hide_index=True)
        st.json(data.get("summary", {}))
    with population:
        population_summary = data.get("population_summary", {})
        if not population_summary:
            st.info("Run scripts/run_symbolic_behavior_validation.py --all-profiles to build the complete predictor index.")
        else:
            counts = population_summary.get("counts", {})
            p1, p2, p3, p4 = st.columns(4)
            p1.metric("Indexed Profiles", counts.get("profiles", 0))
            p2.metric("Feature Ready", counts.get("feature_ready_profiles", 0))
            p3.metric("Behavior Annotated", counts.get("behavior_annotated_profiles", 0))
            p4.metric("Need Annotation", counts.get("profiles_needing_behavior_annotation", 0))
            st.warning("Unannotated profiles are predictor-only records. They are not behavior-negative controls.")
            st.dataframe(pd.DataFrame(data.get("population_coverage", [])), use_container_width=True, hide_index=True)
            st.dataframe(pd.DataFrame(data.get("population_readiness", [])), use_container_width=True, hide_index=True)
    with observations:
        st.info("Registry non-membership means not documented in this pilot—not absence of the behavior.")
        st.dataframe(pd.DataFrame(data.get("observations", [])), use_container_width=True, hide_index=True)
    with features:
        frame = pd.DataFrame(data.get("features", []))
        st.dataframe(frame, use_container_width=True, hide_index=True)
        if not frame.empty:
            counts = frame.groupby(["feature_family", "independence_group"], as_index=False).size()
            st.plotly_chart(px.bar(counts, x="feature_family", y="size", color="independence_group", title="Features by declared dependency group"), use_container_width=True)
    with statistics:
        frame = pd.DataFrame(data.get("associations", []))
        st.dataframe(frame, use_container_width=True, hide_index=True)
        if not frame.empty:
            chart = frame.nsmallest(min(30, len(frame)), "corrected_p_value")
            st.plotly_chart(px.scatter(chart, x="effect_size", y="corrected_p_value", color="independence_group", hover_data=["behavior_id", "feature_id"], title="Largest corrected exploratory associations"), use_container_width=True)
        st.warning("Nominal p-values are displayed for auditability but are not findings. Only corrected, sufficiently powered, independently replicated results can be retained.")
    with independence:
        st.dataframe(pd.DataFrame(data.get("independence_audit", [])), use_container_width=True, hide_index=True)
    with quality:
        st.json(data.get("quality", {}))
        st.dataframe(pd.DataFrame(data.get("profile_quality", [])), use_container_width=True, hide_index=True)
    with sources:
        for source in data.get("sources", []):
            st.markdown(f"- [{source.get('title')}]({source.get('url')}) — {source.get('publisher')} (`{source.get('source_id')}`)")
    with downloads:
        for item in payload.get("downloads", []):
            path = Path(item["path"])
            st.download_button(item["name"], data=path.read_bytes(), file_name=path.name, key=f"symbolic_behavior_download_{path.name}")


def render() -> None:
    render_symbolic_behavior_validation_page()
