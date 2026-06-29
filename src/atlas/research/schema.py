"""Atlas research dataset schema."""

from __future__ import annotations

from typing import Any


CONSTRUCTION_METADATA = [
    "name",
    "cipher",
    "planet",
    "kamea",
    "grid_size",
    "grid_capacity",
    "sequence_length",
]

PRIMARY_TOPOLOGY = [
    "unique_nodes",
    "unique_edges",
    "node_coverage",
    "density",
    "clusters",
    "self_loops",
    "max_depth",
]

GRAPH_STATISTICS = [
    "component_count",
    "largest_component_size",
    "largest_component_ratio",
    "mean_degree",
    "max_degree",
    "degree_std",
    "hub_count",
    "hub_ratio",
    "leaf_count",
    "leaf_ratio",
    "bridge_count",
    "bridge_ratio",
    "articulation_count",
    "articulation_ratio",
]

COHERENCE_STATISTICS = [
    "mean_node_coherence",
    "median_node_coherence",
    "std_node_coherence",
    "mean_edge_coherence",
    "median_edge_coherence",
    "std_edge_coherence",
    "core_node_ratio",
    "adaptive_node_ratio",
    "peripheral_node_ratio",
    "core_edge_ratio",
    "adaptive_edge_ratio",
    "peripheral_edge_ratio",
    "graph_coherence",
]

REDUCTION_STATISTICS = [
    "reduction_iterations",
    "surviving_node_ratio",
    "surviving_edge_ratio",
    "collapse_iteration",
    "collapse_ratio",
    "core_survival_score",
    "topology_stability",
    "reduction_entropy",
    "node_survival_auc",
    "edge_survival_auc",
    "edge_loss_rate",
    "collapse_slope",
]

ATTRACTOR_STATISTICS = [
    "attractor_node_count",
    "attractor_edge_count",
    "attractor_node_ratio",
    "attractor_edge_ratio",
    "attractor_density",
    "attractor_mean_node_score",
    "attractor_min_node_score",
    "attractor_max_node_score",
    "attractor_stability",
]

ATTRACTOR_METADATA = [
    "attractor_signature",
]

INFORMATION_MEASURES = [
    "entropy",
    "axis_strength",
]

TRANSITIONAL_METRICS = [
    "max_node_weight",
]

IDENTITY_PERSISTENCE = [
    "profile_node_persistence_ratio",
    "profile_edge_persistence_ratio",
]

SUBTYPE_METADATA = [
    "subtype_primary",
    "subtype_secondary",
]

DEPRECATED_COLUMNS = [
    "kamea_score",
]

CANONICAL_RESEARCH_COLUMNS = (
    CONSTRUCTION_METADATA
    + PRIMARY_TOPOLOGY
    + GRAPH_STATISTICS
    + COHERENCE_STATISTICS
    + REDUCTION_STATISTICS
    + ATTRACTOR_STATISTICS
    + ATTRACTOR_METADATA
    + INFORMATION_MEASURES
    + TRANSITIONAL_METRICS
    + SUBTYPE_METADATA
    + IDENTITY_PERSISTENCE
)

MEASUREMENT_COLUMNS = (
    PRIMARY_TOPOLOGY
    + GRAPH_STATISTICS
    + COHERENCE_STATISTICS
    + REDUCTION_STATISTICS
    + ATTRACTOR_STATISTICS
    + INFORMATION_MEASURES
    + TRANSITIONAL_METRICS
    + IDENTITY_PERSISTENCE
)


def classify_column(column: str) -> str:
    """Classify one research matrix column."""
    if column in CONSTRUCTION_METADATA:
        return "construction_metadata"

    if column in PRIMARY_TOPOLOGY:
        return "primary_topology"

    if column in GRAPH_STATISTICS:
        return "graph_statistic"

    if column in COHERENCE_STATISTICS:
        return "coherence_statistic"

    if column in REDUCTION_STATISTICS:
        return "reduction_statistic"

    if column in ATTRACTOR_STATISTICS:
        return "attractor_statistic"

    if column in ATTRACTOR_METADATA:
        return "attractor_metadata"

    if column in INFORMATION_MEASURES:
        return "information_measure"

    if column in TRANSITIONAL_METRICS:
        return "transitional_metric"

    if column in IDENTITY_PERSISTENCE:
        return "identity_persistence"

    if column in SUBTYPE_METADATA:
        return "subtype_metadata"

    if column in DEPRECATED_COLUMNS:
        return "deprecated"

    return "unknown"


def audit_research_row(row: dict[str, Any]) -> dict[str, Any]:
    """Audit one research matrix row against the Atlas schema."""
    columns = list(row.keys())

    deprecated = [
        column
        for column in columns
        if column in DEPRECATED_COLUMNS
    ]

    unknown = [
        column
        for column in columns
        if classify_column(column) == "unknown"
    ]

    missing = [
        column
        for column in CANONICAL_RESEARCH_COLUMNS
        if column not in row
    ]

    classifications = {
        column: classify_column(column)
        for column in columns
    }

    return {
        "valid": not deprecated and not unknown and not missing,
        "columns": columns,
        "classifications": classifications,
        "deprecated_columns": deprecated,
        "unknown_columns": unknown,
        "missing_columns": missing,
        "measurement_columns": [
            column
            for column in columns
            if column in MEASUREMENT_COLUMNS
        ],
        "construction_metadata": [
            column
            for column in columns
            if column in CONSTRUCTION_METADATA
        ],
    }


def audit_research_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Audit a list of research matrix rows."""
    if not rows:
        return {
            "valid": False,
            "row_count": 0,
            "deprecated_columns": [],
            "unknown_columns": [],
            "missing_columns": list(CANONICAL_RESEARCH_COLUMNS),
            "column_classes": {},
        }

    row_audits = [
        audit_research_row(row)
        for row in rows
    ]

    deprecated = sorted(
        {
            column
            for audit in row_audits
            for column in audit["deprecated_columns"]
        }
    )

    unknown = sorted(
        {
            column
            for audit in row_audits
            for column in audit["unknown_columns"]
        }
    )

    missing = sorted(
        {
            column
            for audit in row_audits
            for column in audit["missing_columns"]
        }
    )

    column_classes = {}

    for row in rows:
        for column in row:
            column_classes[column] = classify_column(column)

    return {
        "valid": not deprecated and not unknown and not missing,
        "row_count": len(rows),
        "deprecated_columns": deprecated,
        "unknown_columns": unknown,
        "missing_columns": missing,
        "column_classes": column_classes,
    }


def clean_research_row(row: dict[str, Any]) -> dict[str, Any]:
    """Return a row with deprecated columns removed."""
    return {
        key: value
        for key, value in row.items()
        if key not in DEPRECATED_COLUMNS
    }


def clean_research_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return rows with deprecated columns removed."""
    return [
        clean_research_row(row)
        for row in rows
    ]