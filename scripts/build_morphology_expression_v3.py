"""Run Atlas Morphology Expression Engine V3."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.expression_v3 import (
    MorphologyExpressionConfig,
    build_expression_catalog,
    evaluate_expression_catalog,
    fuse_expression_inputs,
    load_expression_evolution,
    load_expression_scores,
    load_expression_trajectories,
    write_expression_outputs,
)
from atlas.investment.morphology_intelligence.field_incremental_value import (
    load_incremental_outcomes,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scores",
        required=True,
    )

    parser.add_argument(
        "--evolution",
        required=True,
    )

    parser.add_argument(
        "--trajectories",
        required=True,
    )

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_expression_v3"
        ),
    )

    parser.add_argument(
        "--horizon-bars",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--transaction-cost-bps",
        type=float,
        default=8.0,
    )

    parser.add_argument(
        "--non-overlap-bars",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--discovery-fraction",
        type=float,
        default=0.60,
    )

    parser.add_argument(
        "--minimum-raw-candidate-rows",
        type=int,
        default=500,
    )

    parser.add_argument(
        "--minimum-condition-observations",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--minimum-control-observations",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--minimum-cluster-observations",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--minimum-discovery-folds",
        type=int,
        default=6,
    )

    parser.add_argument(
        "--minimum-validation-folds",
        type=int,
        default=4,
    )

    parser.add_argument(
        "--maximum-pair-candidates",
        type=int,
        default=60,
    )

    parser.add_argument(
        "--maximum-triple-candidates",
        type=int,
        default=60,
    )

    args = parser.parse_args()

    config = MorphologyExpressionConfig(
        horizon_bars=args.horizon_bars,
        transaction_cost_bps=(
            args.transaction_cost_bps
        ),
        non_overlap_bars=(
            args.non_overlap_bars
        ),
        discovery_fraction=(
            args.discovery_fraction
        ),
        minimum_raw_candidate_rows=(
            args.minimum_raw_candidate_rows
        ),
        minimum_condition_observations=(
            args.minimum_condition_observations
        ),
        minimum_control_observations=(
            args.minimum_control_observations
        ),
        minimum_cluster_observations=(
            args.minimum_cluster_observations
        ),
        minimum_discovery_folds=(
            args.minimum_discovery_folds
        ),
        minimum_validation_folds=(
            args.minimum_validation_folds
        ),
        maximum_pair_candidates=(
            args.maximum_pair_candidates
        ),
        maximum_triple_candidates=(
            args.maximum_triple_candidates
        ),
    )

    scores = load_expression_scores(
        args.scores
    )

    evolution = load_expression_evolution(
        args.evolution
    )

    trajectories = (
        load_expression_trajectories(
            args.trajectories
        )
    )

    outcomes = load_incremental_outcomes(
        args.assignments,
        horizon_bars=(
            config.horizon_bars
        ),
    )

    fused = fuse_expression_inputs(
        scores=scores,
        evolution=evolution,
        trajectories=trajectories,
        outcomes=outcomes,
        config=config,
    )

    catalog = build_expression_catalog(
        fused,
        config=config,
    )

    (
        evaluations,
        summary,
        discovery_folds,
        validation_folds,
    ) = evaluate_expression_catalog(
        fused,
        catalog=catalog,
        config=config,
    )

    outputs = write_expression_outputs(
        fused=fused,
        catalog=catalog,
        evaluations=evaluations,
        summary=summary,
        discovery_folds=discovery_folds,
        validation_folds=validation_folds,
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY EXPRESSION ENGINE V3 ==="
    )

    print(
        f"fused_rows={len(fused)}"
    )

    print(
        f"catalog_candidates={len(catalog)}"
    )

    print(
        "single_candidates="
        f"{int(catalog['candidate_kind'].eq('single').sum()) if not catalog.empty else 0}"
    )

    print(
        "pair_candidates="
        f"{int(catalog['candidate_kind'].eq('pair').sum()) if not catalog.empty else 0}"
    )

    print(
        "triple_candidates="
        f"{int(catalog['candidate_kind'].eq('triple').sum()) if not catalog.empty else 0}"
    )

    print(
        f"evaluation_rows={len(evaluations)}"
    )

    print(
        "discovered="
        f"{int(summary['discovered'].astype(bool).sum()) if not summary.empty else 0}"
    )

    print(
        "validated="
        f"{int(summary['validated'].astype(bool).sum()) if not summary.empty else 0}"
    )

    if not summary.empty:
        for row in (
            summary.head(30)
            .itertuples(index=False)
        ):
            print(
                f"{row.asset} "
                f"{row.direction} "
                f"{row.expression}: "
                f"discovery={row.discovery_weighted_uplift:.6f} "
                f"validation={row.validation_weighted_uplift:.6f} "
                f"rate={row.validation_positive_uplift_rate:.3f} "
                f"p_adj={row.validation_bh_adjusted_p_value:.6f} "
                f"validated={row.validated}"
            )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
