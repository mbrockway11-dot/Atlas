"""Morphology Lab page."""

from __future__ import annotations

from typing import Any

import pandas as pd
import streamlit as st

from atlas.services.graph_service import (
    build_morphology_payload,
    json_export,
    list_graph_profiles,
    safe_filename,
)


def render_morphology_lab_page() -> None:
    """Render Morphology Lab page."""
    st.header("Morphology Lab")
    st.caption(
        "Compare two Identity Graph Stacks as structural transformations: "
        "edits, mutation scores, topology shifts, and resonance shifts."
    )

    profiles = list_graph_profiles()

    if len(profiles) < 2:
        st.info("Build at least two profiles first.")
        return

    col_a, col_b = st.columns(2)

    with col_a:
        profile_a = st.selectbox(
            "Profile A",
            profiles,
            index=0,
            key="morphology_profile_a",
        )

    with col_b:
        profile_b = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="morphology_profile_b",
        )

    if profile_a == profile_b:
        st.warning("Select two different profiles.")
        return

    if not st.button("Compare Morphology", type="primary"):
        st.info("Select two profiles and compare morphology.")
        return

    with st.spinner("Comparing graph morphology..."):
        payload = build_morphology_payload(profile_a, profile_b)

    if not payload.get("success"):
        st.error("Morphology comparison failed.")
        for error in payload.get("errors", []):
            st.error(error)
        st.json(payload)
        return

    data = payload["data"]["morphology_data"]

    render_morphology_summary(data, payload)
    render_edit_counts(data)
    render_mutation_scores(data)
    render_genome_mutation(data)
    render_topology_mutation(data)
    render_resonance_mutation(data)
    render_exports(profile_a, profile_b, data)


def render_morphology_summary(data: dict[str, Any], payload: dict[str, Any]) -> None:
    """Render top-level morphology summary."""
    st.markdown("## Morphology Summary")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Source", metrics.get("source", "n/a"))
    c2.metric("Target", metrics.get("target", "n/a"))
    c3.metric("Distance", format_float(metrics.get("distance")))
    c4.metric("Class", metrics.get("morphology_class", "n/a"))

    c5, c6 = st.columns(2)
    c5.metric("Similarity", format_float(metrics.get("similarity")))
    c6.metric("Mutation Score", format_float(metrics.get("mutation_score")))

    with st.expander("Raw Summary JSON", expanded=False):
        st.json(
            {
                "metrics": metrics,
                "summary": data.get("summary", {}),
            }
        )


def render_edit_counts(data: dict[str, Any]) -> None:
    """Render edit counts."""
    st.markdown("## Edit Counts")

    edit_counts = data.get("edit_counts", {})

    render_dict_table(edit_counts, "edit", "count", "No edit count data available.")


def render_mutation_scores(data: dict[str, Any]) -> None:
    """Render mutation scores."""
    st.markdown("## Mutation Scores")

    scores = data.get("mutation_scores", {})

    render_dict_table(scores, "metric", "score", "No mutation scores available.")


def render_genome_mutation(data: dict[str, Any]) -> None:
    """Render genome mutation."""
    st.markdown("## Genome Mutation")

    genome = data.get("genome_mutation", {})

    render_dict_table(genome, "metric", "value", "No genome mutation data available.")


def render_topology_mutation(data: dict[str, Any]) -> None:
    """Render topology mutation."""
    st.markdown("## Topology Mutation")

    topology = data.get("topology_mutation", {})

    render_dict_table(topology, "metric", "value", "No topology mutation data available.")


def render_resonance_mutation(data: dict[str, Any]) -> None:
    """Render resonance mutation."""
    st.markdown("## Resonance Mutation")

    resonance = data.get("resonance_mutation", {})

    render_dict_table(resonance, "metric", "value", "No resonance mutation data available.")


def render_dict_table(
    data: dict[str, Any],
    key_name: str,
    value_name: str,
    empty_message: str,
) -> None:
    """Render dictionary as dataframe."""
    if not data:
        st.info(empty_message)
        return

    dataframe = pd.DataFrame(
        [
            {
                key_name: key,
                value_name: format_table_value(value),
            }
            for key, value in data.items()
        ]
    )

    st.dataframe(dataframe, width="stretch")

    if dataframe.shape[0] > 0:
        st.download_button(
            f"Download {key_name}_{value_name}.csv",
            data=dataframe.to_csv(index=False).encode("utf-8"),
            file_name=f"{key_name}_{value_name}.csv",
            mime="text/csv",
        )


def render_exports(profile_a: str, profile_b: str, data: dict[str, Any]) -> None:
    """Render morphology JSON export."""
    st.markdown("## Exports")

    file_name = (
        f"{safe_filename(profile_a)}_to_{safe_filename(profile_b)}_morphology.json"
    )

    st.download_button(
        label="Download morphology JSON",
        data=json_export(data),
        file_name=file_name,
        mime="application/json",
    )

    with st.expander("Raw Morphology JSON", expanded=False):
        st.json(data)


def format_float(value: Any) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_table_value(value: Any) -> str:
    """Format table values safely."""
    if isinstance(value, float):
        return f"{value:.4f}"

    if isinstance(value, (list, dict)):
        return json_export(value)

    return str(value)