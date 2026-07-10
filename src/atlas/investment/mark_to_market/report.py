
"""Mark-to-Market v4 report and export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.mark_to_market.equity_curve import (
    append_equity_snapshot,
)
from atlas.investment.mark_to_market.loader import (
    load_mark_to_market_inputs,
)
from atlas.investment.mark_to_market.pricing import latest_prices
from atlas.investment.mark_to_market.valuation import (
    ledger_cash,
    ledger_equity,
    value_ledger_positions,
)


OUT_DIR = Path("output/investment_mark_to_market")
REPORT_JSON = OUT_DIR / "mark_to_market_report.json"
REPORT_MD = OUT_DIR / "mark_to_market_report.md"
POSITIONS_CSV = OUT_DIR / "positions.csv"
UNREALIZED_CSV = OUT_DIR / "unrealized_pnl.csv"
REALIZED_CSV = OUT_DIR / "realized_pnl.csv"
EQUITY_CURVE_CSV = OUT_DIR / "equity_curve.csv"


POSITION_COLUMNS = [
    "asset",
    "side",
    "quantity",
    "cost_basis",
    "weight",
    "current_price",
    "avg_entry_price",
    "market_value",
    "portfolio_weight",
    "unrealized_pnl",
    "unrealized_pnl_pct",
    "source",
]


def build_mark_to_market_report() -> dict[str, Any]:
    inputs = load_mark_to_market_inputs()

    ledger_report = inputs.get(
        "broker_ledger_report",
        {},
    ) or {}

    reconciliation = (
        ledger_report.get("reconciliation", {})
        or {}
    )

    if not ledger_report:
        return failure_report(
            "Broker Ledger v4.1 report is unavailable."
        )

    if reconciliation and not reconciliation.get(
        "balanced",
        False,
    ):
        return failure_report(
            "Broker Ledger v4.1 is not reconciled."
        )

    prices = latest_prices(inputs["price_data"])
    starting_equity = ledger_equity(ledger_report)
    cash = ledger_cash(ledger_report)

    positions = value_ledger_positions(
        inputs["broker_ledger_positions"],
        prices,
        starting_equity,
    )

    market_value = (
        float(
            pd.to_numeric(
                positions["market_value"],
                errors="coerce",
            ).fillna(0.0).sum()
        )
        if not positions.empty
        else 0.0
    )

    equity = cash + market_value

    initial_equity = float(
        reconciliation.get(
            "expected_equity",
            starting_equity,
        )
        or starting_equity
    )

    pnl = equity - initial_equity
    pnl_pct = (
        pnl / initial_equity
        if initial_equity
        else 0.0
    )

    equity_snapshot, equity_curve = (
        append_equity_snapshot(
            equity,
            cash,
            market_value,
            pnl,
            pnl_pct,
        )
    )

    report = {
        "success": True,
        "version": "mark_to_market_v4",
        "source": "broker_ledger_v4_1",
        "summary": (
            f"Mark-to-Market v4 valued "
            f"{len(positions)} Broker Ledger position(s). "
            f"Equity={round(equity, 2)}, "
            f"PnL={round(pnl, 2)}, "
            f"drawdown={equity_snapshot.get('drawdown')}."
        ),
        "text_summary": (
            f"Mark-to-Market v4 valued "
            f"{len(positions)} Broker Ledger position(s). "
            f"Equity={round(equity, 2)}, "
            f"PnL={round(pnl, 2)}, "
            f"drawdown={equity_snapshot.get('drawdown')}."
        ),
        "ledger_reconciliation": reconciliation,
        "equity_snapshot": equity_snapshot,
        "positions": (
            positions.to_dict("records")
            if not positions.empty
            else []
        ),
        "prices": prices,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "positions_csv": str(POSITIONS_CSV),
            "unrealized_csv": str(UNREALIZED_CSV),
            "realized_csv": str(REALIZED_CSV),
            "equity_curve_csv": str(EQUITY_CURVE_CSV),
        },
    }

    write_outputs(
        report,
        positions,
        equity_curve,
    )
    return report


def failure_report(reason: str) -> dict[str, Any]:
    report = {
        "success": False,
        "version": "mark_to_market_v4",
        "source": "broker_ledger_v4_1",
        "summary": f"Mark-to-Market v4 blocked: {reason}",
        "text_summary": (
            f"Mark-to-Market v4 blocked: {reason}"
        ),
        "reason": reason,
        "equity_snapshot": {},
        "positions": [],
        "prices": {},
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "positions_csv": str(POSITIONS_CSV),
            "unrealized_csv": str(UNREALIZED_CSV),
            "realized_csv": str(REALIZED_CSV),
            "equity_curve_csv": str(EQUITY_CURVE_CSV),
        },
    }

    write_outputs(
        report,
        pd.DataFrame(columns=POSITION_COLUMNS),
        read_existing_equity_curve(),
    )
    return report


def write_outputs(
    report: dict[str, Any],
    positions: pd.DataFrame,
    equity_curve: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if positions is None or positions.empty:
        position_frame = pd.DataFrame(
            columns=POSITION_COLUMNS
        )
    else:
        position_frame = positions

    position_frame.to_csv(
        POSITIONS_CSV,
        index=False,
    )
    position_frame.to_csv(
        UNREALIZED_CSV,
        index=False,
    )

    pd.DataFrame(
        columns=[
            "asset",
            "realized_pnl",
            "realized_pnl_pct",
            "source",
        ]
    ).to_csv(
        REALIZED_CSV,
        index=False,
    )

    if equity_curve is None:
        equity_curve = pd.DataFrame()

    equity_curve.to_csv(
        EQUITY_CURVE_CSV,
        index=False,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def read_existing_equity_curve() -> pd.DataFrame:
    if (
        not EQUITY_CURVE_CSV.exists()
        or EQUITY_CURVE_CSV.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(EQUITY_CURVE_CSV)
    except Exception:
        return pd.DataFrame()


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Mark-to-Market v4 Report",
        "",
        report.get("summary", ""),
        "",
        f"Source: `{report.get('source')}`",
        "",
        "## Broker Ledger Reconciliation",
        "",
        "```json",
        json.dumps(
            report.get(
                "ledger_reconciliation",
                {},
            ),
            indent=2,
        ),
        "```",
        "",
        "## Positions",
        "",
    ]

    positions = report.get("positions", [])

    if not positions:
        lines.append("No open positions.")
    else:
        for row in positions:
            lines.append(
                f"- `{row.get('asset')}` "
                f"value=`{round(float(row.get('market_value') or 0.0), 2)}` "
                f"unrealized=`{round(float(row.get('unrealized_pnl') or 0.0), 2)}`"
            )

    return "\n".join(lines) + "\n"
