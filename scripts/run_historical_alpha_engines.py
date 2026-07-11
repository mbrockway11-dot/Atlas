"""Run historical Atlas Alpha Engine Framework analysis."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.engines import (
    registered_engines,
)
from atlas.investment.alpha.engines.backtest_adapter import (
    build_engine_trades,
    non_overlapping_engine_trades,
    summarize_engine_performance,
)
from atlas.investment.alpha.engines.historical import (
    load_historical_market_features,
    run_historical_engines,
)
from atlas.investment.alpha.engines.independence import (
    build_engine_correlation_matrix,
    build_engine_independence_summary,
)


OUT_DIR = Path(
    "output/investment_alpha_engines"
)

SIGNALS_CSV = (
    OUT_DIR
    / "historical_alpha_engine_signals.csv"
)

TRADES_CSV = (
    OUT_DIR
    / "historical_alpha_engine_trades.csv"
)

NON_OVERLAP_CSV = (
    OUT_DIR
    / "historical_alpha_engine_non_overlapping_trades.csv"
)

PERFORMANCE_CSV = (
    OUT_DIR
    / "historical_alpha_engine_performance.csv"
)

CORRELATION_CSV = (
    OUT_DIR
    / "historical_alpha_engine_correlation.csv"
)

INDEPENDENCE_CSV = (
    OUT_DIR
    / "historical_alpha_engine_independence.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "historical_alpha_engine_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "historical_alpha_engine_report.md"
)


def run_historical_alpha_engine_analysis(
) -> dict[str, Any]:
    """Run historical signal, trade, and independence analysis."""
    market = load_historical_market_features()

    if market.empty:
        report = {
            "success": False,
            "error": (
                "Historical Market Features v2 data "
                "was missing or empty."
            ),
        }

        write_report(
            report,
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )

        return report

    engines = registered_engines()

    signals = run_historical_engines(
        market,
        engines,
    )

    trades = build_engine_trades(
        signals,
        market,
    )

    non_overlap = (
        non_overlapping_engine_trades(
            trades
        )
    )

    raw_performance = (
        summarize_engine_performance(
            trades
        )
    )

    non_overlap_performance = (
        summarize_engine_performance(
            non_overlap
        )
    )

    correlation = (
        build_engine_correlation_matrix(
            signals
        )
    )

    independence = (
        build_engine_independence_summary(
            correlation
        )
    )

    report = {
        "success": True,
        "framework_version": "1.0.0",
        "market_rows": int(len(market)),
        "timestamps": int(
            market["timestamp"].nunique()
        ),
        "asset_count": int(
            market["asset"].nunique()
        ),
        "engine_count": len(engines),
        "signal_rows": int(len(signals)),
        "trade_rows": int(len(trades)),
        "non_overlapping_trade_rows": int(
            len(non_overlap)
        ),
        "raw_performance": (
            raw_performance.to_dict(
                orient="records"
            )
        ),
        "non_overlapping_performance": (
            non_overlap_performance.to_dict(
                orient="records"
            )
        ),
        "independence": (
            independence.to_dict(
                orient="records"
            )
        ),
        "summary": (
            "Historical Alpha Engine analysis processed "
            f"{len(market)} market row(s), generated "
            f"{len(signals)} signal row(s), and evaluated "
            f"{len(non_overlap)} non-overlapping trade(s)."
        ),
        "outputs": {
            "signals_csv": str(
                SIGNALS_CSV
            ),
            "trades_csv": str(
                TRADES_CSV
            ),
            "non_overlap_csv": str(
                NON_OVERLAP_CSV
            ),
            "performance_csv": str(
                PERFORMANCE_CSV
            ),
            "correlation_csv": str(
                CORRELATION_CSV
            ),
            "independence_csv": str(
                INDEPENDENCE_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_report(
        report,
        signals,
        trades,
        non_overlap,
        non_overlap_performance,
        correlation,
        independence,
    )

    return report


def write_report(
    report: dict[str, Any],
    signals: pd.DataFrame,
    trades: pd.DataFrame,
    non_overlap: pd.DataFrame,
    performance: pd.DataFrame,
    correlation: pd.DataFrame,
    independence: pd.DataFrame,
) -> None:
    """Write historical engine artifacts."""
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    signals.to_csv(
        SIGNALS_CSV,
        index=False,
    )

    trades.to_csv(
        TRADES_CSV,
        index=False,
    )

    non_overlap.to_csv(
        NON_OVERLAP_CSV,
        index=False,
    )

    performance.to_csv(
        PERFORMANCE_CSV,
        index=False,
    )

    correlation.to_csv(
        CORRELATION_CSV,
        index=True,
    )

    independence.to_csv(
        INDEPENDENCE_CSV,
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


def build_markdown(
    report: dict[str, Any],
) -> str:
    """Render historical alpha-engine analysis."""
    lines = [
        "# Historical Alpha Engine Analysis",
        "",
        report.get(
            "summary",
            report.get("error", ""),
        ),
        "",
        "## Coverage",
        "",
        f"- Success: `{report.get('success')}`",
        f"- Market rows: `{report.get('market_rows', 0)}`",
        f"- Timestamps: `{report.get('timestamps', 0)}`",
        f"- Assets: `{report.get('asset_count', 0)}`",
        f"- Engines: `{report.get('engine_count', 0)}`",
        f"- Signal rows: `{report.get('signal_rows', 0)}`",
        f"- Raw trades: `{report.get('trade_rows', 0)}`",
        (
            "- Non-overlapping trades: "
            f"`{report.get('non_overlapping_trade_rows', 0)}`"
        ),
        "",
        "## Non-Overlapping Performance",
        "",
    ]

    for row in report.get(
        "non_overlapping_performance",
        [],
    ):
        lines.extend([
            f"### {row.get('engine_id')}",
            "",
            f"- Family: `{row.get('family')}`",
            f"- Trades: `{row.get('trade_count')}`",
            f"- Assets: `{row.get('asset_count')}`",
            f"- Win rate: `{row.get('win_rate')}`",
            f"- Mean return: `{row.get('mean_return')}`",
            f"- Median return: `{row.get('median_return')}`",
            f"- Profit factor: `{row.get('profit_factor')}`",
            (
                "- Cumulative return: "
                f"`{row.get('cumulative_return')}`"
            ),
            f"- Best trade: `{row.get('best_trade')}`",
            f"- Worst trade: `{row.get('worst_trade')}`",
            "",
        ])

    lines.extend([
        "## Engine Independence",
        "",
    ])

    for row in report.get(
        "independence",
        [],
    ):
        lines.append(
            "- "
            f"`{row.get('engine_a')}` vs "
            f"`{row.get('engine_b')}`: "
            f"correlation `{row.get('correlation')}`, "
            f"independence `{row.get('independence_score')}`"
        )

    lines.append("")

    return "\n".join(lines)


def main() -> None:
    report = (
        run_historical_alpha_engine_analysis()
    )

    print(report["success"])

    print(
        report.get(
            "summary",
            report.get("error"),
        )
    )

    print("Non-overlapping performance:")

    for row in report.get(
        "non_overlapping_performance",
        [],
    ):
        print(row)

    print("Independence:")

    for row in report.get(
        "independence",
        [],
    ):
        print(row)

    print("Outputs:")

    for name, path in (
        report.get("outputs", {}) or {}
    ).items():
        print(f"- {name}: {path}")


if __name__ == "__main__":
    main()
