"""Run Field Incremental Value Validation V1.1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.field_incremental_value import (
    FieldIncrementalValueConfig,
    evaluate_incremental_value,
    load_incremental_outcomes,
    load_incremental_scores,
    summarize_incremental_value,
    write_incremental_value_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scores",
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
            "investment_morphology_field_incremental_value"
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
        "--minimum-condition-observations",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--minimum-control-observations",
        type=int,
        default=30,
    )

    parser.add_argument(
        "--minimum-cluster-observations",
        type=int,
        default=60,
    )

    parser.add_argument(
        "--minimum-valid-folds",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--bootstrap-iterations",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--permutation-iterations",
        type=int,
        default=1000,
    )

    parser.add_argument(
        "--random-seed",
        type=int,
        default=33,
    )

    args = parser.parse_args()

    config = FieldIncrementalValueConfig(
        horizon_bars=args.horizon_bars,
        transaction_cost_bps=(
            args.transaction_cost_bps
        ),
        non_overlap_bars=(
            args.non_overlap_bars
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
        minimum_valid_folds=(
            args.minimum_valid_folds
        ),
        bootstrap_iterations=(
            args.bootstrap_iterations
        ),
        permutation_iterations=(
            args.permutation_iterations
        ),
        random_seed=args.random_seed,
    )

    scores = load_incremental_scores(
        args.scores
    )

    outcomes = load_incremental_outcomes(
        args.assignments,
        horizon_bars=(
            config.horizon_bars
        ),
    )

    joined = outcomes.merge(
        scores,
        on=[
            "timestamp",
            "morphology_cluster_id",
        ],
        how="inner",
        validate="many_to_one",
        suffixes=(
            "",
            "_field",
        ),
    )

    evaluations, cluster_details = (
        evaluate_incremental_value(
            joined,
            config=config,
        )
    )

    summary = summarize_incremental_value(
        evaluations,
        config=config,
    )

    outputs = write_incremental_value_outputs(
        evaluations=evaluations,
        cluster_details=cluster_details,
        summary=summary,
        config=config,
        output_dir=args.output,
    )

    print(
        "=== FIELD INCREMENTAL VALUE V1.1 ==="
    )

    print(
        f"joined_rows={len(joined)}"
    )

    print(
        f"fold_rows={len(evaluations)}"
    )

    print(
        f"cluster_rows={len(cluster_details)}"
    )

    print(
        f"summary_rows={len(summary)}"
    )

    print(
        "incremental_candidates="
        f"{int(summary['incremental_value_candidate'].astype(bool).sum()) if not summary.empty else 0}"
    )

    if not summary.empty:
        for row in (
            summary.head(20)
            .itertuples(index=False)
        ):
            print(
                f"{row.asset} "
                f"{row.direction} "
                f"{row.condition_name}: "
                f"folds={row.valid_fold_count} "
                f"net={row.weighted_condition_net_return:.6f} "
                f"uplift={row.weighted_cluster_matched_uplift:.6f} "
                f"uplift_rate={row.positive_uplift_fold_rate:.3f} "
                f"p_adj={row.bh_adjusted_p_value:.6f} "
                f"candidate={row.incremental_value_candidate}"
            )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
