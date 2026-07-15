"""Directed graph intelligence for learned market morphologies.

The engine converts morphology cluster assignments, profiles, and transitions
into a directed probabilistic graph. Graph nodes represent learned morphology
clusters; weighted edges represent historical transitions.

Research only:
- no order creation;
- no portfolio sizing;
- no live execution;
- no future information used to build graph transitions.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


NODE_REQUIRED = {
    "morphology_cluster_id",
    "morphology_cluster",
    "asset",
    "observation_count",
}

EDGE_REQUIRED = {
    "morphology_cluster_id",
    "morphology_cluster",
    "next_cluster_id",
    "next_cluster",
    "transition_count",
    "transition_probability",
}


@dataclass(frozen=True, slots=True)
class MorphologyGraphConfig:
    pagerank_damping: float = 0.85
    pagerank_tolerance: float = 1e-10
    pagerank_maximum_iterations: int = 500
    minimum_edge_probability: float = 0.0
    minimum_transition_count: int = 1
    forecast_depth: int = 4
    top_paths_per_source: int = 10
    outcome_horizons: tuple[int, ...] = (
        1,
        2,
        4,
        8,
        16,
        32,
        96,
    )

    def __post_init__(self) -> None:
        if not 0.0 < self.pagerank_damping < 1.0:
            raise ValueError(
                "pagerank_damping must be between zero and one."
            )

        if self.pagerank_tolerance <= 0.0:
            raise ValueError(
                "pagerank_tolerance must be positive."
            )

        if self.pagerank_maximum_iterations < 1:
            raise ValueError(
                "pagerank_maximum_iterations must be positive."
            )

        if not 0.0 <= self.minimum_edge_probability <= 1.0:
            raise ValueError(
                "minimum_edge_probability must be between zero and one."
            )

        if self.minimum_transition_count < 1:
            raise ValueError(
                "minimum_transition_count must be positive."
            )

        if self.forecast_depth < 1:
            raise ValueError(
                "forecast_depth must be positive."
            )

        if self.top_paths_per_source < 1:
            raise ValueError(
                "top_paths_per_source must be positive."
            )


def load_cluster_profiles(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    missing = sorted(
        NODE_REQUIRED - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Cluster profiles missing required columns: {missing}"
        )

    frame = frame.copy()

    frame["morphology_cluster_id"] = pd.to_numeric(
        frame["morphology_cluster_id"],
        errors="raise",
    ).astype(int)

    frame["observation_count"] = pd.to_numeric(
        frame["observation_count"],
        errors="coerce",
    ).fillna(0).astype(int)

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    return frame.sort_values(
        [
            "morphology_cluster_id",
            "asset",
        ],
        kind="stable",
    ).reset_index(drop=True)


def load_cluster_transitions(
    path: str | Path,
    *,
    config: MorphologyGraphConfig = MorphologyGraphConfig(),
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    missing = sorted(
        EDGE_REQUIRED - set(frame.columns)
    )

    if missing:
        raise ValueError(
            f"Cluster transitions missing required columns: {missing}"
        )

    frame = frame.copy()

    for column in (
        "morphology_cluster_id",
        "next_cluster_id",
        "transition_count",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame["transition_probability"] = pd.to_numeric(
        frame["transition_probability"],
        errors="coerce",
    )

    frame = frame.dropna(
        subset=[
            "morphology_cluster_id",
            "next_cluster_id",
            "transition_count",
            "transition_probability",
        ]
    )

    frame["morphology_cluster_id"] = (
        frame["morphology_cluster_id"]
        .astype(int)
    )

    frame["next_cluster_id"] = (
        frame["next_cluster_id"]
        .astype(int)
    )

    frame["transition_count"] = (
        frame["transition_count"]
        .astype(int)
    )

    frame = frame[
        frame["transition_count"].ge(
            config.minimum_transition_count
        )
        & frame["transition_probability"].ge(
            config.minimum_edge_probability
        )
    ].copy()

    return frame.sort_values(
        [
            "morphology_cluster_id",
            "transition_probability",
            "next_cluster_id",
        ],
        ascending=[
            True,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def normalize_transition_probabilities(
    edges: pd.DataFrame,
) -> pd.DataFrame:
    frame = edges.copy()

    totals = (
        frame.groupby(
            "morphology_cluster_id"
        )["transition_probability"]
        .transform("sum")
    )

    valid = totals.gt(0.0)

    frame.loc[
        valid,
        "transition_probability",
    ] = (
        frame.loc[
            valid,
            "transition_probability",
        ]
        / totals.loc[valid]
    )

    return frame


def build_adjacency_matrix(
    edges: pd.DataFrame,
    *,
    node_ids: Iterable[int],
) -> tuple[np.ndarray, tuple[int, ...]]:
    ordered_ids = tuple(
        sorted(
            set(
                int(value)
                for value in node_ids
            )
        )
    )

    index = {
        cluster_id: position
        for position, cluster_id in enumerate(
            ordered_ids
        )
    }

    matrix = np.zeros(
        (
            len(ordered_ids),
            len(ordered_ids),
        ),
        dtype=float,
    )

    for row in edges.itertuples(
        index=False
    ):
        source = int(
            row.morphology_cluster_id
        )

        target = int(
            row.next_cluster_id
        )

        if source not in index or target not in index:
            continue

        matrix[
            index[source],
            index[target],
        ] += float(
            row.transition_probability
        )

    row_sums = matrix.sum(
        axis=1
    )

    for position, total in enumerate(
        row_sums
    ):
        if total > 0.0:
            matrix[
                position
            ] /= total
        else:
            matrix[
                position,
                position,
            ] = 1.0

    return matrix, ordered_ids


def calculate_pagerank(
    adjacency: np.ndarray,
    *,
    damping: float,
    tolerance: float,
    maximum_iterations: int,
) -> tuple[np.ndarray, int, bool]:
    count = adjacency.shape[0]

    if count == 0:
        return (
            np.asarray([], dtype=float),
            0,
            True,
        )

    rank = np.full(
        count,
        1.0 / count,
        dtype=float,
    )

    teleport = (
        1.0 - damping
    ) / count

    converged = False
    iterations = 0

    for iteration in range(
        1,
        maximum_iterations + 1,
    ):
        iterations = iteration

        updated = (
            teleport
            + damping
            * adjacency.T.dot(rank)
        )

        total = float(
            updated.sum()
        )

        if total > 0.0:
            updated /= total

        movement = float(
            np.abs(
                updated - rank
            ).sum()
        )

        rank = updated

        if movement <= tolerance:
            converged = True
            break

    return rank, iterations, converged


def transition_entropy(
    probabilities: Iterable[float],
) -> float:
    values = np.asarray(
        list(probabilities),
        dtype=float,
    )

    values = values[
        values > 0.0
    ]

    if len(values) == 0:
        return 0.0

    entropy = float(
        -np.sum(
            values
            * np.log2(values)
        )
    )

    maximum = math.log2(
        len(values)
    ) if len(values) > 1 else 0.0

    return (
        entropy / maximum
        if maximum > 0.0
        else 0.0
    )


def build_asset_outcome_profiles(
    profiles: pd.DataFrame,
    *,
    config: MorphologyGraphConfig,
) -> pd.DataFrame:
    preferred = [
        "morphology_cluster_id",
        "morphology_cluster",
        "asset",
        "observation_count",
        "dominant_rank_state",
        "dominant_transition",
    ]

    outcome_columns: list[str] = []

    for horizon in config.outcome_horizons:
        for prefix in (
            "long_mean_return",
            "long_win_rate",
            "short_mean_return",
            "short_win_rate",
        ):
            column = (
                f"{prefix}_{horizon}"
            )

            if column in profiles.columns:
                outcome_columns.append(
                    column
                )

    feature_columns = [
        column
        for column in profiles.columns
        if column.startswith("mean_")
        and column not in outcome_columns
    ]

    columns = [
        column
        for column in (
            preferred
            + feature_columns
            + outcome_columns
        )
        if column in profiles.columns
    ]

    return profiles[
        columns
    ].copy()


def build_graph_nodes(
    profiles: pd.DataFrame,
    edges: pd.DataFrame,
    *,
    config: MorphologyGraphConfig,
) -> tuple[pd.DataFrame, dict[str, Any]]:
    cluster_metadata = (
        profiles.groupby(
            [
                "morphology_cluster_id",
                "morphology_cluster",
            ],
            sort=True,
            observed=True,
        )
        .agg(
            observation_count=(
                "observation_count",
                "max",
            ),
            asset_count=(
                "asset",
                "nunique",
            ),
        )
        .reset_index()
    )

    node_ids = (
        cluster_metadata[
            "morphology_cluster_id"
        ]
        .astype(int)
        .tolist()
    )

    adjacency, ordered_ids = (
        build_adjacency_matrix(
            edges,
            node_ids=node_ids,
        )
    )

    pagerank, iterations, converged = (
        calculate_pagerank(
            adjacency,
            damping=config.pagerank_damping,
            tolerance=config.pagerank_tolerance,
            maximum_iterations=(
                config.pagerank_maximum_iterations
            ),
        )
    )

    id_to_position = {
        cluster_id: position
        for position, cluster_id in enumerate(
            ordered_ids
        )
    }

    outgoing_groups = {
        int(cluster_id): group
        for cluster_id, group
        in edges.groupby(
            "morphology_cluster_id",
            observed=True,
        )
    }

    incoming_counts = (
        edges.groupby(
            "next_cluster_id"
        )["transition_count"]
        .sum()
        .to_dict()
    )

    incoming_sources = (
        edges.groupby(
            "next_cluster_id"
        )["morphology_cluster_id"]
        .nunique()
        .to_dict()
    )

    rows: list[dict[str, Any]] = []

    for row in cluster_metadata.itertuples(
        index=False
    ):
        cluster_id = int(
            row.morphology_cluster_id
        )

        outgoing = outgoing_groups.get(
            cluster_id,
            pd.DataFrame(),
        )

        if outgoing.empty:
            outgoing_count = 0
            outgoing_transitions = 0
            self_probability = 0.0
            entropy = 0.0
            dominant_next_id = cluster_id
            dominant_next = str(
                row.morphology_cluster
            )
            dominant_probability = 0.0
        else:
            outgoing_count = int(
                outgoing[
                    "transition_count"
                ].sum()
            )

            outgoing_transitions = int(
                len(outgoing)
            )

            self_rows = outgoing[
                outgoing[
                    "next_cluster_id"
                ].eq(cluster_id)
            ]

            self_probability = float(
                self_rows[
                    "transition_probability"
                ].sum()
            )

            entropy = transition_entropy(
                outgoing[
                    "transition_probability"
                ]
            )

            best = outgoing.sort_values(
                [
                    "transition_probability",
                    "transition_count",
                ],
                ascending=[
                    False,
                    False,
                ],
                kind="stable",
            ).iloc[0]

            dominant_next_id = int(
                best["next_cluster_id"]
            )

            dominant_next = str(
                best["next_cluster"]
            )

            dominant_probability = float(
                best[
                    "transition_probability"
                ]
            )

        position = id_to_position[
            cluster_id
        ]

        rows.append({
            "morphology_cluster_id":
                cluster_id,
            "morphology_cluster":
                str(
                    row.morphology_cluster
                ),
            "observation_count":
                int(
                    row.observation_count
                ),
            "asset_count":
                int(
                    row.asset_count
                ),
            "outgoing_transition_count":
                outgoing_count,
            "outgoing_edge_count":
                outgoing_transitions,
            "incoming_transition_count":
                int(
                    incoming_counts.get(
                        cluster_id,
                        0,
                    )
                ),
            "incoming_source_count":
                int(
                    incoming_sources.get(
                        cluster_id,
                        0,
                    )
                ),
            "self_transition_probability":
                self_probability,
            "transition_entropy":
                entropy,
            "dominant_next_cluster_id":
                dominant_next_id,
            "dominant_next_cluster":
                dominant_next,
            "dominant_next_probability":
                dominant_probability,
            "pagerank":
                float(
                    pagerank[position]
                ),
        })

    nodes = (
        pd.DataFrame(rows)
        .sort_values(
            [
                "pagerank",
                "observation_count",
            ],
            ascending=[
                False,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )

    metadata = {
        "pagerank_iterations":
            int(iterations),
        "pagerank_converged":
            bool(converged),
    }

    return nodes, metadata


def build_graph_edges(
    edges: pd.DataFrame,
) -> pd.DataFrame:
    frame = normalize_transition_probabilities(
        edges
    )

    frame["is_self_transition"] = (
        frame["morphology_cluster_id"]
        .eq(
            frame["next_cluster_id"]
        )
    )

    frame["edge_surprise"] = (
        -np.log2(
            frame[
                "transition_probability"
            ].clip(
                lower=1e-15
            )
        )
    )

    frame["edge_strength"] = (
        frame[
            "transition_probability"
        ]
        * np.log1p(
            frame[
                "transition_count"
            ]
        )
    )

    return frame.sort_values(
        [
            "morphology_cluster_id",
            "transition_probability",
            "transition_count",
        ],
        ascending=[
            True,
            False,
            False,
        ],
        kind="stable",
    ).reset_index(drop=True)


def matrix_power_forecasts(
    adjacency: np.ndarray,
    *,
    node_ids: tuple[int, ...],
    depth: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    current = np.eye(
        len(node_ids),
        dtype=float,
    )

    for step in range(
        1,
        depth + 1,
    ):
        current = current.dot(
            adjacency
        )

        for source_position, source_id in enumerate(
            node_ids
        ):
            for target_position, target_id in enumerate(
                node_ids
            ):
                probability = float(
                    current[
                        source_position,
                        target_position,
                    ]
                )

                if probability <= 0.0:
                    continue

                rows.append({
                    "source_cluster_id":
                        int(source_id),
                    "forecast_step":
                        int(step),
                    "target_cluster_id":
                        int(target_id),
                    "forecast_probability":
                        probability,
                })

    return pd.DataFrame(rows)


def enumerate_top_paths(
    adjacency: np.ndarray,
    *,
    node_ids: tuple[int, ...],
    depth: int,
    top_paths_per_source: int,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    for source_position, source_id in enumerate(
        node_ids
    ):
        paths = [
            (
                [source_position],
                1.0,
            )
        ]

        for _ in range(depth):
            expanded = []

            for path, probability in paths:
                current_position = path[-1]

                candidates = np.where(
                    adjacency[
                        current_position
                    ] > 0.0
                )[0]

                for candidate in candidates:
                    next_probability = (
                        probability
                        * float(
                            adjacency[
                                current_position,
                                candidate,
                            ]
                        )
                    )

                    expanded.append(
                        (
                            path
                            + [
                                int(candidate)
                            ],
                            next_probability,
                        )
                    )

            expanded.sort(
                key=lambda item: item[1],
                reverse=True,
            )

            paths = expanded[
                :top_paths_per_source
            ]

        for rank, (
            path,
            probability,
        ) in enumerate(
            paths,
            start=1,
        ):
            cluster_path = [
                int(
                    node_ids[position]
                )
                for position in path
            ]

            rows.append({
                "source_cluster_id":
                    int(source_id),
                "path_rank":
                    int(rank),
                "path_depth":
                    int(depth),
                "cluster_path":
                    "->".join(
                        str(value)
                        for value in cluster_path
                    ),
                "terminal_cluster_id":
                    int(
                        cluster_path[-1]
                    ),
                "path_probability":
                    float(probability),
            })

    return pd.DataFrame(rows)


def build_graph_forecasts(
    edges: pd.DataFrame,
    *,
    node_ids: Iterable[int],
    config: MorphologyGraphConfig,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    adjacency, ordered_ids = (
        build_adjacency_matrix(
            edges,
            node_ids=node_ids,
        )
    )

    forecasts = matrix_power_forecasts(
        adjacency,
        node_ids=ordered_ids,
        depth=config.forecast_depth,
    )

    paths = enumerate_top_paths(
        adjacency,
        node_ids=ordered_ids,
        depth=config.forecast_depth,
        top_paths_per_source=(
            config.top_paths_per_source
        ),
    )

    return forecasts, paths


def build_edge_outcome_map(
    assignments: pd.DataFrame,
    *,
    horizon: int = 16,
) -> pd.DataFrame:
    required = {
        "timestamp",
        "asset",
        "morphology_cluster_id",
        "morphology_cluster",
        f"forward_return_{horizon}",
        f"short_return_{horizon}",
    }

    missing = sorted(
        required - set(assignments.columns)
    )

    if missing:
        raise ValueError(
            f"Cluster assignments missing outcome columns: {missing}"
        )

    frame = assignments.sort_values(
        [
            "asset",
            "timestamp",
        ],
        kind="stable",
    ).copy()

    frame["next_cluster_id"] = (
        frame.groupby(
            "asset",
            observed=True,
        )[
            "morphology_cluster_id"
        ]
        .shift(-1)
    )

    frame["next_cluster"] = (
        frame.groupby(
            "asset",
            observed=True,
        )[
            "morphology_cluster"
        ]
        .shift(-1)
    )

    frame = frame.dropna(
        subset=[
            "next_cluster_id",
            "next_cluster",
        ]
    )

    frame["next_cluster_id"] = (
        frame["next_cluster_id"]
        .astype(int)
    )

    grouped = (
        frame.groupby(
            [
                "morphology_cluster_id",
                "morphology_cluster",
                "next_cluster_id",
                "next_cluster",
                "asset",
            ],
            sort=True,
            observed=True,
        )
    )

    rows = []

    for keys, group in grouped:
        (
            source_id,
            source,
            target_id,
            target,
            asset,
        ) = keys

        long_values = pd.to_numeric(
            group[
                f"forward_return_{horizon}"
            ],
            errors="coerce",
        ).dropna()

        short_values = pd.to_numeric(
            group[
                f"short_return_{horizon}"
            ],
            errors="coerce",
        ).dropna()

        rows.append({
            "morphology_cluster_id":
                int(source_id),
            "morphology_cluster":
                str(source),
            "next_cluster_id":
                int(target_id),
            "next_cluster":
                str(target),
            "asset":
                str(asset),
            "horizon_bars":
                int(horizon),
            "observation_count":
                int(len(group)),
            "long_mean_return":
                float(
                    long_values.mean()
                ) if len(long_values) else 0.0,
            "long_win_rate":
                float(
                    (
                        long_values > 0.0
                    ).mean()
                ) if len(long_values) else 0.0,
            "short_mean_return":
                float(
                    short_values.mean()
                ) if len(short_values) else 0.0,
            "short_win_rate":
                float(
                    (
                        short_values > 0.0
                    ).mean()
                ) if len(short_values) else 0.0,
        })

    result = pd.DataFrame(rows)

    if result.empty:
        return result

    result["preferred_direction"] = np.where(
        result[
            "long_mean_return"
        ].ge(
            result[
                "short_mean_return"
            ]
        ),
        "LONG",
        "SHORT",
    )

    result["preferred_mean_return"] = np.maximum(
        result[
            "long_mean_return"
        ],
        result[
            "short_mean_return"
        ],
    )

    return result.sort_values(
        [
            "preferred_mean_return",
            "observation_count",
        ],
        ascending=[
            False,
            False,
        ],
        kind="stable",
    ).reset_index(drop=True)


def write_graph_outputs(
    *,
    nodes: pd.DataFrame,
    edges: pd.DataFrame,
    asset_profiles: pd.DataFrame,
    forecasts: pd.DataFrame,
    paths: pd.DataFrame,
    edge_outcomes: pd.DataFrame,
    metadata: dict[str, Any],
    config: MorphologyGraphConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    outputs = {
        "nodes":
            directory
            / "morphology_graph_nodes.csv",
        "edges":
            directory
            / "morphology_graph_edges.csv",
        "asset_profiles":
            directory
            / "morphology_graph_asset_profiles.csv",
        "forecasts":
            directory
            / "morphology_graph_forecasts.csv",
        "paths":
            directory
            / "morphology_graph_paths.csv",
        "edge_outcomes":
            directory
            / "morphology_graph_edge_outcomes.csv",
        "summary":
            directory
            / "morphology_graph_summary.json",
    }

    nodes.to_csv(
        outputs["nodes"],
        index=False,
    )

    edges.to_csv(
        outputs["edges"],
        index=False,
    )

    asset_profiles.to_csv(
        outputs["asset_profiles"],
        index=False,
    )

    forecasts.to_csv(
        outputs["forecasts"],
        index=False,
    )

    paths.to_csv(
        outputs["paths"],
        index=False,
    )

    edge_outcomes.to_csv(
        outputs["edge_outcomes"],
        index=False,
    )

    summary = {
        "schema_version":
            "atlas.morphology_graph.v1",
        "config":
            asdict(config),
        "node_count":
            int(len(nodes)),
        "edge_count":
            int(len(edges)),
        "asset_profile_count":
            int(len(asset_profiles)),
        "forecast_rows":
            int(len(forecasts)),
        "path_rows":
            int(len(paths)),
        "edge_outcome_rows":
            int(len(edge_outcomes)),
        **metadata,
        "highest_pagerank_nodes": (
            nodes.head(12)
            .to_dict(
                orient="records"
            )
        ),
        "strongest_edges": (
            edges.sort_values(
                [
                    "edge_strength",
                    "transition_probability",
                ],
                ascending=[
                    False,
                    False,
                ],
            )
            .head(25)
            .to_dict(
                orient="records"
            )
        ),
    }

    outputs["summary"].write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return outputs


def run_morphology_graph(
    *,
    profiles: pd.DataFrame,
    transitions: pd.DataFrame,
    assignments: pd.DataFrame | None = None,
    config: MorphologyGraphConfig = MorphologyGraphConfig(),
    edge_outcome_horizon: int = 16,
) -> dict[str, Any]:
    normalized_edges = (
        normalize_transition_probabilities(
            transitions
        )
    )

    nodes, metadata = build_graph_nodes(
        profiles,
        normalized_edges,
        config=config,
    )

    edges = build_graph_edges(
        normalized_edges
    )

    asset_profiles = (
        build_asset_outcome_profiles(
            profiles,
            config=config,
        )
    )

    node_ids = nodes[
        "morphology_cluster_id"
    ].astype(int).tolist()

    forecasts, paths = (
        build_graph_forecasts(
            edges,
            node_ids=node_ids,
            config=config,
        )
    )

    if assignments is None:
        edge_outcomes = pd.DataFrame()
    else:
        edge_outcomes = (
            build_edge_outcome_map(
                assignments,
                horizon=edge_outcome_horizon,
            )
        )

    return {
        "nodes":
            nodes,
        "edges":
            edges,
        "asset_profiles":
            asset_profiles,
        "forecasts":
            forecasts,
        "paths":
            paths,
        "edge_outcomes":
            edge_outcomes,
        "metadata":
            metadata,
    }
