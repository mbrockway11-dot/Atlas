"""Unsupervised market morphology clustering.

The clustering model uses point-in-time morphology features only. Future
returns and path outcomes are excluded from model fitting and are used only
after cluster assignment for descriptive research profiles.

Research only:
- no order creation;
- no portfolio sizing;
- no live execution;
- no future-label leakage into clustering features.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np
import pandas as pd


DEFAULT_FEATURE_COLUMNS = (
    "entropy",
    "transition_velocity",
    "multi_timeframe_agreement",
    "concentration",
    "dispersion",
    "persistence_bars",
    "sol_fulcrum_score",
)

DEFAULT_OUTCOME_HORIZONS = (
    1,
    2,
    4,
    8,
    16,
    32,
    96,
)


@dataclass(frozen=True, slots=True)
class MorphologyClusteringConfig:
    cluster_counts: tuple[int, ...] = (
        6,
        8,
        12,
        16,
    )
    selected_cluster_count: int = 12
    feature_columns: tuple[str, ...] = (
        DEFAULT_FEATURE_COLUMNS
    )
    pca_components: int = 5
    fit_sample_size: int = 100_000
    diagnostic_sample_size: int = 20_000
    maximum_iterations: int = 100
    convergence_tolerance: float = 1e-6
    random_seed: int = 33
    outcome_horizons: tuple[int, ...] = (
        DEFAULT_OUTCOME_HORIZONS
    )

    def __post_init__(self) -> None:
        counts = tuple(
            sorted(
                set(
                    int(value)
                    for value in self.cluster_counts
                )
            )
        )

        if not counts or any(value < 2 for value in counts):
            raise ValueError(
                "cluster_counts must contain integers >= 2."
            )

        if self.selected_cluster_count not in counts:
            raise ValueError(
                "selected_cluster_count must be in cluster_counts."
            )

        if not self.feature_columns:
            raise ValueError(
                "feature_columns cannot be empty."
            )

        if self.pca_components < 1:
            raise ValueError(
                "pca_components must be positive."
            )

        if self.fit_sample_size < 100:
            raise ValueError(
                "fit_sample_size must be at least 100."
            )

        if self.diagnostic_sample_size < 100:
            raise ValueError(
                "diagnostic_sample_size must be at least 100."
            )

        if self.maximum_iterations < 1:
            raise ValueError(
                "maximum_iterations must be positive."
            )

        if (
            not math.isfinite(
                self.convergence_tolerance
            )
            or self.convergence_tolerance <= 0.0
        ):
            raise ValueError(
                "convergence_tolerance must be positive."
            )


@dataclass(frozen=True, slots=True)
class StandardizationModel:
    columns: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class PcaModel:
    feature_columns: tuple[str, ...]
    components: tuple[tuple[float, ...], ...]
    explained_variance_ratio: tuple[float, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class KMeansModel:
    cluster_count: int
    centroids: tuple[tuple[float, ...], ...]
    iterations: int
    inertia: float
    converged: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def load_clustering_observations(
    path: str | Path,
    *,
    config: MorphologyClusteringConfig = (
        MorphologyClusteringConfig()
    ),
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "rank_state",
        "transition",
        *config.feature_columns,
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Morphology observations are missing "
            f"required columns: {missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    for column in config.feature_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "asset",
            "rank_state",
            "transition",
            *config.feature_columns,
        ]
    )

    return (
        frame.sort_values(
            [
                c
                for c in ("timestamp", "asset")
                if c in frame.columns
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def deterministic_sample(
    frame: pd.DataFrame,
    *,
    sample_size: int,
    random_seed: int,
) -> pd.DataFrame:
    if len(frame) <= sample_size:
        return frame.copy()

    return (
        frame.sample(
            n=sample_size,
            random_state=random_seed,
            replace=False,
        )
        .sort_values(
            [
                c
                for c in ("timestamp", "asset")
                if c in frame.columns
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def fit_standardizer(
    frame: pd.DataFrame,
    *,
    columns: Iterable[str],
) -> StandardizationModel:
    names = tuple(columns)

    matrix = frame[
        list(names)
    ].to_numpy(
        dtype=float,
        copy=True,
    )

    means = np.nanmean(
        matrix,
        axis=0,
    )

    scales = np.nanstd(
        matrix,
        axis=0,
        ddof=0,
    )

    scales = np.where(
        scales > 0.0,
        scales,
        1.0,
    )

    return StandardizationModel(
        columns=names,
        means=tuple(
            float(value)
            for value in means
        ),
        scales=tuple(
            float(value)
            for value in scales
        ),
    )


def transform_standardized(
    frame: pd.DataFrame,
    model: StandardizationModel,
) -> np.ndarray:
    matrix = frame[
        list(model.columns)
    ].to_numpy(
        dtype=float,
        copy=True,
    )

    means = np.asarray(
        model.means,
        dtype=float,
    )

    scales = np.asarray(
        model.scales,
        dtype=float,
    )

    return (
        matrix - means
    ) / scales


def fit_pca(
    standardized: np.ndarray,
    *,
    feature_columns: tuple[str, ...],
    component_count: int,
) -> PcaModel:
    if standardized.ndim != 2:
        raise ValueError(
            "standardized matrix must be two-dimensional."
        )

    maximum_components = min(
        standardized.shape[0],
        standardized.shape[1],
    )

    count = min(
        int(component_count),
        maximum_components,
    )

    _, singular_values, right_vectors = (
        np.linalg.svd(
            standardized,
            full_matrices=False,
        )
    )

    components = right_vectors[
        :count
    ]

    variance = singular_values ** 2

    total_variance = float(
        variance.sum()
    )

    if total_variance > 0.0:
        ratios = (
            variance[:count]
            / total_variance
        )
    else:
        ratios = np.zeros(
            count,
            dtype=float,
        )

    return PcaModel(
        feature_columns=feature_columns,
        components=tuple(
            tuple(
                float(value)
                for value in row
            )
            for row in components
        ),
        explained_variance_ratio=tuple(
            float(value)
            for value in ratios
        ),
    )


def transform_pca(
    standardized: np.ndarray,
    model: PcaModel,
) -> np.ndarray:
    components = np.asarray(
        model.components,
        dtype=float,
    )

    return standardized @ components.T


def squared_distances(
    matrix: np.ndarray,
    centroids: np.ndarray,
) -> np.ndarray:
    return np.sum(
        (
            matrix[:, None, :]
            - centroids[None, :, :]
        ) ** 2,
        axis=2,
    )


def initialize_kmeans_plus_plus(
    matrix: np.ndarray,
    *,
    cluster_count: int,
    random_seed: int,
) -> np.ndarray:
    if len(matrix) < cluster_count:
        raise ValueError(
            "cluster_count exceeds observation count."
        )

    generator = np.random.default_rng(
        random_seed
    )

    chosen = [
        int(
            generator.integers(
                0,
                len(matrix),
            )
        )
    ]

    while len(chosen) < cluster_count:
        current = matrix[
            chosen
        ]

        minimum_distance = (
            squared_distances(
                matrix,
                current,
            )
            .min(axis=1)
        )

        minimum_distance[
            chosen
        ] = 0.0

        total = float(
            minimum_distance.sum()
        )

        if total <= 0.0:
            remaining = [
                index
                for index in range(
                    len(matrix)
                )
                if index not in chosen
            ]

            chosen.append(
                remaining[0]
            )

            continue

        probabilities = (
            minimum_distance
            / total
        )

        next_index = int(
            generator.choice(
                len(matrix),
                p=probabilities,
            )
        )

        if next_index not in chosen:
            chosen.append(
                next_index
            )

    return matrix[
        chosen
    ].copy()


def fit_kmeans(
    matrix: np.ndarray,
    *,
    cluster_count: int,
    maximum_iterations: int,
    convergence_tolerance: float,
    random_seed: int,
) -> KMeansModel:
    centroids = (
        initialize_kmeans_plus_plus(
            matrix,
            cluster_count=cluster_count,
            random_seed=random_seed,
        )
    )

    converged = False
    iteration_count = 0

    for iteration in range(
        1,
        maximum_iterations + 1,
    ):
        iteration_count = iteration

        distances = squared_distances(
            matrix,
            centroids,
        )

        labels = distances.argmin(
            axis=1
        )

        updated = centroids.copy()

        for cluster_id in range(
            cluster_count
        ):
            members = matrix[
                labels == cluster_id
            ]

            if len(members) > 0:
                updated[
                    cluster_id
                ] = members.mean(
                    axis=0
                )

        movement = float(
            np.linalg.norm(
                updated - centroids
            )
        )

        centroids = updated

        if movement <= convergence_tolerance:
            converged = True
            break

    final_distances = squared_distances(
        matrix,
        centroids,
    )

    final_labels = final_distances.argmin(
        axis=1
    )

    inertia = float(
        final_distances[
            np.arange(
                len(matrix)
            ),
            final_labels,
        ].sum()
    )

    return KMeansModel(
        cluster_count=int(
            cluster_count
        ),
        centroids=tuple(
            tuple(
                float(value)
                for value in row
            )
            for row in centroids
        ),
        iterations=int(
            iteration_count
        ),
        inertia=inertia,
        converged=bool(
            converged
        ),
    )


def assign_clusters(
    matrix: np.ndarray,
    model: KMeansModel,
) -> tuple[np.ndarray, np.ndarray]:
    centroids = np.asarray(
        model.centroids,
        dtype=float,
    )

    distances = squared_distances(
        matrix,
        centroids,
    )

    labels = distances.argmin(
        axis=1
    )

    nearest = distances[
        np.arange(
            len(matrix)
        ),
        labels,
    ]

    return (
        labels.astype(int),
        np.sqrt(nearest),
    )


def centroid_separation(
    model: KMeansModel,
) -> float:
    centroids = np.asarray(
        model.centroids,
        dtype=float,
    )

    if len(centroids) < 2:
        return 0.0

    distances = np.sqrt(
        squared_distances(
            centroids,
            centroids,
        )
    )

    mask = ~np.eye(
        len(centroids),
        dtype=bool,
    )

    values = distances[
        mask
    ]

    return float(
        values.mean()
    ) if len(values) else 0.0


def build_cluster_diagnostics(
    fit_matrix: np.ndarray,
    *,
    config: MorphologyClusteringConfig,
) -> tuple[pd.DataFrame, dict[int, KMeansModel]]:
    rows = []
    models: dict[int, KMeansModel] = {}

    for cluster_count in config.cluster_counts:
        model = fit_kmeans(
            fit_matrix,
            cluster_count=cluster_count,
            maximum_iterations=(
                config.maximum_iterations
            ),
            convergence_tolerance=(
                config.convergence_tolerance
            ),
            random_seed=(
                config.random_seed
                + cluster_count
            ),
        )

        models[
            cluster_count
        ] = model

        rows.append({
            "cluster_count":
                int(cluster_count),
            "inertia":
                float(model.inertia),
            "inertia_per_observation":
                float(
                    model.inertia
                    / max(
                        len(fit_matrix),
                        1,
                    )
                ),
            "centroid_separation":
                centroid_separation(
                    model
                ),
            "iterations":
                int(model.iterations),
            "converged":
                bool(model.converged),
            "selected":
                bool(
                    cluster_count
                    == config.selected_cluster_count
                ),
        })

    return (
        pd.DataFrame(rows),
        models,
    )


def cluster_identity(
    *,
    cluster_count: int,
    cluster_id: int,
    centroid: Iterable[float],
) -> str:
    payload = json.dumps(
        {
            "cluster_count":
                int(cluster_count),
            "cluster_id":
                int(cluster_id),
            "centroid": [
                round(
                    float(value),
                    12,
                )
                for value in centroid
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")

    digest = hashlib.sha256(
        payload
    ).hexdigest()[:12]

    return (
        f"MORPH-{cluster_count:02d}-"
        f"{cluster_id:02d}-{digest}"
    )


def build_cluster_assignments(
    observations: pd.DataFrame,
    *,
    standardizer: StandardizationModel,
    pca_model: PcaModel,
    kmeans_model: KMeansModel,
) -> pd.DataFrame:
    standardized = transform_standardized(
        observations,
        standardizer,
    )

    projected = transform_pca(
        standardized,
        pca_model,
    )

    labels, distances = assign_clusters(
        projected,
        kmeans_model,
    )

    frame = observations.copy()

    frame["morphology_cluster_id"] = labels

    frame["morphology_cluster"] = [
        cluster_identity(
            cluster_count=(
                kmeans_model.cluster_count
            ),
            cluster_id=int(label),
            centroid=(
                kmeans_model.centroids[
                    int(label)
                ]
            ),
        )
        for label in labels
    ]

    frame[
        "morphology_cluster_distance"
    ] = distances

    for component_index in range(
        projected.shape[1]
    ):
        frame[
            f"morphology_pc_{component_index + 1}"
        ] = projected[
            :,
            component_index,
        ]

    return frame


def build_cluster_profiles(
    assignments: pd.DataFrame,
    *,
    config: MorphologyClusteringConfig,
) -> pd.DataFrame:
    rows = []

    grouped = assignments.groupby(
        [
            "morphology_cluster_id",
            "morphology_cluster",
            "asset",
        ],
        sort=True,
        observed=True,
    )

    for (
        cluster_id,
        cluster_name,
        asset,
    ), group in grouped:
        row: dict[str, Any] = {
            "morphology_cluster_id":
                int(cluster_id),
            "morphology_cluster":
                str(cluster_name),
            "observation_count":
                int(len(group)),
            "asset":
                str(asset),
            "timestamp_min":
                group[
                    "timestamp"
                ].min().isoformat(),
            "timestamp_max":
                group[
                    "timestamp"
                ].max().isoformat(),
            "dominant_rank_state":
                str(
                    group[
                        "rank_state"
                    ].value_counts().index[0]
                ),
            "dominant_transition":
                str(
                    group[
                        "transition"
                    ].value_counts().index[0]
                ),
        }

        for feature in config.feature_columns:
            row[
                f"mean_{feature}"
            ] = float(
                pd.to_numeric(
                    group[feature],
                    errors="coerce",
                ).mean()
            )

        for horizon in config.outcome_horizons:
            long_column = (
                f"forward_return_{horizon}"
            )

            short_column = (
                f"short_return_{horizon}"
            )

            if long_column in group.columns:
                long_values = pd.to_numeric(
                    group[long_column],
                    errors="coerce",
                ).dropna()

                row[
                    f"long_mean_return_{horizon}"
                ] = float(
                    long_values.mean()
                ) if len(long_values) else 0.0

                row[
                    f"long_win_rate_{horizon}"
                ] = float(
                    (
                        long_values > 0.0
                    ).mean()
                ) if len(long_values) else 0.0

            if short_column in group.columns:
                short_values = pd.to_numeric(
                    group[short_column],
                    errors="coerce",
                ).dropna()

                row[
                    f"short_mean_return_{horizon}"
                ] = float(
                    short_values.mean()
                ) if len(short_values) else 0.0

                row[
                    f"short_win_rate_{horizon}"
                ] = float(
                    (
                        short_values > 0.0
                    ).mean()
                ) if len(short_values) else 0.0

        rows.append(
            row
        )

    return (
        pd.DataFrame(rows)
        .sort_values(
            [
                "observation_count",
                "morphology_cluster_id",
            ],
            ascending=[
                False,
                True,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def build_cluster_transition_matrix(
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    unique_states = (
        assignments[
            [
                "timestamp",
                "morphology_cluster_id",
                "morphology_cluster",
            ]
        ]
        .drop_duplicates(
            subset=["timestamp"],
            keep="first",
        )
        .sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )

    unique_states[
        "next_cluster_id"
    ] = unique_states[
        "morphology_cluster_id"
    ].shift(-1)

    unique_states[
        "next_cluster"
    ] = unique_states[
        "morphology_cluster"
    ].shift(-1)

    transitions = unique_states.dropna(
        subset=[
            "next_cluster_id",
            "next_cluster",
        ]
    ).copy()

    if transitions.empty:
        return pd.DataFrame()

    matrix = (
        transitions.groupby(
            [
                "morphology_cluster_id",
                "morphology_cluster",
                "next_cluster_id",
                "next_cluster",
            ],
            sort=True,
            observed=True,
        )
        .size()
        .rename(
            "transition_count"
        )
        .reset_index()
    )

    totals = (
        matrix.groupby(
            "morphology_cluster_id"
        )["transition_count"]
        .transform("sum")
    )

    matrix[
        "transition_probability"
    ] = (
        matrix[
            "transition_count"
        ]
        / totals
    )

    return (
        matrix.sort_values(
            [
                "morphology_cluster_id",
                "transition_probability",
            ],
            ascending=[
                True,
                False,
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def write_clustering_outputs(
    *,
    assignments: pd.DataFrame,
    profiles: pd.DataFrame,
    transitions: pd.DataFrame,
    diagnostics: pd.DataFrame,
    standardizer: StandardizationModel,
    pca_model: PcaModel,
    kmeans_model: KMeansModel,
    config: MorphologyClusteringConfig,
    output_dir: str | Path,
) -> dict[str, Path]:
    directory = Path(
        output_dir
    )

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    assignments_path = (
        directory
        / "morphology_cluster_assignments.csv"
    )

    profiles_path = (
        directory
        / "morphology_cluster_profiles.csv"
    )

    transitions_path = (
        directory
        / "morphology_cluster_transitions.csv"
    )

    diagnostics_path = (
        directory
        / "morphology_cluster_diagnostics.csv"
    )

    model_path = (
        directory
        / "morphology_cluster_model.json"
    )

    summary_path = (
        directory
        / "morphology_cluster_summary.json"
    )

    assignments.to_csv(
        assignments_path,
        index=False,
    )

    profiles.to_csv(
        profiles_path,
        index=False,
    )

    transitions.to_csv(
        transitions_path,
        index=False,
    )

    diagnostics.to_csv(
        diagnostics_path,
        index=False,
    )

    model_payload = {
        "schema_version":
            "atlas.morphology_clustering.v1",
        "config":
            asdict(config),
        "standardizer":
            standardizer.to_dict(),
        "pca":
            pca_model.to_dict(),
        "kmeans":
            kmeans_model.to_dict(),
    }

    model_path.write_text(
        json.dumps(
            model_payload,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    summary = {
        "schema_version":
            "atlas.morphology_clustering.summary.v1",
        "observation_count":
            int(len(assignments)),
        "cluster_count":
            int(kmeans_model.cluster_count),
        "profile_count":
            int(len(profiles)),
        "transition_rows":
            int(len(transitions)),
        "explained_variance_ratio":
            list(
                pca_model.explained_variance_ratio
            ),
        "explained_variance_total":
            float(
                sum(
                    pca_model.explained_variance_ratio
                )
            ),
        "largest_clusters": (
            profiles.head(20)
            .to_dict(
                orient="records"
            )
        ),
    }

    summary_path.write_text(
        json.dumps(
            summary,
            indent=2,
            sort_keys=True,
            default=str,
        )
        + "\n",
        encoding="utf-8",
    )

    return {
        "assignments":
            assignments_path,
        "profiles":
            profiles_path,
        "transitions":
            transitions_path,
        "diagnostics":
            diagnostics_path,
        "model":
            model_path,
        "summary":
            summary_path,
    }


def run_morphology_clustering(
    observations: pd.DataFrame,
    *,
    config: MorphologyClusteringConfig = (
        MorphologyClusteringConfig()
    ),
) -> dict[str, Any]:
    morphology_frame = (
        observations[
            [
                "timestamp",
                "rank_state",
                "transition",
                *config.feature_columns,
            ]
        ]
        .drop_duplicates(
            subset=["timestamp"],
            keep="first",
        )
        .sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )

    fit_frame = deterministic_sample(
        morphology_frame,
        sample_size=(
            config.fit_sample_size
        ),
        random_seed=(
            config.random_seed
        ),
    )

    standardizer = fit_standardizer(
        fit_frame,
        columns=config.feature_columns,
    )

    fit_standardized = (
        transform_standardized(
            fit_frame,
            standardizer,
        )
    )

    pca_model = fit_pca(
        fit_standardized,
        feature_columns=(
            config.feature_columns
        ),
        component_count=(
            config.pca_components
        ),
    )

    fit_projected = transform_pca(
        fit_standardized,
        pca_model,
    )

    diagnostics, models = (
        build_cluster_diagnostics(
            fit_projected,
            config=config,
        )
    )

    selected_model = models[
        config.selected_cluster_count
    ]

    timestamp_assignments = (
        build_cluster_assignments(
            morphology_frame,
            standardizer=standardizer,
            pca_model=pca_model,
            kmeans_model=selected_model,
        )
    )

    cluster_columns = [
        "timestamp",
        "morphology_cluster_id",
        "morphology_cluster",
        "morphology_cluster_distance",
    ] + [
        column
        for column
        in timestamp_assignments.columns
        if column.startswith(
            "morphology_pc_"
        )
    ]

    assignments = observations.merge(
        timestamp_assignments[
            cluster_columns
        ],
        on="timestamp",
        how="inner",
        validate="many_to_one",
    )

    profiles = build_cluster_profiles(
        assignments,
        config=config,
    )

    transitions = (
        build_cluster_transition_matrix(
            assignments
        )
    )

    return {
        "fit_frame":
            fit_frame,
        "standardizer":
            standardizer,
        "pca_model":
            pca_model,
        "kmeans_model":
            selected_model,
        "diagnostics":
            diagnostics,
        "assignments":
            assignments,
        "profiles":
            profiles,
        "transitions":
            transitions,
    }
