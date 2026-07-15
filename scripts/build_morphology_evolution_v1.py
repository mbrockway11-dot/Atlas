"""Build Atlas Morphology Evolution Engine V1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.evolution import (
    MorphologyEvolutionConfig,
    load_evolution_assignments,
    load_evolution_profiles,
    run_morphology_evolution,
    write_evolution_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--profiles",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_evolution"
        ),
    )

    parser.add_argument(
        "--derivative-lag",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--smoothing-window",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--attractor-horizon",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--minimum-attractor-observations",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--attractors-per-asset",
        type=int,
        default=3,
    )

    parser.add_argument(
        "--minimum-attractor-return",
        type=float,
        default=0.0,
    )

    args = parser.parse_args()

    config = MorphologyEvolutionConfig(
        derivative_lag=args.derivative_lag,
        smoothing_window=(
            args.smoothing_window
        ),
        attractor_horizon=(
            args.attractor_horizon
        ),
        minimum_attractor_observations=(
            args.minimum_attractor_observations
        ),
        attractors_per_asset=(
            args.attractors_per_asset
        ),
        minimum_attractor_return=(
            args.minimum_attractor_return
        ),
    )

    assignments = (
        load_evolution_assignments(
            args.assignments
        )
    )

    profiles = load_evolution_profiles(
        args.profiles
    )

    result = run_morphology_evolution(
        assignments=assignments,
        profiles=profiles,
        config=config,
    )

    outputs = write_evolution_outputs(
        motion=result["motion"],
        attractors=result["attractors"],
        attractor_observations=result[
            "attractor_observations"
        ],
        nearest_attractors=result[
            "nearest_attractors"
        ],
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY EVOLUTION ENGINE V1 ==="
    )

    print(
        f"motion_rows={len(result['motion'])}"
    )

    print(
        "attractors="
        f"{len(result['attractors'])}"
    )

    print(
        "attractor_observations="
        f"{len(result['attractor_observations'])}"
    )

    print(
        "nearest_attractor_rows="
        f"{len(result['nearest_attractors'])}"
    )

    latest = result[
        "nearest_attractors"
    ]

    if not latest.empty:
        latest = latest[
            latest["timestamp"].eq(
                latest["timestamp"].max()
            )
        ]

        for row in latest.itertuples(
            index=False
        ):
            print(
                f"{row.asset}: "
                f"cluster={row.morphology_cluster_id} "
                f"attractor={row.attractor_cluster_id} "
                f"distance={row.distance_to_attractor:.6f} "
                f"closing_velocity={row.attractor_closing_velocity:.6f} "
                f"eta={row.estimated_bars_to_attractor:.2f} "
                f"signal={row.evolution_signal}"
            )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
