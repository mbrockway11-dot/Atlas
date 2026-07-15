"""Build realized morphology trajectory intelligence."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.trajectory import (
    MorphologyTrajectoryConfig,
    load_trajectory_assignments,
    run_morphology_trajectory_engine,
    write_trajectory_outputs,
)


def parse_integers(
    value: str,
) -> tuple[int, ...]:
    return tuple(
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_trajectory"
        ),
    )

    parser.add_argument(
        "--sequence-lengths",
        default="3,4,5,8",
    )

    parser.add_argument(
        "--outcome-horizons",
        default="4,8,16,32,96",
    )

    parser.add_argument(
        "--minimum-observations",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--confidence-target",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--stride",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--compress-repeated-states",
        action="store_true",
    )

    parser.add_argument(
        "--maximum-gap-multiple",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "--risk-penalty",
        type=float,
        default=0.50,
    )

    args = parser.parse_args()

    config = MorphologyTrajectoryConfig(
        sequence_lengths=parse_integers(
            args.sequence_lengths
        ),
        outcome_horizons=parse_integers(
            args.outcome_horizons
        ),
        minimum_observations=(
            args.minimum_observations
        ),
        confidence_target=(
            args.confidence_target
        ),
        stride=args.stride,
        compress_repeated_states=(
            args.compress_repeated_states
        ),
        maximum_gap_multiple=(
            args.maximum_gap_multiple
        ),
        risk_penalty=args.risk_penalty,
    )

    assignments = (
        load_trajectory_assignments(
            args.assignments,
            config=config,
        )
    )

    result = (
        run_morphology_trajectory_engine(
            assignments,
            config=config,
        )
    )

    outputs = write_trajectory_outputs(
        windows=result["windows"],
        observations=result[
            "observations"
        ],
        profiles=result["profiles"],
        transitions=result[
            "transitions"
        ],
        latest=result["latest"],
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY TRAJECTORY ENGINE V1 ==="
    )

    print(
        "morphology_timestamps="
        f"{len(result['morphology'])}"
    )

    print(
        f"windows={len(result['windows'])}"
    )

    print(
        "asset_observations="
        f"{len(result['observations'])}"
    )

    print(
        f"profiles={len(result['profiles'])}"
    )

    print(
        "positive_profiles="
        f"{int(result['profiles']['recommended_action'].eq('ENTER').sum())}"
    )

    print(
        "trajectory_transitions="
        f"{len(result['transitions'])}"
    )

    print(
        f"latest_rows={len(result['latest'])}"
    )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
