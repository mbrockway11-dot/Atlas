"""Population Observatory dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.population_observatory_service import (
    DEFAULT_PROFILE_DIR,
    build_neighbor_payload,
    build_population_observatory_payload,
    collect_population_identities,
    json_export,
    load_profile_detail,
    slugify,
)


def render_population_observatory_page() -> None:
    """Render Population Observatory dashboard."""
    st.header("Population Observatory")
    st.caption("Browse population records, similarity structure, and profile details.")

    profile_dir = st.text_input(
        "Profile library directory",
        value=str(DEFAULT_PROFILE_DIR),
    )

    threshold = st.slider(
        "Similarity graph threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01,
    )

    with st.spinner("Loading population observatory payload..."):
        payload = build_population_observatory_payload(
            profile_dir,
            threshold=threshold,
        )

    if not payload.get("success"):
        for error in payload.get("errors", []):
            st.error(error)

        with st.expander("Raw service payload", expanded=False):
            st.json(payload)
        return

    records = payload.get("records", [])
    dataframe = pd.DataFrame(records)

    render_population_summary(payload)
    render_population_table(dataframe)
    render_population_intelligence(payload)
    render_profile_detail(profile_dir, dataframe)


def render_population_summary(payload: dict) -> None:
    """Render population summary cards."""
    st.markdown("## Population Summary")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", metrics.get("profiles", 0))
    c2.metric("With Intake Metadata", metrics.get("with_intake", 0))
    c3.metric("With ACF", metrics.get("with_acf", 0))
    c4.metric("Known Birth Times", metrics.get("known_birth_times", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Unknown Birth Times", metrics.get("unknown_birth_times", 0))
    c6.metric("Similarity Pairs", metrics.get("similarity_pairs", 0))
    c7.metric("Graph Edges", metrics.get("graph_edges", 0))
    c8.metric("Graph Density", round(metrics.get("graph_density", 0.0), 4))

    with st.expander("Population Metrics JSON", expanded=False):
        st.json(metrics)


def render_population_table(dataframe: pd.DataFrame) -> None:
    """Render searchable population table."""
    st.markdown("## Population Table")

    if dataframe.empty:
        st.info("No population records available.")
        return

    search = st.text_input("Search profiles", "")

    filtered = dataframe.copy()

    if search:
        needle = search.casefold()
        filtered = filtered[
            filtered.apply(
                lambda row: needle
                in " ".join(str(value).casefold() for value in row.values),
                axis=1,
            )
        ]

    st.dataframe(filtered, width="stretch")

    st.download_button(
        "Download population_records.csv",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="population_records.csv",
        mime="text/csv",
    )


def render_population_intelligence(payload: dict) -> None:
    """Render similarity matrix, nearest neighbors, and graph exports."""
    st.markdown("## Population Intelligence")

    data = payload.get("data", {})
    matrix = data.get("matrix")
    graph = data.get("graph")

    if matrix is None or graph is None:
        st.info("Population intelligence artifacts are unavailable.")
        return

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Similarity Pairs", metrics.get("similarity_pairs", 0))
    c2.metric("Mean Similarity", round(metrics.get("mean_similarity", 0.0), 4))
    c3.metric("Graph Edges", metrics.get("graph_edges", 0))
    c4.metric("Threshold", payload.get("threshold", 0.85))

    with st.expander("Similarity Matrix Summary", expanded=False):
        st.json(getattr(matrix, "summary", {}))

    with st.expander("Population Graph Summary", expanded=False):
        st.json(getattr(graph, "summary", {}))

    render_neighbor_explorer(matrix)
    render_population_exports(data)


def render_neighbor_explorer(matrix) -> None:
    """Render nearest-neighbor explorer."""
    st.markdown("### Nearest Neighbor Explorer")

    identities = collect_population_identities(matrix)

    if not identities:
        st.info("No identities available for nearest-neighbor query.")
        return

    selected = st.selectbox(
        "Nearest neighbor query",
        identities,
        key="nearest_neighbor_query",
    )

    max_limit = min(25, max(1, len(identities) - 1))

    limit = st.slider(
        "Neighbor limit",
        min_value=1,
        max_value=max_limit,
        value=min(10, max_limit),
        step=1,
    )

    neighbor_payload = build_neighbor_payload(matrix, selected, limit=limit)
    neighbors = neighbor_payload.get("neighbors", [])

    st.markdown(f"#### Nearest Neighbors for {selected}")

    if neighbors:
        st.dataframe(pd.DataFrame(neighbors), width="stretch")
    else:
        st.info("No neighbors found.")

    with st.expander("Neighbor Report JSON", expanded=False):
        st.json(neighbor_payload.get("report", {}))

    st.download_button(
        label="Download neighbors JSON",
        data=json_export(neighbor_payload.get("report", {})),
        file_name=f"{slugify(selected)}_neighbors.json",
        mime="application/json",
    )


def render_population_exports(data: dict) -> None:
    """Render population intelligence export buttons."""
    st.markdown("### Exports")

    c1, c2 = st.columns(2)

    c1.download_button(
        label="Download similarity matrix JSON",
        data=json_export(data.get("matrix_dict", {})),
        file_name="similarity_matrix.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download population graph JSON",
        data=json_export(data.get("graph_dict", {})),
        file_name="population_graph.json",
        mime="application/json",
    )


def render_profile_detail(profile_dir: str, dataframe: pd.DataFrame) -> None:
    """Render selected profile details."""
    st.markdown("## Profile Detail")

    if dataframe.empty or "slug" not in dataframe.columns:
        st.info("No profiles available.")
        return

    selected = st.selectbox(
        "Select profile",
        dataframe["slug"].tolist(),
        key="population_observatory_profile_detail",
    )

    detail = load_profile_detail(selected, profile_dir)

    st.write(f"**Profile Folder:** `{detail.get('profile_dir')}`")

    available = detail.get("available", [])
    missing = detail.get("missing", [])

    c1, c2 = st.columns(2)
    c1.metric("Available Files", len(available))
    c2.metric("Missing Files", len(missing))

    if missing:
        st.warning("Missing files: " + ", ".join(missing))

    tabs = st.tabs(["Intake", "ACF", "Raw Detail"])

    with tabs[0]:
        intake = detail.get("intake")
        if intake is None:
            st.info("No profile.intake.json found.")
        else:
            st.json(intake)

    with tabs[1]:
        acf = detail.get("acf")
        if acf is None:
            st.info("No profile.acf.json found.")
        else:
            st.json(acf)

    with tabs[2]:
        st.json(detail)