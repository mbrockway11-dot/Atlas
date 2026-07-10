
"""Market Universe v1 report and exports."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.market_universe.config import (
    enabled_assets,
    load_market_universe_config,
)
from atlas.investment.market_universe.fetcher import (
    CANONICAL_COLUMNS,
    fetch_market_history,
)
from atlas.investment.market_universe.liquidity import (
    evaluate_market_universe,
)


OUT_DIR = Path("output/investment_market_universe")
REPORT_JSON = OUT_DIR / "market_universe_report.json"
REPORT_MD = OUT_DIR / "market_universe_report.md"
PRICES_CSV = OUT_DIR / "market_universe_prices.csv"
STATUS_CSV = OUT_DIR / "market_universe_status.csv"
APPROVED_CSV = OUT_DIR / "approved_universe.csv"
REJECTED_CSV = OUT_DIR / "rejected_universe.csv"


def build_market_universe_report() -> dict[str, Any]:
    config = load_market_universe_config()
    assets = enabled_assets(config)

    prices, fetch_errors = fetch_market_history(
        assets,
        period=str(config.get("period", "2y")),
        interval=str(config.get("interval", "1d")),
    )

    status_rows = evaluate_market_universe(
        prices,
        config,
        fetch_errors,
    )

    approved_rows = [
        row for row in status_rows
        if row.get("approved") is True
    ]
    rejected_rows = [
        row for row in status_rows
        if row.get("approved") is not True
    ]
    failed_required = [
        row for row in status_rows
        if row.get("required_core") is True
        and row.get("approved") is not True
    ]

    approved_assets = [
        str(row["asset"])
        for row in approved_rows
    ]

    approved_prices = (
        prices[
            prices["asset"].astype(str).isin(
                approved_assets
            )
        ].copy()
        if not prices.empty
        else pd.DataFrame(columns=CANONICAL_COLUMNS)
    )

    success = len(failed_required) == 0

    summary = (
        f"Market Universe v1 evaluated {len(status_rows)} "
        f"whitelisted asset(s), approved {len(approved_rows)}, "
        f"rejected {len(rejected_rows)}, and found "
        f"{len(failed_required)} failed required core asset(s)."
    )

    report = {
        "success": success,
        "version": "market_universe_v1",
        "generated_at": datetime.now(UTC).isoformat(),
        "summary": summary,
        "text_summary": summary,
        "provider": config.get("provider"),
        "period": config.get("period"),
        "interval": config.get("interval"),
        "configured_assets": assets,
        "approved_assets": approved_assets,
        "rejected_assets": [
            str(row["asset"])
            for row in rejected_rows
        ],
        "required_core_assets": config.get(
            "required_core_assets",
            [],
        ),
        "failed_required_core_assets": [
            str(row["asset"])
            for row in failed_required
        ],
        "counts": {
            "configured": len(status_rows),
            "approved": len(approved_rows),
            "rejected": len(rejected_rows),
            "required_core_failed": len(failed_required),
            "price_rows": len(approved_prices),
        },
        "liquidity_gates": config.get(
            "liquidity_gates",
            {},
        ),
        "status_rows": status_rows,
        "fetch_errors": fetch_errors,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "prices_csv": str(PRICES_CSV),
            "status_csv": str(STATUS_CSV),
            "approved_csv": str(APPROVED_CSV),
            "rejected_csv": str(REJECTED_CSV),
        },
    }

    write_outputs(
        report,
        approved_prices,
        approved_rows,
        rejected_rows,
    )
    return report


def write_outputs(
    report: dict[str, Any],
    approved_prices: pd.DataFrame,
    approved_rows: list[dict],
    rejected_rows: list[dict],
) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if approved_prices is None or approved_prices.empty:
        price_frame = pd.DataFrame(
            columns=CANONICAL_COLUMNS
        )
    else:
        price_frame = approved_prices

    price_frame.to_csv(PRICES_CSV, index=False)

    status_rows = report.get("status_rows", [])
    status_frame = pd.DataFrame(status_rows)

    if "failure_reasons" in status_frame.columns:
        status_frame["failure_reasons"] = (
            status_frame["failure_reasons"].apply(
                lambda value: "|".join(value)
                if isinstance(value, list)
                else str(value or "")
            )
        )

    status_frame.to_csv(STATUS_CSV, index=False)
    pd.DataFrame(approved_rows).to_csv(
        APPROVED_CSV,
        index=False,
    )
    pd.DataFrame(rejected_rows).to_csv(
        REJECTED_CSV,
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


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Market Universe v1",
        "",
        report.get("summary", ""),
        "",
        "## Approved Assets",
        "",
    ]

    approved = report.get("approved_assets", [])

    if approved:
        for asset in approved:
            lines.append(f"- `{asset}`")
    else:
        lines.append("No assets passed the liquidity gates.")

    lines.extend([
        "",
        "## Rejected Assets",
        "",
    ])

    rejected = [
        row for row in report.get("status_rows", [])
        if row.get("approved") is not True
    ]

    if rejected:
        for row in rejected:
            reasons = ", ".join(
                row.get("failure_reasons", [])
            )
            lines.append(
                f"- `{row.get('asset')}` ? {reasons}"
            )
    else:
        lines.append("No assets were rejected.")

    lines.extend([
        "",
        "## Liquidity Gates",
        "",
        "```json",
        json.dumps(
            report.get("liquidity_gates", {}),
            indent=2,
        ),
        "```",
    ])

    return "\n".join(lines) + "\n"
