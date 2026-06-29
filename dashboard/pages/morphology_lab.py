"""Morphology Lab page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.graph.identity_morphology import (
    compare_identity_morphology,
    identity_morphology_to_dict,
)
from atlas.graph.identity_stack import build_identity_graph_stack
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles


def render_morphology_lab_page() -> None:
    """Render Morphology Lab page."""
    st.header("Morphology Lab")
    st.caption(
        "Compare two Identity Graph Stacks as structural transformations: "
        "node edits, edge edits, motif mutation, genome mutation, topology "
        "mutation, and resonance mutation."
    )

    profiles = list_saved_profiles()

    if len(profiles) < 2:
        st.info("Build at least two saved profiles first.")
        return

    col1, col2 = st.columns(2)

    with col1:
        profile_a_key = st.selectbox(
            "Profile A",
            profiles,
            key="morphology_profile_a",
        )

    with col2:
        profile_b_key = st.selectbox(
            "Profile B",
            profiles,
            index=1 if len(profiles) > 1 else 0,
            key="morphology_profile_b",
        )

    if profile_a_key == profile_b_key:
        st.warning("Choose two different profiles.")
        return

    if not st.button("Compare Morphology", type="primary"):
        return

    acf_a = load_acf(profile_a_key)
    acf_b = load_acf(profile_b_key)

    if acf_a is None or acf_b is None:
        st.error("Could not load one or both profile.acf.json files.")
        return

    stack_a = build_identity_graph_stack(acf_a)
    stack_b = build_identity_graph_stack(acf_b)

    morphology = compare_identity_morphology(stack_a, stack_b)
    data = identity_morphology_to_dict(morphology)

    render_morphology_summary(data)
    render_edit_counts(data)
    render_mutation_scores(data)
    render_genome_mutation(data)
    render_topology_mutation(data)
    render_resonance_mutation(data)

    with st.expander("Raw Morphology JSON"):
        st.json(data)


def load_acf(profile_key: str) -> dict | None:
    """Load saved ACF profile."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    try:
        return json.loads(acf_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def render_morphology_summary(data: dict) -> None:
    """Render top-level morphology summary."""
    st.markdown("## Morphology Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Profile A", data.get("name_a", "n/a"))
    c2.metric("Profile B", data.get("name_b", "n/a"))
    c3.metric(
        "Edit Distance",
        format_float(data.get("structural_edit_distance", 0)),
    )
    c4.metric("Morphology Class", data.get("morphology_class", "n/a"))

    summary = data.get("summary", {})

    st.dataframe(
        dict_to_dataframe(summary, "metric", "value"),
        width="stretch",
    )


def render_edit_counts(data: dict) -> None:
    """Render node and edge edit counts."""
    st.markdown("## Structural Edits")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Node Overlap", format_float(data.get("node_overlap", 0)))
    c2.metric("Edge Overlap", format_float(data.get("edge_overlap", 0)))
    c3.metric("Shared Nodes", data.get("shared_node_count", 0))
    c4.metric("Shared Edges", data.get("shared_edge_count", 0))

    rows = [
        {"edit": "added_nodes", "count": data.get("added_node_count", 0)},
        {"edit": "removed_nodes", "count": data.get("removed_node_count", 0)},
        {"edit": "added_edges", "count": data.get("added_edge_count", 0)},
        {"edit": "removed_edges", "count": data.get("removed_edge_count", 0)},
    ]

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    if not dataframe.empty:
        st.bar_chart(
            dataframe.set_index("edit")["count"],
            width="stretch",
        )


def render_mutation_scores(data: dict) -> None:
    """Render mutation scores."""
    st.markdown("## Mutation Scores")

    rows = [
        {
            "mutation_layer": "motif",
            "score": data.get("motif_mutation", {}).get("mutation_score", 0),
        },
        {
            "mutation_layer": "genome",
            "score": data.get("genome_mutation", {}).get("mutation_score", 0),
        },
        {
            "mutation_layer": "topology",
            "score": data.get("topology_mutation", {}).get("mutation_score", 0),
        },
        {
            "mutation_layer": "resonance",
            "score": data.get("resonance_mutation", {}).get("mutation_score", 0),
        },
    ]

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    if not dataframe.empty:
        st.bar_chart(
            dataframe.set_index("mutation_layer")["score"],
            width="stretch",
        )


def render_genome_mutation(data: dict) -> None:
    """Render genome mutation details."""
    st.markdown("## Genome Mutation")

    genome = data.get("genome_mutation", {})

    c1, c2, c3 = st.columns(3)

    c1.metric("Shared Sequence", len(genome.get("shared_sequence", [])))
    c2.metric("Added Sequence", len(genome.get("added_sequence", [])))
    c3.metric("Removed Sequence", len(genome.get("removed_sequence", [])))

    if genome.get("shared_sequence"):
        st.markdown("### Shared Genome Sequence")
        st.code(" → ".join(genome["shared_sequence"]))

    if genome.get("added_sequence"):
        st.markdown("### Added Genome Sequence")
        st.code(" → ".join(genome["added_sequence"]))

    if genome.get("removed_sequence"):
        st.markdown("### Removed Genome Sequence")
        st.code(" → ".join(genome["removed_sequence"]))

    st.markdown("### Genome Score Deltas")
    st.dataframe(
        dict_to_dataframe(genome.get("score_deltas", {}), "score", "delta"),
        width="stretch",
    )


def render_topology_mutation(data: dict) -> None:
    """Render topology mutation details."""
    st.markdown("## Topology Mutation")

    topology = data.get("topology_mutation", {})

    c1, c2, c3 = st.columns(3)

    c1.metric("From Class", topology.get("from_class", "n/a"))
    c2.metric("To Class", topology.get("to_class", "n/a"))
    c3.metric(
        "Mutation Score",
        format_float(topology.get("mutation_score", 0)),
    )

    rows = [
        {
            "field": "flow",
            "from": topology.get("from_flow", "n/a"),
            "to": topology.get("to_flow", "n/a"),
        },
        {
            "field": "organization",
            "from": topology.get("from_organization", "n/a"),
            "to": topology.get("to_organization", "n/a"),
        },
        {
            "field": "stability",
            "from": topology.get("from_stability", "n/a"),
            "to": topology.get("to_stability", "n/a"),
        },
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")

    st.markdown("### Topology Score Deltas")
    st.dataframe(
        dict_to_dataframe(topology.get("score_deltas", {}), "axis", "delta"),
        width="stretch",
    )


def render_resonance_mutation(data: dict) -> None:
    """Render resonance mutation details."""
    st.markdown("## Resonance Mutation")

    resonance = data.get("resonance_mutation", {})

    c1, c2, c3 = st.columns(3)

    c1.metric("From Class", resonance.get("from_class", "n/a"))
    c2.metric("To Class", resonance.get("to_class", "n/a"))
    c3.metric(
        "Mutation Score",
        format_float(resonance.get("mutation_score", 0)),
    )

    rows = [
        {
            "field": "activation",
            "from": resonance.get("from_activation", "n/a"),
            "to": resonance.get("to_activation", "n/a"),
        },
        {
            "field": "propagation",
            "from": resonance.get("from_propagation", "n/a"),
            "to": resonance.get("to_propagation", "n/a"),
        },
        {
            "field": "damping",
            "from": resonance.get("from_damping", "n/a"),
            "to": resonance.get("to_damping", "n/a"),
        },
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")

    st.markdown("### Resonance Score Deltas")
    st.dataframe(
        dict_to_dataframe(resonance.get("score_deltas", {}), "axis", "delta"),
        width="stretch",
    )


def dict_to_dataframe(data: dict, key_name: str, value_name: str) -> pd.DataFrame:
    """Convert dict to display-safe dataframe."""
    return pd.DataFrame(
        [
            {
                key_name: str(key),
                value_name: format_table_value(value),
            }
            for key, value in data.items()
        ]
    )


def format_float(value) -> str:
    """Format float safely."""
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "n/a"


def format_table_value(value) -> str:
    """Format mixed values safely for Streamlit tables."""
    if value is None:
        return "n/a"

    if isinstance(value, float):
        return f"{value:.4f}"

    if isinstance(value, (list, tuple)):
        return " → ".join(str(item) for item in value)

    if isinstance(value, dict):
        return json.dumps(value, sort_keys=True)

    return str(value)