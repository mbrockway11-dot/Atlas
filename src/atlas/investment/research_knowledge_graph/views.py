"""Research Knowledge Graph lineage views."""

from __future__ import annotations

import pandas as pd


def build_lineage_views(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    """Build query-ready graph subsets."""
    enriched = enrich_edges(
        nodes,
        edges,
    )

    return {
        "engine_relationships": filter_view(
            enriched,
            source_type="ENGINE",
        ),
        "hypothesis_relationships": filter_view(
            enriched,
            source_type="HYPOTHESIS",
        ),
        "variant_lineage": (
            enriched[
                enriched[
                    "source_node_type"
                ].eq("VARIANT")
                | enriched[
                    "target_node_type"
                ].eq("VARIANT")
            ].copy()
            if not enriched.empty
            else enriched.copy()
        ),
        "portfolio_lineage": (
            enriched[
                enriched[
                    "source_node_type"
                ].eq(
                    "PORTFOLIO_EXPERIMENT"
                )
                | enriched[
                    "target_node_type"
                ].eq(
                    "PORTFOLIO_EXPERIMENT"
                )
            ].copy()
            if not enriched.empty
            else enriched.copy()
        ),
        "research_cycle_lineage": (
            enriched[
                enriched[
                    "source_node_type"
                ].eq(
                    "RESEARCH_CYCLE"
                )
                | enriched[
                    "target_node_type"
                ].eq(
                    "RESEARCH_CYCLE"
                )
            ].copy()
            if not enriched.empty
            else enriched.copy()
        ),
    }


def enrich_edges(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
) -> pd.DataFrame:
    if edges.empty:
        return pd.DataFrame()

    source_lookup = nodes[
        [
            "node_id",
            "node_type",
            "label",
            "natural_key",
        ]
    ].rename(columns={
        "node_id": "source_node_id",
        "node_type": "source_node_type",
        "label": "source_label",
        "natural_key": (
            "source_natural_key"
        ),
    })

    target_lookup = nodes[
        [
            "node_id",
            "node_type",
            "label",
            "natural_key",
        ]
    ].rename(columns={
        "node_id": "target_node_id",
        "node_type": "target_node_type",
        "label": "target_label",
        "natural_key": (
            "target_natural_key"
        ),
    })

    return (
        edges.merge(
            source_lookup,
            on="source_node_id",
            how="left",
        )
        .merge(
            target_lookup,
            on="target_node_id",
            how="left",
        )
    )


def filter_view(
    frame: pd.DataFrame,
    *,
    source_type: str,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    return frame[
        frame[
            "source_node_type"
        ].eq(source_type)
    ].copy()
