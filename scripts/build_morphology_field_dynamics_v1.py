"""Build Atlas Morphology Field Dynamics Engine V1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.field_dynamics import (
    MorphologyFieldConfig,
    load_field_motion,
    load_nearest_attractors,
    run_morphology_field_dynamics,
    write_field_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--motion",
        required=True,
    )

    parser.add_argument(
        "--attractors",
        default="",
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_field"
        ),
    )

    parser.add_argument(
        "--grid-bins",
        type=int,
        default=40,
    )

    parser.add_argument(
        "--minimum-cell-observations",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--smoothing-passes",
        type=int,
        default=1,
    )

    args = parser.parse_args()

    config = MorphologyFieldConfig(
        grid_bins=args.grid_bins,
        minimum_cell_observations=(
            args.minimum_cell_observations
        ),
        smoothing_passes=(
            args.smoothing_passes
        ),
    )

    motion = load_field_motion(
        args.motion
    )

    attractors = (
        load_nearest_attractors(
            args.attractors
        )
        if args.attractors
        else None
    )

    result = (
        run_morphology_field_dynamics(
            motion=motion,
            attractors=attractors,
            config=config,
        )
    )

    outputs = write_field_outputs(
        cells=result["cells"],
        observations=result[
            "observations"
        ],
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY FIELD DYNAMICS V1 ==="
    )

    print(
        f"motion_rows={len(motion)}"
    )

    print(
        f"field_cells={len(result['cells'])}"
    )

    print(
        "eligible_cells="
        f"{int(result['cells']['field_eligible'].astype(bool).sum())}"
    )

    print(
        "field_observations="
        f"{len(result['observations'])}"
    )

    latest = result[
        "observations"
    ]

    if not latest.empty:
        latest = latest[
            latest["timestamp"].eq(
                latest["timestamp"].max()
            )
        ].iloc[0]

        print(
            "latest_flow_class="
            f"{latest['field_flow_class']}"
        )

        print(
            "latest_divergence="
            f"{latest['field_divergence']}"
        )

        print(
            "latest_curl="
            f"{latest['field_curl']}"
        )

        print(
            "latest_predictability="
            f"{latest['field_predictability']}"
        )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
