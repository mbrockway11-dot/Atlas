
"""Paper Broker v3 report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.paper_broker.fills import normalize_execution_fills
from atlas.investment.paper_broker.idempotency import filter_new_fills
from atlas.investment.paper_broker.ledger import (
    append_rows,
    build_cash_ledger_rows,
    build_trade_ledger_rows,
    current_cash,
    rebuild_positions,
)
from atlas.investment.paper_broker.loader import (
    load_cash_ledger,
    load_execution_fills,
    load_existing_fills,
    load_ledger,
)


OUT_DIR = Path("output/investment_paper_broker")
FILLS_CSV = OUT_DIR / "paper_broker_fills.csv"
LEDGER_CSV = OUT_DIR / "paper_broker_ledger.csv"
POSITIONS_CSV = OUT_DIR / "paper_broker_positions.csv"
CASH_LEDGER_CSV = OUT_DIR / "paper_broker_cash_ledger.csv"
REPORT_JSON = OUT_DIR / "paper_broker_report.json"
REPORT_MD = OUT_DIR / "paper_broker_report.md"


def build_paper_broker_report() -> dict[str, Any]:
    execution_fills = load_execution_fills()
    existing_fills = load_existing_fills()
    existing_ledger = load_ledger()
    existing_cash = load_cash_ledger()

    new_execution_fills = filter_new_fills(execution_fills, existing_fills)
    normalized_fills = normalize_execution_fills(new_execution_fills)

    all_fills = append_rows(existing_fills, normalized_fills)
    trade_rows = build_trade_ledger_rows(normalized_fills)
    cash_rows = build_cash_ledger_rows(normalized_fills)

    ledger = append_rows(existing_ledger, trade_rows)
    cash_ledger = append_rows(existing_cash, cash_rows)
    positions = rebuild_positions(all_fills)
    cash = current_cash(cash_ledger, positions)

    report = {
        "success": True,
        "version": "paper_broker_v3",
        "summary": (
            f"Paper Broker v3 consumed {len(execution_fills)} execution fill row(s), "
            f"created {len(normalized_fills)} new broker fill(s), "
            f"positions={len(positions)}, cash={cash}."
        ),
        "execution_fill_rows": int(len(execution_fills)),
        "new_fill_count": int(len(normalized_fills)),
        "ledger_rows": int(len(ledger)),
        "position_count": int(len(positions)),
        "cash": cash,
        "positions": positions.to_dict("records") if not positions.empty else [],
        "new_fills": normalized_fills,
        "outputs": {
            "fills_csv": str(FILLS_CSV),
            "ledger_csv": str(LEDGER_CSV),
            "positions_csv": str(POSITIONS_CSV),
            "cash_ledger_csv": str(CASH_LEDGER_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, all_fills, ledger, positions, cash_ledger)
    return report


def write_outputs(
    report: dict[str, Any],
    fills: pd.DataFrame,
    ledger: pd.DataFrame,
    positions: pd.DataFrame,
    cash_ledger: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fills.to_csv(FILLS_CSV, index=False)
    ledger.to_csv(LEDGER_CSV, index=False)
    positions.to_csv(POSITIONS_CSV, index=False)
    cash_ledger.to_csv(CASH_LEDGER_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Paper Broker v3 Report",
        "",
        report.get("summary", ""),
        "",
        "## Positions",
        "",
    ]

    for row in report.get("positions", []):
        lines.append(
            f"- `{row.get('asset')}` weight=`{row.get('net_weight')}` status=`{row.get('status')}`"
        )

    return "\n".join(lines) + "\n"
