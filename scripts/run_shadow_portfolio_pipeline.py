"""Run one complete market-data-driven Atlas shadow portfolio cycle."""

from __future__ import annotations

import argparse
from pathlib import Path

from atlas.investment.execution import (
    PaperBrokerConfig,
    RebalancePolicy,
    RiskLimits,
)
from atlas.investment.execution.shadow_pipeline import (
    run_shadow_pipeline,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run the Atlas market snapshot ? portfolio intents ? "
            "paper execution ? attribution pipeline."
        )
    )

    parser.add_argument(
        "--targets-file",
        required=True,
    )

    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
    )

    parser.add_argument(
        "--strategy-id",
        default=(
            "atlas-shadow-portfolio"
        ),
    )

    parser.add_argument(
        "--evidence-id",
        default="",
    )

    parser.add_argument(
        "--minimum-weight-delta",
        type=float,
        default=0.01,
    )

    parser.add_argument(
        "--minimum-order-notional",
        type=float,
        default=25.0,
    )

    parser.add_argument(
        "--maximum-order-notional",
        type=float,
        default=5_000.0,
    )

    parser.add_argument(
        "--maximum-total-turnover",
        type=float,
        default=0.25,
    )

    parser.add_argument(
        "--minimum-cash-weight",
        type=float,
        default=0.20,
    )

    parser.add_argument(
        "--maximum-asset-notional",
        type=float,
        default=10_000.0,
    )

    parser.add_argument(
        "--maximum-gross-exposure",
        type=float,
        default=20_000.0,
    )

    parser.add_argument(
        "--maximum-daily-loss",
        type=float,
        default=500.0,
    )

    parser.add_argument(
        "--maximum-leverage",
        type=float,
        default=1.0,
    )

    parser.add_argument(
        "--fee-bps",
        type=float,
        default=8.0,
    )

    parser.add_argument(
        "--slippage-bps",
        type=float,
        default=5.0,
    )

    parser.add_argument(
        "--maximum-intents",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--restart",
        action="store_true",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    report = run_shadow_pipeline(
        targets_path=Path(
            args.targets_file
        ),
        initial_cash=(
            args.initial_cash
        ),
        strategy_id=(
            args.strategy_id
        ),
        evidence_id=(
            args.evidence_id
        ),
        policy=RebalancePolicy(
            minimum_weight_delta=(
                args.minimum_weight_delta
            ),
            minimum_order_notional=(
                args.minimum_order_notional
            ),
            maximum_order_notional=(
                args.maximum_order_notional
            ),
            maximum_total_turnover=(
                args.maximum_total_turnover
            ),
            minimum_cash_weight=(
                args.minimum_cash_weight
            ),
        ),
        limits=RiskLimits(
            maximum_order_notional=(
                args.maximum_order_notional
            ),
            maximum_asset_notional=(
                args.maximum_asset_notional
            ),
            maximum_gross_exposure=(
                args.maximum_gross_exposure
            ),
            maximum_daily_loss=(
                args.maximum_daily_loss
            ),
            maximum_leverage=(
                args.maximum_leverage
            ),
        ),
        broker_config=(
            PaperBrokerConfig(
                fee_bps=args.fee_bps,
                slippage_bps=(
                    args.slippage_bps
                ),
            )
        ),
        maximum_intents=(
            args.maximum_intents
        ),
        resume=not args.restart,
    )

    print(
        "ATLAS SHADOW PORTFOLIO PIPELINE "
        + report["status"]
    )

    print(
        "Pipeline ID:",
        report["pipeline_id"],
    )

    print(
        "Snapshot ID:",
        report["snapshot_id"],
    )

    print(
        "Plan ID:",
        report["plan_id"],
    )

    print(
        "Cycle ID:",
        report["cycle_id"],
    )

    print(
        "Intent counts:",
        report[
            "intent_plan"
        ][
            "counts"
        ],
    )

    print(
        "Cycle counts:",
        report[
            "shadow_cycle"
        ][
            "counts"
        ],
    )

    print(
        "Performance:",
        report["performance"],
    )

    print(
        "Errors:",
        report["errors"],
    )

    return (
        0
        if report["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
