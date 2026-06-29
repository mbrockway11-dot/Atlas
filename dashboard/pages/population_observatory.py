"""Population Observatory page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.calibration.nearest_neighbor import (
    find_nearest_neighbors,
    neighbor_result_to_dict,
)
from atlas.calibration.population_graph import (
    build_population_graph,
    population_graph_to_dict,
)
from atlas.calibration.similarity_matrix import (
    build_similarity_matrix_from_library,
    similarity_matrix_to_dict,
)


DEFAULT_PROFILE_DIR = Path("output/library/profiles")


def render_population_observatory_page() -> None:
    """Render Population Observatory."""
    st.header("Population Observatory")
    st.caption("Explore Atlas population metadata, similarity, and graph structure.")

    profile_dir = st.text_input(
        "Profile library directory",
        value=str(DEFAULT_PROFILE_DIR),
    )

    root = Path(profile_dir)

    if not root.exists():
        st.error(f"Profile directory not found: {root}")
        return

    records = load_population_records(root)

    if not records:
        st.warning("No profiles found.")
        return

    dataframe = pd.DataFrame(records)

    render_population_summary(dataframe)
    render_population_table(dataframe)
    render_population_intelligence(root, dataframe)
    render_profile_detail(root, dataframe)


def load_population_records(root: Path) -> list[dict]:
    """Load profile intake records."""
    records: list[dict] = []

    for profile_path in sorted(root.iterdir()):
        if not profile_path.is_dir():
            continue

        acf_path = profile_path / "profile.acf.json"
        intake_path = profile_path / "profile.intake.json"

        if not acf_path.exists():
            continue

        intake = {}

        if intake_path.exists():
            try:
                intake = json.loads(
                    intake_path.read_text(encoding="utf-8")
                )
            except json.JSONDecodeError:
                intake = {}

        records.append(
            {
                "slug": profile_path.name,
                "name": intake.get("name", profile_path.name),
                "birth_date": intake.get("birth_date", ""),
                "birth_time": intake.get("birth_time", "Unknown"),
                "birth_place": intake.get("birth_place", ""),
                "source_file": intake.get("source_file", ""),
                "row_number": intake.get("row_number", ""),
                "has_acf": acf_path.exists(),
                "has_intake": intake_path.exists(),
            }
        )

    return records


def render_population_summary(dataframe: pd.DataFrame) -> None:
    """Render population summary cards."""
    st.markdown("## Population Summary")

    total = len(dataframe)
    with_intake = int(dataframe["has_intake"].sum())
    unknown_times = int(
        (dataframe["birth_time"].fillna("Unknown") == "Unknown").sum()
    )
    known_times = total - unknown_times

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Profiles", total)
    c2.metric("With Intake Metadata", with_intake)
    c3.metric("Known Birth Times", known_times)
    c4.metric("Unknown Birth Times", unknown_times)


def render_population_table(dataframe: pd.DataFrame) -> None:
    """Render searchable population table."""
    st.markdown("## Population Table")

    search = st.text_input("Search profiles", "")

    filtered = dataframe.copy()

    if search.strip():
        query = search.casefold().strip()
        filtered = filtered[
            filtered["name"].str.casefold().str.contains(query)
            | filtered["slug"].str.casefold().str.contains(query)
        ]

    st.dataframe(
        filtered[
            [
                "name",
                "birth_date",
                "birth_time",
                "birth_place",
                "slug",
                "has_intake",
            ]
        ],
        use_container_width=True,
    )

    st.download_button(
        label="Download population table CSV",
        data=filtered.to_csv(index=False),
        file_name="atlas_population_observatory.csv",
        mime="text/csv",
    )


def render_population_intelligence(
    root: Path,
    dataframe: pd.DataFrame,
) -> None:
    """Render similarity matrix, nearest neighbors, and population graph."""
    st.markdown("## Population Intelligence")

    with st.spinner("Building similarity matrix..."):
        matrix = build_similarity_matrix_from_library(root)

    threshold = st.slider(
        "Population graph similarity threshold",
        min_value=0.0,
        max_value=1.0,
        value=0.85,
        step=0.01,
    )

    graph = build_population_graph(
        matrix,
        threshold=threshold,
    )

    m1, m2, m3, m4 = st.columns(4)

    m1.metric("Similarity Pairs", matrix.pair_count)
    m2.metric(
        "Mean Similarity",
        round(matrix.summary.get("mean_similarity", 0.0), 4),
    )
    m3.metric("Graph Edges", graph.edge_count)
    m4.metric(
        "Most Connected",
        graph.summary.get("most_connected_identity") or "None",
    )

    with st.expander("Similarity Matrix Summary", expanded=False):
        st.json(matrix.summary)

    with st.expander("Population Graph Summary", expanded=False):
        st.json(graph.summary)

    selected = st.selectbox(
        "Nearest neighbor query",
        dataframe["name"].tolist(),
        key="nearest_neighbor_query",
    )

    limit = st.slider(
        "Neighbor limit",
        min_value=1,
        max_value=25,
        value=10,
        step=1,
    )

    neighbors = find_nearest_neighbors(
        matrix,
        selected,
        limit=limit,
    )

    st.markdown(f"### Nearest Neighbors for {selected}")

    if neighbors.neighbors:
        st.dataframe(
            pd.DataFrame(neighbors.neighbors),
            use_container_width=True,
        )
    else:
        st.info("No neighbors found.")

    c1, c2, c3 = st.columns(3)

    c1.download_button(
        label="Download similarity matrix JSON",
        data=json.dumps(
            similarity_matrix_to_dict(matrix),
            indent=2,
            sort_keys=True,
        ),
        file_name="similarity_matrix.json",
        mime="application/json",
    )

    c2.download_button(
        label="Download population graph JSON",
        data=json.dumps(
            population_graph_to_dict(graph),
            indent=2,
            sort_keys=True,
        ),
        file_name="population_graph.json",
        mime="application/json",
    )

    c3.download_button(
        label="Download neighbors JSON",
        data=json.dumps(
            neighbor_result_to_dict(neighbors),
            indent=2,
            sort_keys=True,
        ),
        file_name=f"{slugify(selected)}_neighbors.json",
        mime="application/json",
    )


def render_profile_detail(
    root: Path,
    dataframe: pd.DataFrame,
) -> None:
    """Render selected profile details."""
    st.markdown("## Profile Detail")

    names = dataframe["name"].tolist()

    selected = st.selectbox(
        "Select profile",
        names,
    )

    row = dataframe[dataframe["name"] == selected].iloc[0]
    profile_path = root / row["slug"]

    c1, c2, c3 = st.columns(3)

    c1.metric("Name", row["name"])
    c2.metric("Birth Date", row["birth_date"] or "Unknown")
    c3.metric("Birth Time", row["birth_time"] or "Unknown")

    st.write(f"**Birth Place:** {row['birth_place'] or 'Unknown'}")
    st.write(f"**Profile Folder:** `{profile_path}`")

    intake_path = profile_path / "profile.intake.json"
    acf_path = profile_path / "profile.acf.json"

    with st.expander("Intake Metadata JSON", expanded=False):
        if intake_path.exists():
            st.json(
                json.loads(
                    intake_path.read_text(encoding="utf-8")
                )
            )
        else:
            st.info("No profile.intake.json found.")

    with st.expander("ACF Profile JSON Preview", expanded=False):
        if acf_path.exists():
            acf = json.loads(acf_path.read_text(encoding="utf-8"))
            st.json(acf)
        else:
            st.info("No profile.acf.json found.")


def slugify(value: str) -> str:
    """Build safe filename slug."""
    return (
        value.casefold()
        .replace(" ", "_")
        .replace("/", "_")
        .replace("\\", "_")
    )