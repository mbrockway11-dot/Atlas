"""Identity Stack Lab page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from atlas.graph.identity_stack import (
    build_identity_graph_stack,
    identity_graph_stack_to_dict,
)
from atlas.graph.stack_audit import (
    audit_identity_stack,
    stack_audit_to_dict,
)
from atlas.library.profile_library import LIBRARY_DIR, list_saved_profiles
from atlas.visualization import build_canonical_graph_figure


def render_identity_stack_lab_page() -> None:
    """Render Identity Stack Lab page."""
    st.header("Identity Stack Lab")
    st.caption(
        "Build the complete graph-native identity stack: "
        "CIG → STG → Motifs → Genome → Topology → Resonance."
    )

    profiles = list_saved_profiles()

    if not profiles:
        st.info("No saved profiles found. Build a profile first.")
        return

    profile_key = st.selectbox(
        "Profile",
        profiles,
        key="identity_stack_lab_profile",
    )

    graph_mode = st.selectbox(
        "Graph View",
        [
            "Structural Truth Graph only",
            "Both CIG and STG",
            "No graph",
        ],
        key="identity_stack_graph_mode",
    )

    graph_layout = st.selectbox(
        "Graph Layout",
        ["layered", "circular"],
        key="identity_stack_graph_layout",
    )

    if not st.button("Build Identity Stack", type="primary"):
        return

    acf = load_acf(profile_key)

    if acf is None:
        st.error("Could not load profile.acf.json for this profile.")
        return

    stack = build_identity_graph_stack(acf)
    stack_data = identity_graph_stack_to_dict(stack)

    audit = audit_identity_stack(stack_data)
    audit_data = stack_audit_to_dict(audit)

    render_stack_summary(stack_data)
    render_stack_audit(audit_data)

    if graph_mode != "No graph":
        render_graph_visualizations(
            stack_data=stack_data,
            graph_layout=graph_layout,
            graph_mode=graph_mode,
        )

    render_cig_summary(stack_data)
    render_stg_summary(stack_data)
    render_motif_summary(stack_data)
    render_genome_summary(stack_data)
    render_topology_summary(stack_data)
    render_resonance_summary(stack_data)
    render_download_exports(stack_data, audit_data)


def load_acf(profile_key: str) -> dict | None:
    """Load saved ACF profile."""
    acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

    if not acf_path.exists():
        return None

    try:
        return json.loads(acf_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def render_stack_audit(audit_data: dict) -> None:
    """Render Stack Audit dashboard."""
    st.markdown("## Stack Audit")

    summary = audit_data.get("summary", {})
    status = summary.get("status", "unknown")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Status", status)
    c2.metric("Valid", str(summary.get("valid", False)))
    c3.metric("Warnings", summary.get("warning_count", 0))
    c4.metric("Errors", summary.get("error_count", 0))

    if status == "healthy":
        st.success("Stack audit passed. No structural issues detected.")
    elif status == "warning":
        st.warning("Stack audit found warnings. Review before treating output as final.")
    elif status == "error":
        st.error("Stack audit found errors. Fix before trusting downstream analysis.")
    else:
        st.info("Stack audit status unknown.")

    issues = audit_data.get("issues", [])

    if not issues:
        return

    issue_rows = [
        {
            "severity": issue.get("severity"),
            "code": issue.get("code"),
            "message": issue.get("message"),
            "details": json.dumps(issue.get("details", {}), sort_keys=True),
        }
        for issue in issues
    ]

    st.markdown("### Audit Issues")
    st.dataframe(pd.DataFrame(issue_rows), width="stretch")

    st.markdown("### Suggested Fixes")
    for issue in issues:
        st.write(f"- **{issue.get('code')}**: {suggest_fix(issue.get('code'))}")


def suggest_fix(code: str | None) -> str:
    """Return suggested fix for audit code."""
    fixes = {
        "missing_construction_passes": (
            "Check Canonical Identity Graph construction. The stack may not be "
            "exporting CIG construction metadata."
        ),
        "unexpected_layer_count": (
            "Verify the profile generated all 21 layers: 3 ciphers × 7 planets."
        ),
        "within_cipher_visit_imbalance": (
            "Audit character preprocessing inside that cipher. A layer may be "
            "dropping or collapsing symbols."
        ),
        "cross_cipher_visit_imbalance": (
            "Compare ordinal, Hebrew literal, and Hebrew phonetic token streams. "
            "The phonetic layer may be shortening the name."
        ),
        "empty_cig": (
            "Rebuild the profile. The Canonical Identity Graph has no usable nodes."
        ),
        "fragmented_graph": (
            "Inspect disconnected components. Some layers may be producing isolated "
            "subgraphs."
        ),
        "over_connected_graph": (
            "Review edge construction and hub detection. The graph may be too dense "
            "to reveal structural bottlenecks."
        ),
        "high_hub_ratio": (
            "Tune hub classification thresholds. Too many nodes are being marked "
            "as hubs."
        ),
        "missing_edges": (
            "Check visit-history transition extraction. Nodes exist but edges were "
            "not generated."
        ),
        "compressed_edge_weights": (
            "Inspect edge accumulation across layers. Persistent edges may not be "
            "combining correctly."
        ),
        "dominant_singleton_edges": (
            "Consider stronger pruning or persistence thresholds to reduce one-off "
            "edges."
        ),
        "weak_structural_reduction": (
            "Improve STG pruning rules. Current reduction may be too conservative."
        ),
    }

    return fixes.get(code, "Review this rule manually.")


def render_graph_visualizations(
    *,
    stack_data: dict,
    graph_layout: str,
    graph_mode: str,
) -> None:
    """Render CIG and STG graph visualizations."""
    st.markdown("## Graph Visualizations")

    if graph_mode == "Both CIG and STG":
        tab_cig, tab_stg = st.tabs(
            [
                "Canonical Identity Graph",
                "Structural Truth Graph",
            ]
        )

        with tab_cig:
            render_cig_graph(stack_data, graph_layout)

        with tab_stg:
            render_stg_graph(stack_data, graph_layout)

    else:
        render_stg_graph(stack_data, graph_layout)


def render_cig_graph(stack_data: dict, graph_layout: str) -> None:
    """Render Canonical Identity Graph visualization."""
    cig_graph = stack_data.get("cig", {}).get("structural_attractor", {}).get(
        "graph",
        {},
    )

    if not has_graph_data(cig_graph):
        st.info("No CIG graph data available.")
        return

    st.caption(
        "Heavy debug view. This can be slow on large profiles because it draws "
        "the full canonical attractor graph."
    )

    figure = build_canonical_graph_figure(
        cig_graph,
        title="Canonical Identity Graph",
        layout=graph_layout,
    )

    st.plotly_chart(figure, width="stretch")


def render_stg_graph(stack_data: dict, graph_layout: str) -> None:
    """Render Structural Truth Graph visualization."""
    stg_graph = {
        "nodes": stack_data.get("stg", {}).get("nodes", {}),
        "edges": stack_data.get("stg", {}).get("edges", {}),
    }

    if not has_graph_data(stg_graph):
        st.info("No STG graph data available.")
        return

    st.caption(
        "Default lightweight view. This renders only the pruned Structural "
        "Truth Graph."
    )

    figure = build_canonical_graph_figure(
        stg_graph,
        title="Structural Truth Graph",
        layout=graph_layout,
    )

    st.plotly_chart(figure, width="stretch")


def has_graph_data(graph: dict) -> bool:
    """Return True if graph has nodes and edges."""
    return bool(graph.get("nodes")) and bool(graph.get("edges"))


def render_stack_summary(stack_data: dict) -> None:
    """Render top-level stack summary."""
    st.markdown("## Stack Summary")

    summary = stack_data.get("summary", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Name", stack_data.get("name", "n/a"))
    c2.metric("Topology Class", summary.get("topology_class", "n/a"))
    c3.metric("Resonance Class", summary.get("resonance_class", "n/a"))
    c4.metric("Dominant Motif", summary.get("dominant_motif", "n/a"))

    st.dataframe(
        dict_to_dataframe(summary, "metric", "value"),
        width="stretch",
    )


def render_cig_summary(stack_data: dict) -> None:
    """Render Canonical Identity Graph summary."""
    st.markdown("## Canonical Identity Graph")

    summary = stack_data.get("cig", {}).get("summary", {})

    st.dataframe(
        dict_to_dataframe(summary, "metric", "value"),
        width="stretch",
    )


def render_stg_summary(stack_data: dict) -> None:
    """Render Structural Truth Graph summary."""
    st.markdown("## Structural Truth Graph")

    summary = stack_data.get("stg", {}).get("summary", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Truth Nodes", summary.get("truth_node_count", 0))
    c2.metric("Truth Edges", summary.get("truth_edge_count", 0))
    c3.metric("Mean Node Truth", format_float(summary.get("mean_node_truth", 0)))
    c4.metric("Mean Edge Truth", format_float(summary.get("mean_edge_truth", 0)))

    st.dataframe(
        dict_to_dataframe(summary, "metric", "value"),
        width="stretch",
    )


def render_motif_summary(stack_data: dict) -> None:
    """Render Structural Motif summary."""
    st.markdown("## Structural Motifs")

    motifs = stack_data.get("motifs", {})
    summary = motifs.get("summary", {})

    rows = [
        {"motif": "hubs", "count": summary.get("hub_count", 0)},
        {"motif": "bridges", "count": summary.get("bridge_count", 0)},
        {"motif": "articulations", "count": summary.get("articulation_count", 0)},
        {"motif": "leaves", "count": summary.get("leaf_count", 0)},
        {"motif": "chains", "count": summary.get("chain_count", 0)},
        {"motif": "triangles", "count": summary.get("triangle_count", 0)},
        {"motif": "stars", "count": summary.get("star_count", 0)},
        {"motif": "bottlenecks", "count": summary.get("bottleneck_count", 0)},
        {"motif": "cycle_like", "count": summary.get("cycle_like_count", 0)},
    ]

    dataframe = pd.DataFrame(rows)

    st.dataframe(dataframe, width="stretch")

    if not dataframe.empty:
        st.bar_chart(
            dataframe.set_index("motif")["count"],
            width="stretch",
        )


def render_genome_summary(stack_data: dict) -> None:
    """Render Structural Genome summary."""
    st.markdown("## Structural Genome")

    genome = stack_data.get("genome", {})
    summary = genome.get("summary", {})

    c1, c2, c3, c4, c5 = st.columns(5)

    c1.metric("Hierarchy", format_float(genome.get("hierarchy_score", 0)))
    c2.metric("Branching", format_float(genome.get("branching_score", 0)))
    c3.metric("Cyclicity", format_float(genome.get("cyclicity_score", 0)))
    c4.metric("Bottleneck", format_float(genome.get("bottleneck_score", 0)))
    c5.metric("Persistence", format_float(genome.get("persistence_score", 0)))

    sequence = genome.get("genome_sequence", [])

    if sequence:
        st.markdown("### Genome Sequence")
        st.code(" → ".join(sequence))

    st.dataframe(
        dict_to_dataframe(summary, "metric", "value"),
        width="stretch",
    )


def render_topology_summary(stack_data: dict) -> None:
    """Render Identity Topology summary."""
    st.markdown("## Identity Topology")

    topology = stack_data.get("topology", {})
    vector = topology.get("topology_vector", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Class", topology.get("topology_class", "n/a"))
    c2.metric("Dominant Axis", topology.get("dominant_axis", "n/a"))
    c3.metric("Flow", topology.get("flow_pattern", "n/a"))
    c4.metric("Stability", topology.get("stability_pattern", "n/a"))

    st.dataframe(
        dict_to_dataframe(vector, "axis", "score"),
        width="stretch",
    )


def render_resonance_summary(stack_data: dict) -> None:
    """Render Identity Resonance summary."""
    st.markdown("## Identity Resonance")

    resonance = stack_data.get("resonance", {})
    vector = resonance.get("resonance_vector", {})

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Class", resonance.get("resonance_class", "n/a"))
    c2.metric("Dominant Axis", resonance.get("dominant_resonance_axis", "n/a"))
    c3.metric("Activation", resonance.get("activation_pattern", "n/a"))
    c4.metric("Propagation", resonance.get("propagation_pattern", "n/a"))

    st.dataframe(
        dict_to_dataframe(vector, "axis", "score"),
        width="stretch",
    )


def render_download_exports(stack_data: dict, audit_data: dict) -> None:
    """Render downloadable exports without displaying huge JSON."""
    st.markdown("## Exports")

    full_json = json.dumps(
        stack_data,
        indent=2,
        sort_keys=True,
    )

    summary_json = json.dumps(
        stack_data.get("summary", {}),
        indent=2,
        sort_keys=True,
    )

    compact_json = json.dumps(
        build_compact_export(stack_data),
        indent=2,
        sort_keys=True,
    )

    audit_json = json.dumps(
        audit_data,
        indent=2,
        sort_keys=True,
    )

    name = str(stack_data.get("name", "identity_stack"))
    safe_name = safe_filename(name)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.download_button(
            label="Download compact stack JSON",
            data=compact_json,
            file_name=f"{safe_name}_identity_stack_compact.json",
            mime="application/json",
        )

    with col2:
        st.download_button(
            label="Download summary JSON",
            data=summary_json,
            file_name=f"{safe_name}_identity_stack_summary.json",
            mime="application/json",
        )

    with col3:
        st.download_button(
            label="Download audit JSON",
            data=audit_json,
            file_name=f"{safe_name}_identity_stack_audit.json",
            mime="application/json",
        )

    with col4:
        st.download_button(
            label="Download full stack JSON",
            data=full_json,
            file_name=f"{safe_name}_identity_stack_full.json",
            mime="application/json",
        )


def build_compact_export(stack_data: dict) -> dict:
    """Build compact export for easier downstream review."""
    return {
        "version": stack_data.get("version"),
        "name": stack_data.get("name"),
        "summary": stack_data.get("summary", {}),
        "cig_summary": stack_data.get("cig", {}).get("summary", {}),
        "stg_summary": stack_data.get("stg", {}).get("summary", {}),
        "motif_summary": stack_data.get("motifs", {}).get("summary", {}),
        "genome_summary": stack_data.get("genome", {}).get("summary", {}),
        "topology_summary": stack_data.get("topology", {}).get("summary", {}),
        "resonance_summary": stack_data.get("resonance", {}).get("summary", {}),
    }


def safe_filename(name: str) -> str:
    """Convert a name to a safe file stem."""
    safe = name.lower().strip()

    replacements = {
        " ": "_",
        "/": "_",
        "\\": "_",
        ":": "_",
        ";": "_",
        ",": "_",
        ".": "_",
        "'": "",
        '"': "",
        "(": "",
        ")": "",
        "[": "",
        "]": "",
    }

    for old, new in replacements.items():
        safe = safe.replace(old, new)

    return safe or "identity_stack"


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