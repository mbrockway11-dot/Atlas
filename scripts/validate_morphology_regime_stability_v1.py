"""Run Morphology Regime Stability Validation V1."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.regime_stability import (
    MorphologyRegimeStabilityConfig,
    build_expression_stability_matrix,
    build_past_only_regimes,
    load_expression_summary,
    load_regime_catalog,
    load_regime_features,
    load_regime_market,
    run_regime_stability_validation,
    summarize_regime_stability,
    write_regime_stability_outputs,
)
from atlas.investment.morphology_intelligence.field_incremental_value import (
    load_incremental_outcomes,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--features",
        required=True,
    )

    parser.add_argument(
        "--catalog",
        required=True,
    )

    parser.add_argument(
        "--expression-summary",
        required=True,
    )

    parser.add_argument(
        "--assignments",
        required=True,
    )

    parser.add_argument(
        "--market",
        required=True,
    )

    parser.add_argument(
        "--output",
        default=(
            "output/"
            "investment_morphology_regime_stability"
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
        "--trend-lookback-bars",
        type=int,
        default=384,
    )

    parser.add_argument(
        "--volatility-lookback-bars",
        type=int,
        default=96,
    )

    parser.add_argument(
        "--liquidity-lookback-bars",
        type=int,
        default=96,
    )

    parser.add_argument(
        "--minimum-condition-observations",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--minimum-control-observations",
        type=int,
        default=8,
    )

    parser.add_argument(
        "--minimum-cluster-observations",
        type=int,
        default=16,
    )

    parser.add_argument(
        "--minimum-regime-folds",
        type=int,
        default=4,
    )

    args = parser.parse_args()

    config = MorphologyRegimeStabilityConfig(
        horizon_bars=args.horizon_bars,
        transaction_cost_bps=(
            args.transaction_cost_bps
        ),
        non_overlap_bars=(
            args.non_overlap_bars
        ),
        trend_lookback_bars=(
            args.trend_lookback_bars
        ),
        volatility_lookback_bars=(
            args.volatility_lookback_bars
        ),
        liquidity_lookback_bars=(
            args.liquidity_lookback_bars
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
        minimum_regime_folds=(
            args.minimum_regime_folds
        ),
    )

    features = load_regime_features(
        args.features
    )

    catalog = load_regime_catalog(
        args.catalog
    )

    expression_summary = (
        load_expression_summary(
            args.expression_summary
        )
    )

    outcomes = load_incremental_outcomes(
        args.assignments,
        horizon_bars=(
            config.horizon_bars
        ),
    )

    market = load_regime_market(
        args.market
    )

    regimes = build_past_only_regimes(
        market,
        config=config,
    )

    evaluations = (
        run_regime_stability_validation(
            features=features,
            outcomes=outcomes,
            regimes=regimes,
            catalog=catalog,
            expression_summary=(
                expression_summary
            ),
            config=config,
        )
    )

    summary = summarize_regime_stability(
        evaluations,
        config=config,
    )

    matrix = build_expression_stability_matrix(
        summary
    )

    outputs = write_regime_stability_outputs(
        regimes=regimes,
        evaluations=evaluations,
        summary=summary,
        stability_matrix=matrix,
        config=config,
        output_dir=args.output,
    )

    print(
        "=== MORPHOLOGY REGIME STABILITY V1 ==="
    )

    print(
        f"regime_rows={len(regimes)}"
    )

    print(
        f"discovered_expressions={int(expression_summary['discovered'].astype(bool).sum()) if not expression_summary.empty else 0}"
    )

    print(
        f"evaluation_rows={len(evaluations)}"
    )

    print(
        f"summary_rows={len(summary)}"
    )

    print(
        "stable_regime_expressions="
        f"{int(summary['regime_stable'].astype(bool).sum()) if not summary.empty else 0}"
    )

    if not summary.empty:
        for row in (
            summary.head(30)
            .itertuples(index=False)
        ):
            print(
                f"{row.asset} "
                f"{row.direction} "
                f"{row.regime_dimension}="
                f"{row.regime_value} "
                f"{row.expression}: "
                f"folds={row.valid_fold_count} "
                f"net={row.weighted_condition_net_return:.6f} "
                f"uplift={row.weighted_cluster_matched_uplift:.6f} "
                f"rate={row.positive_uplift_fold_rate:.3f} "
                f"p_adj={row.bh_adjusted_p_value:.6f} "
                f"stable={row.regime_stable}"
            )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
