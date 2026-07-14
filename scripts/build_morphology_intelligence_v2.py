"""Build Atlas Morphology Intelligence v2 surfaces."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence import (
    MorphologySurfaceConfig,
    build_entry_exit_surfaces,
    build_surface_matrix,
    load_morphology_observations,
    write_surface_outputs,
)


def parse_horizons(value: str) -> tuple[int, ...]:
    return tuple(
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--observations",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_intelligence"
        ),
    )

    parser.add_argument(
        "--horizons",
        default="1,2,4,8,16,32,96",
    )

    parser.add_argument(
        "--minimum-observations",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--risk-penalty",
        type=float,
        default=0.50,
    )

    parser.add_argument(
        "--confidence-target",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--quantile-bins",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    config = MorphologySurfaceConfig(
        horizons=parse_horizons(
            args.horizons
        ),
        minimum_observations=(
            args.minimum_observations
        ),
        risk_penalty=args.risk_penalty,
        confidence_target=(
            args.confidence_target
        ),
        quantile_bins=args.quantile_bins,
    )

    observations = (
        load_morphology_observations(
            args.observations,
            horizons=config.horizons,
        )
    )

    matrix = build_surface_matrix(
        observations,
        config=config,
    )

    surfaces = build_entry_exit_surfaces(
        matrix
    )

    paths = write_surface_outputs(
        surface_matrix=matrix,
        entry_exit_surfaces=surfaces,
        output_dir=args.output,
        config=config,
    )

    print(
        "=== MORPHOLOGY INTELLIGENCE V2 ==="
    )

    print(
        f"observations={len(observations)}"
    )

    print(
        f"surface_matrix_rows={len(matrix)}"
    )

    print(
        f"entry_exit_surfaces={len(surfaces)}"
    )

    print(
        "positive_entries="
        f"{int(surfaces['recommended_action'].eq('ENTER').sum())}"
    )

    for name, path in paths.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
