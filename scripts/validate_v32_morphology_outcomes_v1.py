"""Validate V32-Morphology Ensemble historical outcomes."""

from __future__ import annotations

import argparse

from atlas.investment.morphology_intelligence.ensemble_outcomes import (
    EnsembleOutcomeConfig,
    load_outcome_ensemble,
    load_outcome_market,
    load_outcome_v32_stream,
    validate_ensemble_outcomes,
    write_outcome_outputs,
)


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--v32-decisions",
        required=True,
    )

    parser.add_argument(
        "--ensemble-decisions",
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
            "investment_v32_morphology_outcomes"
        ),
    )

    parser.add_argument(
        "--transaction-cost-bps",
        type=float,
        default=8.0,
    )

    parser.add_argument(
        "--baseline-exposure",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--maximum-price-age-bars",
        type=int,
        default=2,
    )

    parser.add_argument(
        "--bar-minutes",
        type=int,
        default=15,
    )

    args = parser.parse_args()

    config = EnsembleOutcomeConfig(
        transaction_cost_bps=(
            args.transaction_cost_bps
        ),
        baseline_exposure=(
            args.baseline_exposure
        ),
        maximum_price_age_bars=(
            args.maximum_price_age_bars
        ),
        bar_minutes=(
            args.bar_minutes
        ),
    )

    v32 = load_outcome_v32_stream(
        args.v32_decisions
    )

    ensemble = load_outcome_ensemble(
        args.ensemble_decisions
    )

    market = load_outcome_market(
        args.market
    )

    (
        trades,
        cohorts,
        yearly,
        equity,
        report,
    ) = validate_ensemble_outcomes(
        v32_stream=v32,
        ensemble=ensemble,
        market=market,
        config=config,
    )

    outputs = write_outcome_outputs(
        trades=trades,
        cohort_summary=cohorts,
        yearly_summary=yearly,
        equity_curves=equity,
        report=report,
        output_dir=args.output,
    )

    print(
        "=== V32-MORPHOLOGY OUTCOME VALIDATOR V1 ==="
    )

    print(
        f"paired_trades={len(trades)}"
    )

    print(
        "retained="
        f"{int(trades['entry_ready'].astype(bool).sum()) if not trades.empty else 0}"
    )

    print(
        "vetoed="
        f"{int(trades['morphology_veto'].astype(bool).sum()) if not trades.empty else 0}"
    )

    for row in cohorts.itertuples(
        index=False
    ):
        print(
            f"{row.cohort}: "
            f"trades={row.trade_count} "
            f"win_rate={row.win_rate:.4f} "
            f"mean={row.mean_return:.6f} "
            f"total={row.total_compounded_return:.6f} "
            f"pf={row.profit_factor:.4f} "
            f"max_dd={row.maximum_drawdown:.6f}"
        )

    print(
        "incremental_value_candidate="
        f"{report['morphology_incremental_value_candidate']}"
    )

    for name, path in outputs.items():
        print(f"{name}={path}")


if __name__ == "__main__":
    main()
