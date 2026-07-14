"""Build unsupervised Atlas morphology clusters."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.clustering import (
    MorphologyClusteringConfig,
    load_clustering_observations,
    run_morphology_clustering,
    write_clustering_outputs,
)


def parse_integers(
    value: str,
) -> tuple[int, ...]:
    return tuple(
        int(item.strip())
        for item in value.split(",")
        if item.strip()
    )


def parse_strings(
    value: str,
) -> tuple[str, ...]:
    return tuple(
        item.strip()
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
            "investment_morphology_clustering"
        ),
    )

    parser.add_argument(
        "--cluster-counts",
        default="6,8,12,16",
    )

    parser.add_argument(
        "--selected-clusters",
        type=int,
        default=12,
    )

    parser.add_argument(
        "--features",
        default=(
            "entropy,"
            "transition_velocity,"
            "multi_timeframe_agreement,"
            "concentration,"
            "dispersion,"
            "persistence_bars,"
            "sol_fulcrum_score"
        ),
    )

    parser.add_argument(
        "--pca-components",
        type=int,
        default=5,
    )

    parser.add_argument(
        "--fit-sample-size",
        type=int,
        default=100000,
    )

    parser.add_argument(
        "--maximum-iterations",
        type=int,
        default=100,
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=33,
    )

    args = parser.parse_args()

    config = MorphologyClusteringConfig(
        cluster_counts=parse_integers(
            args.cluster_counts
        ),
        selected_cluster_count=(
            args.selected_clusters
        ),
        feature_columns=parse_strings(
            args.features
        ),
        pca_components=(
            args.pca_components
        ),
        fit_sample_size=(
            args.fit_sample_size
        ),
        maximum_iterations=(
            args.maximum_iterations
        ),
        random_seed=args.random_seed,
    )

    observations = (
        load_clustering_observations(
            args.observations,
            config=config,
        )
    )

    result = run_morphology_clustering(
        observations,
        config=config,
    )

    paths = write_clustering_outputs(
        assignments=result[
            "assignments"
        ],
        profiles=result[
            "profiles"
        ],
        transitions=result[
            "transitions"
        ],
        diagnostics=result[
            "diagnostics"
        ],
        standardizer=result[
            "standardizer"
        ],
        pca_model=result[
            "pca_model"
        ],
        kmeans_model=result[
            "kmeans_model"
        ],
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY CLUSTERING V1 ==="
    )

    print(
        f"observations={len(observations)}"
    )

    print(
        "fit_observations="
        f"{len(result['fit_frame'])}"
    )

    print(
        "selected_clusters="
        f"{result['kmeans_model'].cluster_count}"
    )

    print(
        "iterations="
        f"{result['kmeans_model'].iterations}"
    )

    print(
        "converged="
        f"{result['kmeans_model'].converged}"
    )

    print(
        "inertia="
        f"{result['kmeans_model'].inertia}"
    )

    print(
        "explained_variance="
        f"{sum(result['pca_model'].explained_variance_ratio)}"
    )

    for name, path in paths.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
