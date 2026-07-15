"""Spatial field dynamics over learned morphology space.

The engine converts morphology motion observations into a local vector field
over the first two PCA coordinates. It estimates finite-difference divergence,
curl, strain, expansion, contraction, rotational intensity, and a local
predictability proxy.

Research only:
- no order creation;
- no portfolio allocation;
- no live execution;
- no future outcome labels are used.
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
class MorphologyFieldConfig:
    grid_bins: int = 40
    minimum_cell_observations: int = 20
    smoothing_passes: int = 1
    maximum_absolute_derivative: float = 1000.0
    predictability_scale: float = 1.0

    def __post_init__(self) -> None:
        if self.grid_bins < 4:
            raise ValueError(
                "grid_bins must be at least 4."
            )

        if self.minimum_cell_observations < 1:
            raise ValueError(
                "minimum_cell_observations must be positive."
            )

        if self.smoothing_passes < 0:
            raise ValueError(
                "smoothing_passes cannot be negative."
            )

        if (
            not math.isfinite(
                self.maximum_absolute_derivative
            )
            or self.maximum_absolute_derivative <= 0.0
        ):
            raise ValueError(
                "maximum_absolute_derivative must be positive."
            )

        if (
            not math.isfinite(
                self.predictability_scale
            )
            or self.predictability_scale <= 0.0
        ):
            raise ValueError(
                "predictability_scale must be positive."
            )


def load_field_motion(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "morphology_cluster_id",
        "morphology_cluster",
        "morphology_pc_1",
        "morphology_pc_2",
        "morphology_velocity_1",
        "morphology_velocity_2",
        "morphology_speed",
        "morphology_acceleration_magnitude",
        "morphology_curvature",
        "morphology_directional_stability",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Field motion is missing required columns: "
            f"{missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    numeric_columns = sorted(
        required - {
            "timestamp",
            "morphology_cluster",
        }
    )

    for column in numeric_columns:
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    frame = frame.dropna(
        subset=[
            "timestamp",
            "morphology_pc_1",
            "morphology_pc_2",
            "morphology_velocity_1",
            "morphology_velocity_2",
        ]
    )

    return (
        frame.sort_values(
            "timestamp",
            kind="stable",
        )
        .drop_duplicates(
            subset=["timestamp"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_nearest_attractors(
    path: str | Path,
) -> pd.DataFrame:
    frame = pd.read_csv(
        path,
        low_memory=False,
    )

    required = {
        "timestamp",
        "asset",
        "distance_to_attractor",
        "attractor_closing_velocity",
        "attractor_alignment_score",
        "evolution_signal",
    }

    missing = sorted(
        required - set(frame.columns)
    )

    if missing:
        raise ValueError(
            "Attractor observations are missing columns: "
            f"{missing}"
        )

    frame = frame.copy()

    frame["timestamp"] = pd.to_datetime(
        frame["timestamp"],
        utc=True,
        errors="coerce",
    )

    for column in (
        "distance_to_attractor",
        "attractor_closing_velocity",
        "attractor_alignment_score",
    ):
        frame[column] = pd.to_numeric(
            frame[column],
            errors="coerce",
        )

    return frame.dropna(
        subset=[
            "timestamp",
            "asset",
        ]
    ).reset_index(drop=True)


def quantile_edges(
    values: pd.Series,
    *,
    bin_count: int,
) -> np.ndarray:
    numeric = pd.to_numeric(
        values,
        errors="coerce",
    ).dropna()

    if numeric.empty:
        raise ValueError(
            "Cannot build grid from an empty coordinate."
        )

    probabilities = np.linspace(
        0.0,
        1.0,
        bin_count + 1,
    )

    edges = np.quantile(
        numeric.to_numpy(dtype=float),
        probabilities,
    )

    edges = np.unique(
        edges
    )

    if len(edges) < 3:
        minimum = float(
            numeric.min()
        )

        maximum = float(
            numeric.max()
        )

        if minimum == maximum:
            maximum = minimum + 1.0

        edges = np.linspace(
            minimum,
            maximum,
            bin_count + 1,
        )

    edges[0] = -np.inf
    edges[-1] = np.inf

    return edges


def assign_field_cells(
    motion: pd.DataFrame,
    *,
    config: MorphologyFieldConfig,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    frame = motion.copy()

    x_edges = quantile_edges(
        frame["morphology_pc_1"],
        bin_count=config.grid_bins,
    )

    y_edges = quantile_edges(
        frame["morphology_pc_2"],
        bin_count=config.grid_bins,
    )

    frame["field_x_bin"] = (
        pd.cut(
            frame["morphology_pc_1"],
            bins=x_edges,
            labels=False,
            include_lowest=True,
        )
        .astype(int)
    )

    frame["field_y_bin"] = (
        pd.cut(
            frame["morphology_pc_2"],
            bins=y_edges,
            labels=False,
            include_lowest=True,
        )
        .astype(int)
    )

    frame["field_cell_id"] = (
        frame["field_x_bin"].astype(str)
        + ":"
        + frame["field_y_bin"].astype(str)
    )

    return frame, x_edges, y_edges


def build_field_cells(
    assigned: pd.DataFrame,
    *,
    config: MorphologyFieldConfig,
) -> pd.DataFrame:
    aggregation = (
        assigned.groupby(
            [
                "field_x_bin",
                "field_y_bin",
                "field_cell_id",
            ],
            sort=True,
            observed=True,
        )
        .agg(
            observation_count=(
                "timestamp",
                "size",
            ),
            x_center=(
                "morphology_pc_1",
                "mean",
            ),
            y_center=(
                "morphology_pc_2",
                "mean",
            ),
            field_velocity_x=(
                "morphology_velocity_1",
                "mean",
            ),
            field_velocity_y=(
                "morphology_velocity_2",
                "mean",
            ),
            field_speed=(
                "morphology_speed",
                "mean",
            ),
            field_acceleration=(
                "morphology_acceleration_magnitude",
                "mean",
            ),
            field_curvature=(
                "morphology_curvature",
                "mean",
            ),
            field_directional_stability=(
                "morphology_directional_stability",
                "mean",
            ),
        )
        .reset_index()
    )

    aggregation["field_eligible"] = (
        aggregation[
            "observation_count"
        ].ge(
            config.minimum_cell_observations
        )
    )

    return aggregation


def central_difference(
    negative_value: float | None,
    center_value: float,
    positive_value: float | None,
    negative_position: float | None,
    center_position: float,
    positive_position: float | None,
) -> float:
    if (
        negative_value is not None
        and positive_value is not None
        and negative_position is not None
        and positive_position is not None
        and positive_position != negative_position
    ):
        return (
            positive_value - negative_value
        ) / (
            positive_position - negative_position
        )

    if (
        positive_value is not None
        and positive_position is not None
        and positive_position != center_position
    ):
        return (
            positive_value - center_value
        ) / (
            positive_position - center_position
        )

    if (
        negative_value is not None
        and negative_position is not None
        and center_position != negative_position
    ):
        return (
            center_value - negative_value
        ) / (
            center_position - negative_position
        )

    return 0.0


def smooth_cell_vectors(
    cells: pd.DataFrame,
    *,
    passes: int,
) -> pd.DataFrame:
    frame = cells.copy()

    if passes <= 0 or frame.empty:
        return frame

    for _ in range(passes):
        velocity_x = []
        velocity_y = []

        lookup = {
            (
                int(row.field_x_bin),
                int(row.field_y_bin),
            ): row
            for row in frame.itertuples(
                index=False
            )
        }

        for row in frame.itertuples(
            index=False
        ):
            vectors_x = []
            vectors_y = []
            weights = []

            for offset_x in (-1, 0, 1):
                for offset_y in (-1, 0, 1):
                    neighbor = lookup.get(
                        (
                            int(row.field_x_bin)
                            + offset_x,
                            int(row.field_y_bin)
                            + offset_y,
                        )
                    )

                    if neighbor is None:
                        continue

                    weight = float(
                        max(
                            neighbor.observation_count,
                            1,
                        )
                    )

                    vectors_x.append(
                        float(
                            neighbor.field_velocity_x
                        )
                    )

                    vectors_y.append(
                        float(
                            neighbor.field_velocity_y
                        )
                    )

                    weights.append(weight)

            velocity_x.append(
                float(
                    np.average(
                        vectors_x,
                        weights=weights,
                    )
                )
            )

            velocity_y.append(
                float(
                    np.average(
                        vectors_y,
                        weights=weights,
                    )
                )
            )

        frame[
            "field_velocity_x"
        ] = velocity_x

        frame[
            "field_velocity_y"
        ] = velocity_y

    return frame


def calculate_field_derivatives(
    cells: pd.DataFrame,
    *,
    config: MorphologyFieldConfig,
) -> pd.DataFrame:
    frame = smooth_cell_vectors(
        cells,
        passes=config.smoothing_passes,
    )

    lookup = {
        (
            int(row.field_x_bin),
            int(row.field_y_bin),
        ): row
        for row in frame.itertuples(
            index=False
        )
    }

    rows: list[dict[str, Any]] = []

    for row in frame.itertuples(
        index=False
    ):
        x_bin = int(
            row.field_x_bin
        )

        y_bin = int(
            row.field_y_bin
        )

        left = lookup.get(
            (x_bin - 1, y_bin)
        )

        right = lookup.get(
            (x_bin + 1, y_bin)
        )

        down = lookup.get(
            (x_bin, y_bin - 1)
        )

        up = lookup.get(
            (x_bin, y_bin + 1)
        )

        dvx_dx = central_difference(
            (
                float(left.field_velocity_x)
                if left is not None
                else None
            ),
            float(row.field_velocity_x),
            (
                float(right.field_velocity_x)
                if right is not None
                else None
            ),
            (
                float(left.x_center)
                if left is not None
                else None
            ),
            float(row.x_center),
            (
                float(right.x_center)
                if right is not None
                else None
            ),
        )

        dvy_dx = central_difference(
            (
                float(left.field_velocity_y)
                if left is not None
                else None
            ),
            float(row.field_velocity_y),
            (
                float(right.field_velocity_y)
                if right is not None
                else None
            ),
            (
                float(left.x_center)
                if left is not None
                else None
            ),
            float(row.x_center),
            (
                float(right.x_center)
                if right is not None
                else None
            ),
        )

        dvx_dy = central_difference(
            (
                float(down.field_velocity_x)
                if down is not None
                else None
            ),
            float(row.field_velocity_x),
            (
                float(up.field_velocity_x)
                if up is not None
                else None
            ),
            (
                float(down.y_center)
                if down is not None
                else None
            ),
            float(row.y_center),
            (
                float(up.y_center)
                if up is not None
                else None
            ),
        )

        dvy_dy = central_difference(
            (
                float(down.field_velocity_y)
                if down is not None
                else None
            ),
            float(row.field_velocity_y),
            (
                float(up.field_velocity_y)
                if up is not None
                else None
            ),
            (
                float(down.y_center)
                if down is not None
                else None
            ),
            float(row.y_center),
            (
                float(up.y_center)
                if up is not None
                else None
            ),
        )

        maximum = (
            config.maximum_absolute_derivative
        )

        dvx_dx = float(
            np.clip(
                dvx_dx,
                -maximum,
                maximum,
            )
        )

        dvy_dx = float(
            np.clip(
                dvy_dx,
                -maximum,
                maximum,
            )
        )

        dvx_dy = float(
            np.clip(
                dvx_dy,
                -maximum,
                maximum,
            )
        )

        dvy_dy = float(
            np.clip(
                dvy_dy,
                -maximum,
                maximum,
            )
        )

        divergence = (
            dvx_dx + dvy_dy
        )

        curl = (
            dvy_dx - dvx_dy
        )

        normal_strain = (
            dvx_dx - dvy_dy
        )

        shear_strain = (
            dvx_dy + dvy_dx
        )

        strain_magnitude = math.sqrt(
            normal_strain ** 2
            + shear_strain ** 2
        )

        derivative_energy = math.sqrt(
            divergence ** 2
            + curl ** 2
            + strain_magnitude ** 2
        )

        predictability = (
            1.0
            / (
                1.0
                + config.predictability_scale
                * derivative_energy
                + float(
                    row.field_curvature
                    if not pd.isna(
                        row.field_curvature
                    )
                    else 0.0
                )
            )
        )

        flow_class = classify_flow(
            divergence=divergence,
            curl=curl,
            strain=strain_magnitude,
        )

        rows.append({
            **row._asdict(),
            "field_dvx_dx":
                dvx_dx,
            "field_dvy_dx":
                dvy_dx,
            "field_dvx_dy":
                dvx_dy,
            "field_dvy_dy":
                dvy_dy,
            "field_divergence":
                float(divergence),
            "field_curl":
                float(curl),
            "field_normal_strain":
                float(normal_strain),
            "field_shear_strain":
                float(shear_strain),
            "field_strain_magnitude":
                float(strain_magnitude),
            "field_derivative_energy":
                float(derivative_energy),
            "field_predictability":
                float(predictability),
            "field_flow_class":
                flow_class,
        })

    return pd.DataFrame(rows)


def classify_flow(
    *,
    divergence: float,
    curl: float,
    strain: float,
) -> str:
    magnitudes = {
        "divergence":
            abs(divergence),
        "curl":
            abs(curl),
        "strain":
            abs(strain),
    }

    dominant = max(
        magnitudes,
        key=magnitudes.get,
    )

    maximum = magnitudes[
        dominant
    ]

    if maximum < 1e-9:
        return "QUIET"

    if dominant == "curl":
        return (
            "ROTATING_CCW"
            if curl > 0.0
            else "ROTATING_CW"
        )

    if dominant == "strain":
        return "SHEARING"

    return (
        "EXPANDING"
        if divergence > 0.0
        else "CONTRACTING"
    )


def attach_field_to_observations(
    assigned: pd.DataFrame,
    field_cells: pd.DataFrame,
) -> pd.DataFrame:
    field_columns = [
        column
        for column in field_cells.columns
        if column.startswith(
            "field_"
        )
        or column in {
            "x_center",
            "y_center",
            "observation_count",
        }
    ]

    keys = [
        "field_x_bin",
        "field_y_bin",
        "field_cell_id",
    ]

    available = list(
        dict.fromkeys(
            keys + field_columns
        )
    )

    return (
        assigned.merge(
            field_cells[
                available
            ],
            on=keys,
            how="left",
            validate="many_to_one",
            suffixes=(
                "",
                "_cell",
            ),
        )
        .sort_values(
            "timestamp",
            kind="stable",
        )
        .reset_index(drop=True)
    )


def attach_attractor_pressure(
    field_observations: pd.DataFrame,
    attractors: pd.DataFrame | None,
) -> pd.DataFrame:
    frame = field_observations.copy()

    if attractors is None or attractors.empty:
        frame[
            "field_attractor_pressure"
        ] = 0.0

        return frame

    pressure = (
        attractors.groupby(
            "timestamp",
            observed=True,
        )
        .agg(
            field_attractor_pressure=(
                "attractor_alignment_score",
                "sum",
            ),
            field_mean_closing_efficiency=(
                "attractor_closing_efficiency",
                "mean",
            ),
            field_min_attractor_distance=(
                "distance_to_attractor",
                "min",
            ),
            field_strong_approach_count=(
                "evolution_signal",
                lambda values: int(
                    (
                        values
                        == "STRONG_APPROACH"
                    ).sum()
                ),
            ),
        )
        .reset_index()
    )

    return frame.merge(
        pressure,
        on="timestamp",
        how="left",
        validate="one_to_one",
    ).fillna({
        "field_attractor_pressure":
            0.0,
        "field_mean_closing_efficiency":
            0.0,
        "field_min_attractor_distance":
            0.0,
        "field_strong_approach_count":
            0,
    })


def build_field_summary(
    observations: pd.DataFrame,
    cells: pd.DataFrame,
) -> dict[str, Any]:
    if observations.empty:
        return {
            "observation_count": 0,
            "cell_count": int(
                len(cells)
            ),
            "latest": [],
        }

    latest_timestamp = observations[
        "timestamp"
    ].max()

    latest = observations[
        observations[
            "timestamp"
        ].eq(
            latest_timestamp
        )
    ]

    return {
        "observation_count":
            int(len(observations)),
        "cell_count":
            int(len(cells)),
        "eligible_cell_count":
            int(
                cells[
                    "field_eligible"
                ].astype(bool).sum()
            ),
        "timestamp_min":
            observations[
                "timestamp"
            ].min().isoformat(),
        "timestamp_max":
            latest_timestamp.isoformat(),
        "flow_class_counts":
            cells[
                "field_flow_class"
            ].value_counts().to_dict(),
        "latest":
            latest.to_dict(
                orient="records"
            ),
    }


def write_field_outputs(
    *,
    cells: pd.DataFrame,
    observations: pd.DataFrame,
    config: MorphologyFieldConfig,
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
        "cells":
            directory
            / "morphology_field_cells.csv",
        "observations":
            directory
            / "morphology_field_observations.csv",
        "summary":
            directory
            / "morphology_field_summary.json",
    }

    cells.to_csv(
        outputs["cells"],
        index=False,
    )

    observations.to_csv(
        outputs["observations"],
        index=False,
    )

    summary = {
        "schema_version":
            "atlas.morphology_field_dynamics.v1",
        "config":
            asdict(config),
        **build_field_summary(
            observations,
            cells,
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


def run_morphology_field_dynamics(
    *,
    motion: pd.DataFrame,
    attractors: pd.DataFrame | None = None,
    config: MorphologyFieldConfig = (
        MorphologyFieldConfig()
    ),
) -> dict[str, pd.DataFrame]:
    assigned, _, _ = assign_field_cells(
        motion,
        config=config,
    )

    cells = build_field_cells(
        assigned,
        config=config,
    )

    field_cells = (
        calculate_field_derivatives(
            cells,
            config=config,
        )
    )

    observations = (
        attach_field_to_observations(
            assigned,
            field_cells,
        )
    )

    observations = attach_attractor_pressure(
        observations,
        attractors,
    )

    return {
        "assigned":
            assigned,
        "cells":
            field_cells,
        "observations":
            observations,
    }
