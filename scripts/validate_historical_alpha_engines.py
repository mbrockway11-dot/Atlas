"""Run segmented validation for historical Atlas alpha engines."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.engines.validation import (
    build_validation_segments,
    classify_engine_status,
)


INPUT_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_non_overlapping_trades.csv"
)

OUT_DIR = Path(
    "output/investment_alpha_engines"
)

VALIDATION_CSV = (
    OUT_DIR
    / "historical_alpha_engine_validation.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "historical_alpha_engine_validation.json"
)

REPORT_MD = (
    OUT_DIR
    / "historical_alpha_engine_validation.md"
)


def main() -> None:
    """Run segmented validation and write reports."""
    if (
        not INPUT_CSV.exists()
        or not INPUT_CSV.is_file()
        or INPUT_CSV.stat().st_size == 0
    ):
        raise FileNotFoundError(
            f"Missing historical trades: {INPUT_CSV}"
        )

    trades = pd.read_csv(
        INPUT_CSV
    )

    validation = build_validation_segments(
        trades,
        cost_bps=10.0,
    )

    statuses = classify_engine_status(
        validation
    )

    report = {
        "success": True,
        "cost_bps": 10.0,
        "input_trade_rows": int(
            len(trades)
        ),
        "validation_rows": int(
            len(validation)
        ),
        "engine_statuses": statuses,
        "summary": (
            "Historical Alpha Engine Validation "
            f"produced {len(validation)} segmented row(s)."
        ),
        "outputs": {
            "validation_csv": str(
                VALIDATION_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    validation.to_csv(
        VALIDATION_CSV,
        index=False,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )

    print(report["success"])
    print(report["summary"])

    for status in statuses:
        print(status)

    print("CSV:", VALIDATION_CSV)
    print("JSON:", REPORT_JSON)
    print("Markdown:", REPORT_MD)


def build_markdown(
    report: dict,
) -> str:
    """Render validation results."""
    lines = [
        "# Historical Alpha Engine Validation",
        "",
        report["summary"],
        "",
        f"- Transaction cost: `{report['cost_bps']} bps`",
        f"- Input trades: `{report['input_trade_rows']}`",
        f"- Validation rows: `{report['validation_rows']}`",
        "",
        "## Engine Status",
        "",
    ]

    for status in report.get(
        "engine_statuses",
        [],
    ):
        lines.extend([
            f"### {status['engine_id']}",
            "",
            f"- Status: `{status['status']}`",
            f"- Trades: `{status['trade_count']}`",
            (
                "- Mean net return: "
                f"`{status['mean_return']}`"
            ),
            (
                "- Profit factor: "
                f"`{status['profit_factor']}`"
            ),
            "",
        ])

    return "\n".join(lines)


if __name__ == "__main__":
    main()
