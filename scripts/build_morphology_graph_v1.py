"""Build the Atlas Morphology Graph Engine."""

from __future__ import annotations

import argparse

import pandas as pd

from atlas.investment.morphology_intelligence.graph import (
    MorphologyGraphConfig,
    load_cluster_profiles,
    load_cluster_transitions,
    run_morphology_graph,
    write_graph_outputs,
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
        "--profiles",
        required=True,
    )

    parser.add_argument(
        "--transitions",
        required=True,
    )

    parser.add_argument(
        "--assignments",
        default="",
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_graph"
        ),
    )

    parser.add_argument(
        "--minimum-edge-probability",
        type=float,
        default=0.0,
    )

    parser.add_argument(
        "--minimum-transition-count",
        type=int,
        default=1,
    )

    parser.add_argument(
        "--forecast-depth",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--top-paths",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--outcome-horizons",
        default="1,2,4,8,16,32,96",
    )

    parser.add_argument(
        "--edge-outcome-horizon",
        type=int,
        default=16,
    )

    args = parser.parse_args()

    config = MorphologyGraphConfig(
        minimum_edge_probability=(
            args.minimum_edge_probability
        ),
        minimum_transition_count=(
            args.minimum_transition_count
        ),
        forecast_depth=(
            args.forecast_depth
        ),
        top_paths_per_source=(
            args.top_paths
        ),
        outcome_horizons=parse_integers(
            args.outcome_horizons
        ),
    )

    profiles = load_cluster_profiles(
        args.profiles
    )

    transitions = (
        load_cluster_transitions(
            args.transitions,
            config=config,
        )
    )

    assignments = (
        pd.read_csv(
            args.assignments,
            low_memory=False,
        )
        if args.assignments
        else None
    )

    result = run_morphology_graph(
        profiles=profiles,
        transitions=transitions,
        assignments=assignments,
        config=config,
        edge_outcome_horizon=(
            args.edge_outcome_horizon
        ),
    )

    paths = write_graph_outputs(
        nodes=result["nodes"],
        edges=result["edges"],
        asset_profiles=(
            result["asset_profiles"]
        ),
        forecasts=result["forecasts"],
        paths=result["paths"],
        edge_outcomes=(
            result["edge_outcomes"]
        ),
        metadata=result["metadata"],
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY GRAPH ENGINE V1 ==="
    )

    print(
        f"nodes={len(result['nodes'])}"
    )

    print(
        f"edges={len(result['edges'])}"
    )

    print(
        "asset_profiles="
        f"{len(result['asset_profiles'])}"
    )

    print(
        f"forecasts={len(result['forecasts'])}"
    )

    print(
        f"paths={len(result['paths'])}"
    )

    print(
        "edge_outcomes="
        f"{len(result['edge_outcomes'])}"
    )

    print(
        "pagerank_converged="
        f"{result['metadata']['pagerank_converged']}"
    )

    for name, path in paths.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
