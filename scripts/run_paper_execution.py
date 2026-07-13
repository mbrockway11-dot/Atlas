"""Run one safe broker-neutral Atlas paper execution."""

from __future__ import annotations

import argparse
import json

from atlas.investment.execution import (
    AccountSnapshot,
    OrderIntent,
    PaperBrokerConfig,
    RiskLimits,
    run_paper_execution,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Run one Atlas paper order through "
            "pre-trade risk and the deterministic paper broker."
        )
    )

    parser.add_argument(
        "--asset",
        required=True,
    )
    parser.add_argument(
        "--side",
        required=True,
        choices=[
            "BUY",
            "SELL",
        ],
    )
    parser.add_argument(
        "--quantity",
        required=True,
        type=float,
    )
    parser.add_argument(
        "--price",
        required=True,
        type=float,
    )
    parser.add_argument(
        "--strategy-id",
        required=True,
    )
    parser.add_argument(
        "--evidence-id",
        required=True,
    )
    parser.add_argument(
        "--cash",
        type=float,
        default=10_000.0,
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
        "--max-order-notional",
        type=float,
        default=5_000.0,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    intent = OrderIntent(
        asset=args.asset,
        side=args.side,
        quantity=args.quantity,
        reference_price=args.price,
        strategy_id=(
            args.strategy_id
        ),
        evidence_id=(
            args.evidence_id
        ),
    )

    account = AccountSnapshot(
        cash=args.cash
    )

    limits = RiskLimits(
        maximum_order_notional=(
            args.max_order_notional
        )
    )

    broker_config = (
        PaperBrokerConfig(
            fee_bps=args.fee_bps,
            slippage_bps=(
                args.slippage_bps
            ),
        )
    )

    report = run_paper_execution(
        intent=intent,
        account=account,
        limits=limits,
        broker_config=(
            broker_config
        ),
    )

    print(
        "ATLAS PAPER EXECUTION "
        + (
            "SUCCEEDED"
            if report["success"]
            else "REJECTED"
        )
    )

    print(
        "Intent:",
        report["intent"][
            "intent_id"
        ],
    )

    print(
        "Risk:",
        report["risk"][
            "approved"
        ],
        report["risk"][
            "reason_codes"
        ],
    )

    print(
        "Order:",
        report["order"][
            "status"
        ],
        report["order"][
            "order_id"
        ],
    )

    print(
        "Account after:",
        json.dumps(
            report[
                "account_after"
            ],
            indent=2,
        ),
    )

    return (
        0
        if report["success"]
        else 1
    )


if __name__ == "__main__":
    raise SystemExit(main())
