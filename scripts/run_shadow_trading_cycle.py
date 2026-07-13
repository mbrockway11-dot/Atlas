"""Run one restart-safe Atlas paper shadow trading cycle."""

from __future__ import annotations

import argparse

from atlas.investment.execution import (
    PaperBrokerConfig,
    RiskLimits,
)
from atlas.investment.execution.shadow_loop import (
    run_shadow_cycle,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run one autonomous Atlas shadow-trading cycle "
            "through the paper execution plane."
        )
    )

    parser.add_argument(
        "--initial-cash",
        type=float,
        default=10_000.0,
    )

    parser.add_argument(
        "--maximum-intents",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--restart",
        action="store_true",
        help=(
            "Ignore an existing cycle checkpoint."
        ),
    )

    parser.add_argument(
        "--maximum-order-notional",
        type=float,
        default=5_000.0,
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

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    report = run_shadow_cycle(
        initial_cash=(
            args.initial_cash
        ),
        maximum_intents=(
            args.maximum_intents
        ),
        resume=not args.restart,
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
    )

    print(
        "ATLAS SHADOW CYCLE "
        + report["status"]
    )

    print(
        "Cycle ID:",
        report["cycle_id"],
    )

    print(
        "Plan ID:",
        report["plan_id"],
    )

    print(
        "Resumed:",
        report["resumed"],
    )

    print(
        "Counts:",
        report["counts"],
    )

    print(
        "Halt reason:",
        report["halt_reason"]
        or "(none)",
    )

    print(
        "Cash:",
        report["account_after"][
            "cash"
        ],
    )

    print(
        "Positions:",
        list(
            report["account_after"][
                "positions"
            ]
        ),
    )

    return (
        0
        if report["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
