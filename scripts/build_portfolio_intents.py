"""Build broker-neutral paper order intents from portfolio targets."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from atlas.investment.execution import (
    AccountSnapshot,
    PositionSnapshot,
)
from atlas.investment.execution.portfolio_bridge import (
    RebalancePolicy,
    build_portfolio_intent_plan,
    load_portfolio_targets,
)


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Convert Atlas portfolio optimizer targets "
            "into broker-neutral paper order intents."
        )
    )

    parser.add_argument(
        "--portfolio-report",
        default=(
            "output/investment_portfolio_optimizer/"
            "portfolio_optimizer_report.json"
        ),
    )

    price_source = parser.add_mutually_exclusive_group(
        required=True
    )

    price_source.add_argument(
        "--prices-json",
        help=(
            "JSON object mapping assets to reference prices."
        ),
    )

    price_source.add_argument(
        "--prices-file",
        help=(
            "Path to a JSON file mapping assets "
            "to reference prices."
        ),
    )

    parser.add_argument(
        "--account-json",
        default="",
        help=(
            "Optional account snapshot JSON file."
        ),
    )

    parser.add_argument(
        "--cash",
        type=float,
        default=10_000.0,
    )

    parser.add_argument(
        "--strategy-id",
        default=(
            "atlas-portfolio-optimizer"
        ),
    )

    parser.add_argument(
        "--evidence-id",
        required=True,
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
        default=0.10,
    )

    return parser.parse_args()


def load_account(
    path_text: str,
    *,
    default_cash: float,
) -> AccountSnapshot:
    if not path_text:
        return AccountSnapshot(
            cash=default_cash
        )

    payload = json.loads(
        Path(
            path_text
        ).read_text(
            encoding="utf-8"
        )
    )

    positions = {}

    for asset, row in (
        payload.get(
            "positions",
            {}
        ).items()
    ):
        positions[
            str(asset).upper()
        ] = PositionSnapshot(
            asset=str(asset).upper(),
            quantity=float(
                row["quantity"]
            ),
            average_price=float(
                row["average_price"]
            ),
            mark_price=float(
                row["mark_price"]
            ),
        )

    return AccountSnapshot(
        cash=float(
            payload.get(
                "cash",
                default_cash,
            )
        ),
        positions=positions,
        realized_pnl=float(
            payload.get(
                "realized_pnl",
                0.0,
            )
        ),
        daily_pnl=float(
            payload.get(
                "daily_pnl",
                0.0,
            )
        ),
    )


def main() -> int:
    args = parse_args()

    if args.prices_file:
        raw_prices = json.loads(
            Path(
                args.prices_file
            ).read_text(
                encoding="utf-8"
            )
        )
    else:
        raw_prices = json.loads(
            args.prices_json
        )

    prices = {
        str(asset).upper(): float(
            price
        )
        for asset, price
        in raw_prices.items()
    }

    account = load_account(
        args.account_json,
        default_cash=args.cash,
    )

    targets = load_portfolio_targets(
        report_path=Path(
            args.portfolio_report
        ),
        prices=prices,
    )

    plan = build_portfolio_intent_plan(
        targets=targets,
        account=account,
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
    )

    print(
        "ATLAS PORTFOLIO INTENT PLAN READY"
    )

    print(
        "Plan ID:",
        plan["plan_id"],
    )

    print(
        "Targets:",
        plan["counts"][
            "targets"
        ],
    )

    print(
        "Generated intents:",
        plan["counts"][
            "generated_intents"
        ],
    )

    print(
        "Skipped:",
        plan["counts"][
            "skipped_lines"
        ],
    )

    print(
        "Turnover weight:",
        plan[
            "total_turnover_weight"
        ],
    )

    for intent in plan[
        "intents"
    ]:
        print(
            intent["asset"],
            intent["side"],
            intent["quantity"],
            "@",
            intent[
                "reference_price"
            ],
        )

    print(
        "Output:",
        plan["outputs"][
            "intent_plan_json"
        ],
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
