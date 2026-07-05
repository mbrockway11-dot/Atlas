"""Population Intelligence dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.services.population_structural_service import build_structural_neighbors_payload
from atlas.services.population_intelligence_service import (
    DEFAULT_PROFILE_DIR,
    build_cluster_rows,
    build_neighbor_payload,
    build_population_intelligence_payload,
    collect_population_identities,
    json_export,
    slugify,
)


POPULATION_V2_PATH = Path("output/population/population_intelligence_v2.json")
STRUCTURAL_RARITY_PATH = Path("output/population/structural_rarity_report.json")
STRUCTURAL_IMPACT_PATH = Path("output/population/structural_impact_report.json")


def render_population_intelligence_page() -> None:
    """Render Population Intelligence dashboard."""
    st.header("Population Intelligence")
    st.caption("Similarity, nearest neighbors, graph structure, and clustering.")

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

    with st.spinner("Building population intelligence payload..."):
        payload = build_population_intelligence_payload(
            profile_dir,
            threshold=threshold,
        )

    if not payload.get("success"):
        for error in payload.get("errors", []):
            st.error(error)
        with st.expander("Raw service payload", expanded=False):
            st.json(payload)
        return

    data = payload["data"]
    matrix = data["matrix"]
    graph = data["graph"]
    clusters = data["clusters"]

    render_summary_cards(payload)
    render_population_v2_summary()
    render_structural_rarity_summary()
    render_structural_impact_summary()
    render_cluster_table(clusters)
    render_neighbor_explorer(matrix)
    render_structural_neighbors_v2()
    render_downloads(data)


def render_summary_cards(payload: dict) -> None:
    """Render top-level population intelligence cards."""
    st.markdown("## Summary")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Profiles", metrics.get("profiles", 0))
    c2.metric("Similarity Pairs", metrics.get("similarity_pairs", 0))
    c3.metric("Graph Edges", metrics.get("graph_edges", 0))
    c4.metric("Clusters", metrics.get("clusters", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Mean Similarity", round(metrics.get("mean_similarity", 0.0), 4))
    c6.metric("Graph Density", round(metrics.get("graph_density", 0.0), 4))
    c7.metric("Largest Cluster", metrics.get("largest_cluster", 0))
    c8.metric("Singletons", metrics.get("singletons", 0))

    data = payload.get("data", {})

    with st.expander("Similarity Summary", expanded=False):
        st.json(getattr(data.get("matrix"), "summary", {}))

    with st.expander("Population Graph Summary", expanded=False):
        st.json(getattr(data.get("graph"), "summary", {}))

    with st.expander("Structural Clustering Summary", expanded=False):
        st.json(getattr(data.get("clusters"), "summary", {}))

    with st.expander("Raw Service Payload Metadata", expanded=False):
        st.json(
            {
                "success": payload.get("success"),
                "profile_dir": payload.get("profile_dir"),
                "threshold": payload.get("threshold"),
                "warnings": payload.get("warnings", []),
                "errors": payload.get("errors", []),
                "metrics": metrics,
            }
        )


def render_cluster_table(clusters) -> None:
    """Render structural cluster table."""
    st.markdown("## Structural Families")

    rows = build_cluster_rows(clusters)
    dataframe = pd.DataFrame(rows)

    if dataframe.empty:
        st.info("No structural clusters found.")
        return

    st.dataframe(
        dataframe,
        width="stretch",
    )

    st.download_button(
        label="Download clusters CSV",
        data=dataframe.to_csv(index=False),
        file_name="structural_clusters.csv",
        mime="text/csv",
    )


def render_neighbor_explorer(matrix) -> None:
    """Render nearest-neighbor explorer."""
    st.markdown("## Nearest Neighbor Explorer")

    identities = collect_population_identities(matrix)

    if not identities:
        st.info("No identities available.")
        return

    selected = st.selectbox(
        "Select profile",
        identities,
    )

    max_limit = min(25, max(1, len(identities) - 1))

    limit = st.slider(
        "Neighbor limit",
        min_value=1,
        max_value=max_limit,
        value=min(10, max_limit),
        step=1,
    )

    neighbor_payload = build_neighbor_payload(
        matrix,
        selected,
        limit=limit,
    )

    st.markdown(f"### Nearest Neighbors for {selected}")

    neighbors = neighbor_payload.get("neighbors", [])

    if neighbors:
        st.dataframe(
            pd.DataFrame(neighbors),
            width="stretch",
        )
    else:
        st.info("No neighbors found.")

    with st.expander("Neighbor Report JSON", expanded=False):
        st.json(neighbor_payload.get("report", {}))

    st.download_button(
        label="Download selected neighbor report JSON",
        data=json_export(neighbor_payload.get("report", {})),
        file_name=f"{slugify(selected)}_neighbors.json",
        mime="application/json",
    )


def render_downloads(data: dict) -> None:
    """Render JSON export buttons."""
    st.markdown("## Exports")

    c1, c2, c3 = st.columns(3)

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

    c3.download_button(
        label="Download structural clusters JSON",
        data=json_export(data.get("clusters_dict", {})),
        file_name="structural_clusters.json",
        mime="application/json",
    )


def load_population_v2() -> dict:
    """Load Population Intelligence v2 summary."""
    if not POPULATION_V2_PATH.exists():
        return {}

    with POPULATION_V2_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def render_population_v2_summary() -> None:
    """Render Population Intelligence v2 corpus summary."""
    data = load_population_v2()

    if not data:
        st.info("Population Intelligence v2 summary has not been built yet.")
        return

    st.markdown("## Population Intelligence v2")
    st.caption("Corpus-level structural role, subtype, topology, and density summary.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Compiled Profiles", data.get("profile_count", 0))
    c2.metric("Structural Roles", len(data.get("role_distribution", {})))
    c3.metric("Topology Classes", len(data.get("topology_distribution", {})))

    render_distribution_table("Role Distribution", data.get("role_distribution", {}))
    render_distribution_table("Subtype Distribution", data.get("subtype_distribution", {}))
    render_distribution_table("Topology Distribution", data.get("topology_distribution", {}))
    render_role_summaries(data.get("role_summaries", {}))

    with st.expander("Raw Population Intelligence v2 JSON", expanded=False):
        st.json(data)


def render_distribution_table(title: str, distribution: dict) -> None:
    """Render distribution as dataframe."""
    st.markdown(f"### {title}")

    if not distribution:
        st.info(f"No {title.lower()} data available.")
        return

    total = sum(distribution.values()) or 1

    rows = [
        {
            "label": key,
            "count": value,
            "percent": round((value / total) * 100, 2),
        }
        for key, value in distribution.items()
    ]

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_role_summaries(role_summaries: dict) -> None:
    """Render per-role population summaries."""
    st.markdown("### Role Summaries")

    if not role_summaries:
        st.info("No role summaries available.")
        return

    rows = []

    for role, summary in role_summaries.items():
        rows.append(
            {
                "role": role,
                "count": summary.get("count", 0),
                "avg_motif_richness": summary.get("avg_motif_richness", 0),
                "avg_raw_density": summary.get("avg_raw_density", 0),
                "avg_truth_density": summary.get("avg_truth_density", 0),
                "avg_raw_nodes": summary.get("avg_raw_nodes", 0),
                "avg_truth_nodes": summary.get("avg_truth_nodes", 0),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Role Examples", expanded=False):
        for role, summary in role_summaries.items():
            st.markdown(f"#### {role}")
            st.write(", ".join(summary.get("examples", [])))


def render_structural_neighbors_v2() -> None:
    """Render explainable structural nearest neighbors."""
    st.markdown("## Structural Neighbors v2")
    st.caption("Weighted similarity using role, topology, motif, resonance, and graph-density metrics.")

    data = load_population_v2()
    profiles = data.get("profiles", []) if isinstance(data, dict) else []

    if not profiles:
        st.info("Build Population Intelligence v2 before using structural neighbors.")
        return

    profile_keys = [item["profile_key"] for item in profiles if item.get("profile_key")]

    selected = st.selectbox(
        "Select structural profile",
        profile_keys,
        key="structural_neighbors_v2_select",
    )

    limit = st.slider(
        "Structural neighbor limit",
        min_value=1,
        max_value=25,
        value=10,
        step=1,
        key="structural_neighbors_v2_limit",
    )

    with st.spinner("Computing structural neighbors..."):
        result = build_structural_neighbors_payload(selected, limit=limit, profile_keys=profile_keys)

    if not result.get("success"):
        for error in result.get("errors", []):
            st.error(error)
        return

    neighbors = result.get("neighbors", [])

    if not neighbors:
        st.info("No structural neighbors found.")
        return

    rows = []

    for item in neighbors:
        candidate = item.get("candidate", {})
        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "similarity_percent": item.get("similarity_percent"),
                "role": candidate.get("role"),
                "subtype": candidate.get("subtype"),
                "topology": candidate.get("topology"),
                "axis": candidate.get("axis"),
                "motif_richness": candidate.get("motif_richness"),
                "truth_density": candidate.get("truth_density"),
                "shared": "; ".join(item.get("shared", [])[:4]),
                "differences": "; ".join(item.get("differences", [])[:4]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")

    with st.expander("Selected Structural Neighbor Report", expanded=False):
        st.json(result)

    st.download_button(
        label="Download structural neighbor report JSON",
        data=json_export(result),
        file_name=f"{slugify(selected)}_structural_neighbors_v2.json",
        mime="application/json",
    )


def load_structural_rarity() -> dict:
    """Load Structural Rarity report."""
    if not STRUCTURAL_RARITY_PATH.exists():
        return {}

    with STRUCTURAL_RARITY_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def render_structural_rarity_summary() -> None:
    """Render Structural Rarity Engine report."""
    report = load_structural_rarity()

    if not report:
        st.info("Structural Rarity report has not been built yet.")
        return

    st.markdown("## Structural Rarity Engine")
    st.caption("Corpus-level outlier detection for rare structures, unusual graph density, and exceptional profile signatures.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Profiles Scored", report.get("profile_count", 0))
    c2.metric("Top Outliers", len(report.get("top_outliers", [])))
    c3.metric("Metric Groups", len(report.get("metric_leaders", {})))

    render_top_structural_outliers(report.get("top_outliers", []))
    render_metric_leaders(report.get("metric_leaders", {}))
    render_grouped_outliers("Role Outliers", report.get("role_outliers", {}))
    render_grouped_outliers("Topology Outliers", report.get("topology_outliers", {}))

    with st.expander("Raw Structural Rarity JSON", expanded=False):
        st.json(report)


def render_top_structural_outliers(outliers: list[dict]) -> None:
    """Render top rarity outliers."""
    st.markdown("### Top Structural Outliers")

    if not outliers:
        st.info("No structural outliers found.")
        return

    rows = []

    for item in outliers[:50]:
        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "role": item.get("role"),
                "subtype": item.get("subtype"),
                "topology": item.get("topology"),
                "rarity_score": item.get("overall_rarity_score"),
                "label": item.get("outlier_label"),
                "truth_density": item.get("truth_density"),
                "raw_density": item.get("raw_density"),
                "reasons": "; ".join(item.get("outlier_reasons", [])[:4]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_metric_leaders(metric_leaders: dict) -> None:
    """Render metric leaders."""
    st.markdown("### Metric Leaders")

    if not metric_leaders:
        st.info("No metric leader data available.")
        return

    metric = st.selectbox(
        "Select rarity metric",
        list(metric_leaders.keys()),
        key="structural_rarity_metric_select",
    )

    rows = []

    for item in metric_leaders.get(metric, []):
        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "role": item.get("role"),
                "topology": item.get("topology"),
                "axis": item.get("axis"),
                "motif_richness": item.get("motif_richness"),
                "raw_density": item.get("raw_density"),
                "truth_density": item.get("truth_density"),
                "rarity_score": item.get("overall_rarity_score"),
                "label": item.get("outlier_label"),
                "reasons": "; ".join(item.get("outlier_reasons", [])[:3]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_grouped_outliers(title: str, groups: dict) -> None:
    """Render grouped outlier tables."""
    st.markdown(f"### {title}")

    if not groups:
        st.info(f"No {title.lower()} available.")
        return

    selected = st.selectbox(
        title,
        list(groups.keys()),
        key=f"{slugify(title)}_select",
    )

    rows = []

    for item in groups.get(selected, []):
        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "role": item.get("role"),
                "subtype": item.get("subtype"),
                "topology": item.get("topology"),
                "axis": item.get("axis"),
                "rarity_score": item.get("overall_rarity_score"),
                "label": item.get("outlier_label"),
                "reasons": "; ".join(item.get("outlier_reasons", [])[:3]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def load_structural_impact() -> dict:
    """Load Structural Impact report."""
    if not STRUCTURAL_IMPACT_PATH.exists():
        return {}

    with STRUCTURAL_IMPACT_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def render_structural_impact_summary() -> None:
    """Render Structural Impact Engine report."""
    report = load_structural_impact()

    if not report:
        st.info("Structural Impact report has not been built yet.")
        return

    st.markdown("## Structural Impact Engine")
    st.caption("Multi-factor ranking of outstanding structural signatures across rarity, graph complexity, truth density, motif richness, and centrality proxies.")

    c1, c2, c3 = st.columns(3)
    c1.metric("Profiles Scored", report.get("profile_count", 0))
    c2.metric("Top Impact Profiles", len(report.get("top_impact_profiles", [])))
    c3.metric("Leaderboards", len(report.get("leaderboards", {})))

    render_top_structural_impact(report.get("top_impact_profiles", []))
    render_impact_leaderboards(report.get("leaderboards", {}))

    with st.expander("Impact Weights", expanded=False):
        st.json(report.get("weights", {}))

    with st.expander("Raw Structural Impact JSON", expanded=False):
        st.json(report)


def render_top_structural_impact(profiles: list[dict]) -> None:
    """Render top impact profiles."""
    st.markdown("### Top Structural Impact Profiles")

    if not profiles:
        st.info("No structural impact profiles found.")
        return

    rows = []

    for item in profiles[:100]:
        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "role": item.get("role"),
                "subtype": item.get("subtype"),
                "topology": item.get("topology"),
                "impact_percent": item.get("impact_percent"),
                "impact_label": item.get("impact_label"),
                "rarity": item.get("components", {}).get("rarity"),
                "graph_complexity": item.get("components", {}).get("graph_complexity"),
                "truth_density": item.get("components", {}).get("truth_density"),
                "motif_richness": item.get("components", {}).get("motif_richness"),
                "centrality_proxy": item.get("components", {}).get("centrality_proxy"),
                "reasons": "; ".join(item.get("impact_reasons", [])[:4]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")


def render_impact_leaderboards(leaderboards: dict) -> None:
    """Render structural impact leaderboards."""
    st.markdown("### Impact Leaderboards")

    if not leaderboards:
        st.info("No impact leaderboards available.")
        return

    selected = st.selectbox(
        "Select impact leaderboard",
        list(leaderboards.keys()),
        key="structural_impact_leaderboard_select",
    )

    rows = []

    for item in leaderboards.get(selected, []):
        components = item.get("components", {})

        rows.append(
            {
                "profile_key": item.get("profile_key"),
                "name": item.get("name"),
                "role": item.get("role"),
                "subtype": item.get("subtype"),
                "topology": item.get("topology"),
                "impact_percent": item.get("impact_percent"),
                "impact_label": item.get("impact_label"),
                "rarity": components.get("rarity"),
                "graph_complexity": components.get("graph_complexity"),
                "truth_density": components.get("truth_density"),
                "motif_richness": components.get("motif_richness"),
                "centrality_proxy": components.get("centrality_proxy"),
                "reasons": "; ".join(item.get("impact_reasons", [])[:4]),
            }
        )

    st.dataframe(pd.DataFrame(rows), width="stretch")
