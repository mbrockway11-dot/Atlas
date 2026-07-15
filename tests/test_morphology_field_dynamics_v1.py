from __future__ import annotations

import numpy as np
import pandas as pd

from atlas.investment.morphology_intelligence.field_dynamics import (
    MorphologyFieldConfig,
    assign_field_cells,
    build_field_cells,
    calculate_field_derivatives,
    classify_flow,
    run_morphology_field_dynamics,
)


def _motion(
    periods: int = 400,
) -> pd.DataFrame:
    side = int(
        np.sqrt(periods)
    )

    rows = []

    timestamp = pd.Timestamp(
        "2025-01-01",
        tz="UTC",
    )

    for x_index in range(side):
        for y_index in range(side):
            x = (
                -1.0
                + 2.0
                * x_index
                / max(side - 1, 1)
            )

            y = (
                -1.0
                + 2.0
                * y_index
                / max(side - 1, 1)
            )

            rows.append({
                "timestamp": timestamp,
                "morphology_cluster_id": 0,
                "morphology_cluster": "MORPH-0",
                "morphology_pc_1": x,
                "morphology_pc_2": y,
                "morphology_velocity_1": x,
                "morphology_velocity_2": y,
                "morphology_speed":
                    float(
                        np.hypot(x, y)
                    ),
                "morphology_acceleration_magnitude":
                    0.0,
                "morphology_curvature":
                    0.0,
                "morphology_directional_stability":
                    1.0,
            })

            timestamp += pd.Timedelta(
                minutes=15
            )

    return pd.DataFrame(rows)


def _config() -> MorphologyFieldConfig:
    return MorphologyFieldConfig(
        grid_bins=8,
        minimum_cell_observations=1,
        smoothing_passes=0,
    )


def test_cells_are_assigned() -> None:
    assigned, _, _ = assign_field_cells(
        _motion(),
        config=_config(),
    )

    assert {
        "field_x_bin",
        "field_y_bin",
        "field_cell_id",
    }.issubset(
        assigned.columns
    )


def test_field_cells_are_aggregated() -> None:
    assigned, _, _ = assign_field_cells(
        _motion(),
        config=_config(),
    )

    cells = build_field_cells(
        assigned,
        config=_config(),
    )

    assert not cells.empty

    assert cells[
        "observation_count"
    ].ge(1).all()


def test_radial_field_has_positive_divergence() -> None:
    assigned, _, _ = assign_field_cells(
        _motion(),
        config=_config(),
    )

    cells = build_field_cells(
        assigned,
        config=_config(),
    )

    dynamics = calculate_field_derivatives(
        cells,
        config=_config(),
    )

    interior = dynamics[
        dynamics["field_x_bin"].between(
            1,
            6,
        )
        & dynamics["field_y_bin"].between(
            1,
            6,
        )
    ]

    assert (
        interior[
            "field_divergence"
        ].mean()
        > 0.0
    )


def test_flow_classification() -> None:
    assert classify_flow(
        divergence=2.0,
        curl=0.1,
        strain=0.2,
    ) == "EXPANDING"

    assert classify_flow(
        divergence=-2.0,
        curl=0.1,
        strain=0.2,
    ) == "CONTRACTING"

    assert classify_flow(
        divergence=0.1,
        curl=2.0,
        strain=0.2,
    ) == "ROTATING_CCW"


def test_predictability_is_bounded() -> None:
    result = run_morphology_field_dynamics(
        motion=_motion(),
        config=_config(),
    )

    values = result[
        "observations"
    ][
        "field_predictability"
    ]

    assert values.between(
        0.0,
        1.0,
    ).all()


def test_output_preserves_all_timestamps() -> None:
    motion = _motion()

    result = run_morphology_field_dynamics(
        motion=motion,
        config=_config(),
    )

    assert len(
        result["observations"]
    ) == len(motion)
