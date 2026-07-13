"""End-to-end Atlas paper execution service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.investment.execution.contracts import (
    AccountSnapshot,
    OrderIntent,
    RiskLimits,
)
from atlas.investment.execution.ledger import (
    apply_fill,
)
from atlas.investment.execution.paper_broker import (
    PaperBroker,
    PaperBrokerConfig,
)
from atlas.investment.execution.risk import (
    evaluate_order_intent,
)


OUTPUT_DIR = Path(
    "output/investment_paper_execution"
)

LATEST_REPORT_JSON = (
    OUTPUT_DIR
    / "paper_execution_report.json"
)

EXECUTION_LEDGER_JSONL = (
    OUTPUT_DIR
    / "paper_execution_ledger.jsonl"
)


def run_paper_execution(
    *,
    intent: OrderIntent,
    account: AccountSnapshot,
    limits: RiskLimits | None = None,
    broker_config: (
        PaperBrokerConfig | None
    ) = None,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Run risk, paper order submission, fills, and ledger updates."""
    effective_limits = (
        limits
        or RiskLimits()
    )

    broker = PaperBroker(
        broker_config
    )

    risk = evaluate_order_intent(
        intent,
        account,
        effective_limits,
    )

    order, fills = broker.submit(
        intent,
        risk,
    )

    next_account = account

    for fill in fills:
        next_account = apply_fill(
            next_account,
            fill,
        )

    report = {
        "success": bool(
            risk.approved
            and order.status
            in {
                "FILLED",
                "PARTIALLY_FILLED",
            }
        ),
        "mode": "PAPER",
        "live_execution": False,
        "intent": intent.to_dict(),
        "risk": risk.to_dict(),
        "order": order.to_dict(),
        "fills": [
            fill.to_dict()
            for fill in fills
        ],
        "account_before": (
            account.to_dict()
        ),
        "account_after": (
            next_account.to_dict()
        ),
        "contract": {
            "broker_neutral": True,
            "paper_only": True,
            "live_credentials_used": False,
            "pre_trade_risk_required": True,
            "immutable_input_account": True,
        },
        "outputs": {
            "report_json": str(
                LATEST_REPORT_JSON
            ),
            "ledger_jsonl": str(
                EXECUTION_LEDGER_JSONL
            ),
        },
    }

    if write_outputs:
        write_execution_outputs(
            report
        )

    return report


def write_execution_outputs(
    report: dict[str, Any],
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    temporary = (
        LATEST_REPORT_JSON
        .with_suffix(
            ".json.tmp"
        )
    )

    temporary.write_text(
        json.dumps(
            report,
            indent=2,
            sort_keys=True,
            default=str,
        ),
        encoding="utf-8",
    )

    temporary.replace(
        LATEST_REPORT_JSON
    )

    with EXECUTION_LEDGER_JSONL.open(
        "a",
        encoding="utf-8",
        newline="\n",
    ) as handle:
        handle.write(
            json.dumps(
                {
                    "intent_id": (
                        report[
                            "intent"
                        ][
                            "intent_id"
                        ]
                    ),
                    "order_id": (
                        report[
                            "order"
                        ][
                            "order_id"
                        ]
                    ),
                    "status": (
                        report[
                            "order"
                        ][
                            "status"
                        ]
                    ),
                    "success": (
                        report[
                            "success"
                        ]
                    ),
                    "risk_approved": (
                        report[
                            "risk"
                        ][
                            "approved"
                        ]
                    ),
                    "reason_codes": (
                        report[
                            "risk"
                        ][
                            "reason_codes"
                        ]
                    ),
                },
                sort_keys=True,
            )
            + "\n"
        )
