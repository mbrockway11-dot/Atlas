"""Research Knowledge Graph integrity and metrics."""

from __future__ import annotations

import pandas as pd


def build_integrity_report(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
) -> pd.DataFrame:
    """Check graph referential and structural integrity."""
    node_ids = set(
        nodes["node_id"].astype(str)
    ) if not nodes.empty else set()

    rows = []

    duplicate_nodes = (
        int(
            nodes[
                "node_id"
            ].duplicated().sum()
        )
        if not nodes.empty
        else 0
    )

    duplicate_edges = (
        int(
            edges[
                "edge_id"
            ].duplicated().sum()
        )
        if not edges.empty
        else 0
    )

    orphan_sources = []

    orphan_targets = []

    self_edges = []

    if not edges.empty:
        for _, row in edges.iterrows():
            source = str(
                row["source_node_id"]
            )

            target = str(
                row["target_node_id"]
            )

            if source not in node_ids:
                orphan_sources.append(
                    str(row["edge_id"])
                )

            if target not in node_ids:
                orphan_targets.append(
                    str(row["edge_id"])
                )

            if source == target:
                self_edges.append(
                    str(row["edge_id"])
                )

    checks = [
        (
            "UNIQUE_NODE_IDS",
            duplicate_nodes == 0,
            duplicate_nodes,
        ),
        (
            "UNIQUE_EDGE_IDS",
            duplicate_edges == 0,
            duplicate_edges,
        ),
        (
            "NO_ORPHAN_SOURCES",
            len(orphan_sources) == 0,
            len(orphan_sources),
        ),
        (
            "NO_ORPHAN_TARGETS",
            len(orphan_targets) == 0,
            len(orphan_targets),
        ),
        (
            "NO_SELF_EDGES",
            len(self_edges) == 0,
            len(self_edges),
        ),
        (
            "NO_EXECUTION_INSTRUCTIONS",
            no_execution_instructions(
                nodes,
                edges,
            ),
            0,
        ),
    ]

    for check_id, passed, issue_count in checks:
        rows.append({
            "check_id": check_id,
            "passed": bool(passed),
            "issue_count": int(
                issue_count
            ),
            "status": (
                "PASS"
                if passed
                else "FAIL"
            ),
        })

    return pd.DataFrame(rows)


def build_graph_metrics(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate degree-based graph metrics."""
    if nodes.empty:
        return pd.DataFrame(
            columns=[
                "node_id",
                "node_type",
                "label",
                "in_degree",
                "out_degree",
                "total_degree",
                "is_isolated",
            ]
        )

    in_degree = (
        edges[
            "target_node_id"
        ].value_counts()
        if not edges.empty
        else pd.Series(dtype=int)
    )

    out_degree = (
        edges[
            "source_node_id"
        ].value_counts()
        if not edges.empty
        else pd.Series(dtype=int)
    )

    rows = []

    for _, node in nodes.iterrows():
        current_id = str(
            node["node_id"]
        )

        incoming = int(
            in_degree.get(
                current_id,
                0,
            )
        )

        outgoing = int(
            out_degree.get(
                current_id,
                0,
            )
        )

        rows.append({
            "node_id": current_id,
            "node_type": node[
                "node_type"
            ],
            "label": node["label"],
            "in_degree": incoming,
            "out_degree": outgoing,
            "total_degree": (
                incoming + outgoing
            ),
            "is_isolated": (
                incoming + outgoing == 0
            ),
        })

    return pd.DataFrame(
        rows
    ).sort_values(
        [
            "total_degree",
            "node_type",
            "label",
        ],
        ascending=[
            False,
            True,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def no_execution_instructions(
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
) -> bool:
    node_safe = (
        True
        if nodes.empty
        else not nodes[
            "execution_instruction"
        ].astype(bool).any()
    )

    edge_safe = (
        True
        if edges.empty
        else not edges[
            "execution_instruction"
        ].astype(bool).any()
    )

    return node_safe and edge_safe
