"""Continuous morphology evolution intelligence.

The engine measures motion through learned morphology space:

- velocity;
- acceleration;
- curvature;
- directional stability;
- distance to historically favorable attractor clusters;
- closing velocity toward attractors;
- estimated time to attractor.

Point-in-time motion features never use future outcome labels. Outcome profiles
are used only to identify candidate attractor clusters after clustering.

Research only:
- no portfolio sizing;
- no order generation;
- no live execution.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


@dataclass(frozen=True, slots=True)
class MorphologyEvolutionConfig:
    derivative_lag: int = 1
    smoothing_window: int = 4
    attractor_horizon: int = 16
    minimum_attractor_observations: int = 500
    attractors_per_asset: int = 3
    minimum_attractor_return: float = 0.0
    maximum_eta_bars: float = 10_000.0
    stability_window: int = 8

    def __post_init__(self) -> None:
        if self.derivative_lag < 1:
            raise ValueError(
                "derivative_lag must be positive."
            )

        if self.smoothing_window < 1:
            raise ValueError(
                "smoothing_window must be positive."
            )

        if self.attractor_horizon < 1:
            raise ValueError(
                "attractor_horizon must be positive."
            )

        if self.minimum_attractor_observations < 1:
            raise ValueError(
                "minimum_attractor_observations must be positive."
            )

        if self.attractors_per_asset < 1:
            raise ValueError(
                "attractors_per_asset must be positive."
            )

        if (
            not math.isfinite(
                self.maximum_eta_bars
            )
            or self.maximum_eta_bars <= 0.0
        ):
            raise ValueError(
                "maximum_eta_bars must be finite and positive."
            )

        if self.stability_window < 2:
            raise ValueError(
                "stability_window must be at least 2."
            )


def load_evolution_assignments(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "morphology_cluster_id",
        "morphology_cluster",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Evolution assignments are missing "
            f"required columns: {missing}"
        )

    pc_columns = sorted(
        column
        for column in frame.columns
        if column.startswith(
            "morphology_pc_"
        )
    )

    if not pc_columns:
        raise ValueError(
            "No morphology_pc_* columns were found."
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

    frame["morphology_cluster_id"] = (
        pd.to_numeric(
            frame[
                "morphology_cluster_id"
            ],
            errors="coerce",
        )
    )

    for column in pc_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "asset",
            "morphology_cluster_id",
            *pc_columns,
        ]
    )

    frame[
        "morphology_cluster_id"
    ] = frame[
        "morphology_cluster_id"
    ].astype(int)

    cluster_counts = (
        frame.groupby(
            "timestamp",
            observed=True,
        )[
            "morphology_cluster_id"
        ]
        .nunique()
    )

    if not cluster_counts.eq(1).all():
        raise ValueError(
            "Each timestamp must map to exactly one cluster."
        )

    return (
        frame.sort_values(
            [
                "timestamp",
                "asset",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def load_evolution_profiles(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "morphology_cluster_id",
        "morphology_cluster",
        "asset",
        "observation_count",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Evolution profiles are missing "
            f"required columns: {missing}"
        )

    frame = frame.copy()

    frame["asset"] = (
        frame["asset"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    frame["morphology_cluster_id"] = (
        pd.to_numeric(
            frame[
                "morphology_cluster_id"
            ],
            errors="coerce",
        )
    )

    frame["observation_count"] = (
        pd.to_numeric(
            frame["observation_count"],
            errors="coerce",
        )
        .fillna(0)
        .astype(int)
    )

    return frame.dropna(
        subset=[
            "morphology_cluster_id",
            "asset",
        ]
    ).reset_index(drop=True)


def morphology_pc_columns(
    frame: pd.DataFrame,
) -> tuple[str, ...]:
    columns = tuple(
        sorted(
            column
            for column in frame.columns
            if column.startswith(
                "morphology_pc_"
            )
        )
    )

    if not columns:
        raise ValueError(
            "Morphology PCA coordinates are required."
        )

    return columns


def build_timestamp_geometry(
    assignments: pd.DataFrame,
) -> pd.DataFrame:
    pcs = morphology_pc_columns(
        assignments
    )

    columns = [
        "timestamp",
        "morphology_cluster_id",
        "morphology_cluster",
        *pcs,
    ]

    frame = (
        assignments[
            columns
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

    return frame


def vector_norm(
    matrix: np.ndarray,
) -> np.ndarray:
    return np.sqrt(
        np.sum(
            matrix ** 2,
            axis=1,
        )
    )


def safe_unit_vectors(
    matrix: np.ndarray,
) -> np.ndarray:
    norms = vector_norm(
        matrix
    )

    result = np.zeros_like(
        matrix,
        dtype=float,
    )

    valid = norms > 0.0

    result[valid] = (
        matrix[valid]
        / norms[valid, None]
    )

    return result


def build_motion_features(
    geometry: pd.DataFrame,
    *,
    config: MorphologyEvolutionConfig,
) -> pd.DataFrame:
    frame = geometry.copy()

    pcs = morphology_pc_columns(
        frame
    )

    coordinates = frame[
        list(pcs)
    ].to_numpy(
        dtype=float,
        copy=True,
    )

    lag = int(
        config.derivative_lag
    )

    velocity = np.full_like(
        coordinates,
        np.nan,
        dtype=float,
    )

    velocity[lag:] = (
        coordinates[lag:]
        - coordinates[:-lag]
    ) / float(lag)

    acceleration = np.full_like(
        coordinates,
        np.nan,
        dtype=float,
    )

    acceleration[lag:] = (
        velocity[lag:]
        - velocity[:-lag]
    ) / float(lag)

    velocity_units = safe_unit_vectors(
        np.nan_to_num(
            velocity,
            nan=0.0,
        )
    )

    curvature = np.full(
        len(frame),
        np.nan,
        dtype=float,
    )

    if len(frame) > lag:
        unit_change = (
            velocity_units[lag:]
            - velocity_units[:-lag]
        )

        curvature[lag:] = vector_norm(
            unit_change
        ) / float(lag)

    speed = vector_norm(
        np.nan_to_num(
            velocity,
            nan=0.0,
        )
    )

    acceleration_magnitude = vector_norm(
        np.nan_to_num(
            acceleration,
            nan=0.0,
        )
    )

    radial_position = vector_norm(
        coordinates
    )

    for index, column in enumerate(
        pcs
    ):
        suffix = column.replace(
            "morphology_pc_",
            "",
        )

        frame[
            f"morphology_velocity_{suffix}"
        ] = velocity[
            :,
            index,
        ]

        frame[
            f"morphology_acceleration_{suffix}"
        ] = acceleration[
            :,
            index,
        ]

    frame[
        "morphology_speed"
    ] = speed

    frame[
        "morphology_acceleration_magnitude"
    ] = acceleration_magnitude

    frame[
        "morphology_curvature"
    ] = curvature

    frame[
        "morphology_radius"
    ] = radial_position

    frame[
        "morphology_radial_velocity"
    ] = (
        frame[
            "morphology_radius"
        ]
        .diff(lag)
        / float(lag)
    )

    frame[
        "morphology_speed_smoothed"
    ] = (
        frame[
            "morphology_speed"
        ]
        .rolling(
            config.smoothing_window,
            min_periods=1,
        )
        .mean()
    )

    frame[
        "morphology_curvature_smoothed"
    ] = (
        frame[
            "morphology_curvature"
        ]
        .rolling(
            config.smoothing_window,
            min_periods=1,
        )
        .mean()
    )

    frame[
        "morphology_directional_stability"
    ] = (
        1.0
        / (
            1.0
            + frame[
                "morphology_curvature_smoothed"
            ].fillna(0.0)
        )
    )

    frame[
        "morphology_speed_stability"
    ] = (
        1.0
        / (
            1.0
            + frame[
                "morphology_speed"
            ]
            .rolling(
                config.stability_window,
                min_periods=2,
            )
            .std(ddof=0)
            .fillna(0.0)
        )
    )

    frame[
        "morphology_motion_state"
    ] = np.select(
        [
            frame[
                "morphology_speed_smoothed"
            ].le(
                frame[
                    "morphology_speed_smoothed"
                ].quantile(0.25)
            ),
            frame[
                "morphology_curvature_smoothed"
            ].ge(
                frame[
                    "morphology_curvature_smoothed"
                ].quantile(0.75)
            ),
            frame[
                "morphology_acceleration_magnitude"
            ].gt(
                frame[
                    "morphology_acceleration_magnitude"
                ].quantile(0.75)
            ),
        ],
        [
            "STATIONARY",
            "TURNING",
            "ACCELERATING",
        ],
        default="FLOWING",
    )

    return frame


def build_cluster_centroids(
    geometry: pd.DataFrame,
) -> pd.DataFrame:
    pcs = morphology_pc_columns(
        geometry
    )

    aggregation = {
        column: "mean"
        for column in pcs
    }

    return (
        geometry.groupby(
            [
                "morphology_cluster_id",
                "morphology_cluster",
            ],
            sort=True,
            observed=True,
        )
        .agg(aggregation)
        .reset_index()
    )


def select_attractor_clusters(
    profiles: pd.DataFrame,
    *,
    config: MorphologyEvolutionConfig,
) -> pd.DataFrame:
    return_column = (
        f"long_mean_return_"
        f"{config.attractor_horizon}"
    )

    win_rate_column = (
        f"long_win_rate_"
        f"{config.attractor_horizon}"
    )

    if return_column not in profiles.columns:
        raise ValueError(
            f"Missing profile column: {return_column}"
        )

    frame = profiles.copy()

    frame[return_column] = pd.to_numeric(
        frame[return_column],
        errors="coerce",
    )

    if win_rate_column in frame.columns:
        frame[win_rate_column] = (
            pd.to_numeric(
                frame[win_rate_column],
                errors="coerce",
            )
        )
    else:
        frame[win_rate_column] = 0.0

    frame = frame[
        frame[
            "observation_count"
        ].ge(
            config.minimum_attractor_observations
        )
        & frame[
            return_column
        ].gt(
            config.minimum_attractor_return
        )
    ].copy()

    if frame.empty:
        return frame

    frame[
        "attractor_strength"
    ] = (
        frame[
            return_column
        ]
        * np.sqrt(
            frame[
                "observation_count"
            ].clip(lower=1)
        )
        * (
            0.5
            + frame[
                win_rate_column
            ].fillna(0.0)
        )
    )

    frame[
        "attractor_rank"
    ] = (
        frame.groupby(
            "asset",
            observed=True,
        )[
            "attractor_strength"
        ]
        .rank(
            method="first",
            ascending=False,
        )
    )

    frame = frame[
        frame[
            "attractor_rank"
        ].le(
            config.attractors_per_asset
        )
    ]

    return (
        frame.sort_values(
            [
                "asset",
                "attractor_rank",
            ],
            kind="stable",
        )
        .reset_index(drop=True)
    )


def attach_attractor_geometry(
    attractors: pd.DataFrame,
    centroids: pd.DataFrame,
) -> pd.DataFrame:
    return attractors.merge(
        centroids,
        on=[
            "morphology_cluster_id",
            "morphology_cluster",
        ],
        how="inner",
        validate="many_to_one",
    )


def calculate_attractor_observations(
    motion: pd.DataFrame,
    attractors: pd.DataFrame,
    *,
    config: MorphologyEvolutionConfig,
) -> pd.DataFrame:
    if attractors.empty:
        return pd.DataFrame()

    pcs = morphology_pc_columns(
        motion
    )

    velocity_columns = [
        column.replace(
            "morphology_pc_",
            "morphology_velocity_",
        )
        for column in pcs
    ]

    rows = []

    for attractor in attractors.itertuples(
        index=False
    ):
        target = np.asarray(
            [
                float(
                    getattr(
                        attractor,
                        column,
                    )
                )
                for column in pcs
            ],
            dtype=float,
        )

        coordinates = motion[
            list(pcs)
        ].to_numpy(
            dtype=float,
            copy=True,
        )

        velocities = motion[
            velocity_columns
        ].to_numpy(
            dtype=float,
            copy=True,
        )

        displacement = (
            target[None, :]
            - coordinates
        )

        distance = vector_norm(
            displacement
        )

        direction = safe_unit_vectors(
            displacement
        )

        closing_velocity = np.sum(
            np.nan_to_num(
                velocities,
                nan=0.0,
            )
            * direction,
            axis=1,
        )

        eta = np.full(
            len(motion),
            np.inf,
            dtype=float,
        )

        approaching = (
            closing_velocity > 0.0
        )

        eta[approaching] = (
            distance[approaching]
            / closing_velocity[
                approaching
            ]
        )

        eta = np.minimum(
            eta,
            config.maximum_eta_bars,
        )

        frame = motion[
            [
                "timestamp",
                "morphology_cluster_id",
                "morphology_cluster",
                "morphology_speed",
                "morphology_acceleration_magnitude",
                "morphology_curvature",
                "morphology_directional_stability",
                "morphology_speed_stability",
                "morphology_motion_state",
            ]
        ].copy()

        frame["asset"] = str(
            getattr(
                attractor,
                "asset",
            )
        )

        frame[
            "attractor_cluster_id"
        ] = int(
            getattr(
                attractor,
                "morphology_cluster_id",
            )
        )

        frame[
            "attractor_cluster"
        ] = str(
            getattr(
                attractor,
                "morphology_cluster",
            )
        )

        frame[
            "attractor_rank"
        ] = int(
            getattr(
                attractor,
                "attractor_rank",
            )
        )

        frame[
            "attractor_strength"
        ] = float(
            getattr(
                attractor,
                "attractor_strength",
            )
        )

        frame[
            "distance_to_attractor"
        ] = distance

        frame[
            "attractor_closing_velocity"
        ] = closing_velocity

        frame[
            "approaching_attractor"
        ] = approaching

        frame[
            "estimated_bars_to_attractor"
        ] = eta

        frame[
            "attractor_alignment_score"
        ] = (
            np.maximum(
                closing_velocity,
                0.0,
            )
            * float(
                getattr(
                    attractor,
                    "attractor_strength",
                )
            )
            / (
                1.0
                + distance
            )
        )

        rows.append(
            frame
        )

    return pd.concat(
        rows,
        ignore_index=True,
    )


def select_nearest_attractor(
    observations: pd.DataFrame,
) -> pd.DataFrame:
    if observations.empty:
        return observations

    ranked = observations.sort_values(
        [
            "timestamp",
            "asset",
            "distance_to_attractor",
            "attractor_rank",
        ],
        ascending=[
            True,
            True,
            True,
            True,
        ],
        kind="stable",
    )

    nearest = (
        ranked.groupby(
            [
                "timestamp",
                "asset",
            ],
            observed=True,
        )
        .head(1)
        .reset_index(drop=True)
    )

    speed = nearest[
        "morphology_speed"
    ].clip(lower=1e-12)

    nearest[
        "attractor_closing_efficiency"
    ] = (
        nearest[
            "attractor_closing_velocity"
        ]
        / speed
    )

    nearest[
        "distance_percentile"
    ] = (
        nearest.groupby(
            "asset",
            observed=True,
        )[
            "distance_to_attractor"
        ]
        .rank(
            method="average",
            pct=True,
        )
    )

    valid_eta = nearest[
        "estimated_bars_to_attractor"
    ].where(
        nearest[
            "estimated_bars_to_attractor"
        ].lt(
            10000.0
        )
    )

    nearest[
        "eta_percentile"
    ] = (
        valid_eta.groupby(
            nearest["asset"]
        )
        .rank(
            method="average",
            pct=True,
        )
        .fillna(1.0)
    )

    approaching = nearest[
        "attractor_closing_efficiency"
    ].gt(0.0)

    strong_alignment = nearest[
        "attractor_closing_efficiency"
    ].ge(0.50)

    moderate_alignment = nearest[
        "attractor_closing_efficiency"
    ].ge(0.20)

    near_attractor = nearest[
        "distance_percentile"
    ].le(0.35)

    short_eta = nearest[
        "eta_percentile"
    ].le(0.35)

    stable_motion = nearest[
        "morphology_directional_stability"
    ].ge(0.40)

    nearest[
        "evolution_signal"
    ] = np.select(
        [
            approaching
            & strong_alignment
            & near_attractor
            & short_eta
            & stable_motion,

            approaching
            & moderate_alignment
            & (
                near_attractor
                | short_eta
            ),

            approaching,

            nearest[
                "attractor_closing_efficiency"
            ].ge(-0.10),

            nearest[
                "attractor_closing_efficiency"
            ].gt(-0.50),
        ],
        [
            "STRONG_APPROACH",
            "APPROACH",
            "WEAK_APPROACH",
            "TANGENTIAL",
            "WEAK_RECESSION",
        ],
        default="RECEDING",
    )

    return nearest


def build_evolution_summary(
    nearest: pd.DataFrame,
) -> dict[str, Any]:
    if nearest.empty:
        return {
            "row_count": 0,
            "latest": [],
        }

    latest_timestamp = nearest[
        "timestamp"
    ].max()

    latest = nearest[
        nearest[
            "timestamp"
        ].eq(
            latest_timestamp
        )
    ]

    return {
        "row_count":
            int(len(nearest)),
        "timestamp_min":
            nearest[
                "timestamp"
            ].min().isoformat(),
        "timestamp_max":
            latest_timestamp.isoformat(),
        "asset_count":
            int(
                nearest[
                    "asset"
                ].nunique()
            ),
        "latest":
            latest.to_dict(
                orient="records",
            ),
    }


def write_evolution_outputs(
    *,
    motion: pd.DataFrame,
    attractors: pd.DataFrame,
    attractor_observations: pd.DataFrame,
    nearest_attractors: pd.DataFrame,
    config: MorphologyEvolutionConfig,
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
        "motion":
            directory
            / "morphology_evolution_motion.csv",
        "attractors":
            directory
            / "morphology_evolution_attractors.csv",
        "attractor_observations":
            directory
            / "morphology_evolution_attractor_observations.csv",
        "nearest_attractors":
            directory
            / "morphology_evolution_nearest_attractors.csv",
        "summary":
            directory
            / "morphology_evolution_summary.json",
    }

    motion.to_csv(
        outputs["motion"],
        index=False,
    )

    attractors.to_csv(
        outputs["attractors"],
        index=False,
    )

    attractor_observations.to_csv(
        outputs[
            "attractor_observations"
        ],
        index=False,
    )

    nearest_attractors.to_csv(
        outputs[
            "nearest_attractors"
        ],
        index=False,
    )

    summary = {
        "schema_version":
            "atlas.morphology_evolution.v1",
        "config":
            asdict(config),
        "motion_rows":
            int(len(motion)),
        "attractor_count":
            int(len(attractors)),
        "attractor_observation_rows":
            int(
                len(
                    attractor_observations
                )
            ),
        "nearest_attractor_rows":
            int(
                len(
                    nearest_attractors
                )
            ),
        **build_evolution_summary(
            nearest_attractors
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


def run_morphology_evolution(
    *,
    assignments: pd.DataFrame,
    profiles: pd.DataFrame,
    config: MorphologyEvolutionConfig = (
        MorphologyEvolutionConfig()
    ),
) -> dict[str, Any]:
    geometry = build_timestamp_geometry(
        assignments
    )

    motion = build_motion_features(
        geometry,
        config=config,
    )

    centroids = build_cluster_centroids(
        geometry
    )

    selected_attractors = (
        select_attractor_clusters(
            profiles,
            config=config,
        )
    )

    attractors = attach_attractor_geometry(
        selected_attractors,
        centroids,
    )

    attractor_observations = (
        calculate_attractor_observations(
            motion,
            attractors,
            config=config,
        )
    )

    nearest = select_nearest_attractor(
        attractor_observations
    )

    return {
        "geometry":
            geometry,
        "motion":
            motion,
        "centroids":
            centroids,
        "attractors":
            attractors,
        "attractor_observations":
            attractor_observations,
        "nearest_attractors":
            nearest,
    }
