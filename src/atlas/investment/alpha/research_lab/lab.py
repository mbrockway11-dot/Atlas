"""Atlas Alpha Research Lab v1 orchestration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.research_lab.metrics import (
    build_engine_metrics,
)
from atlas.investment.alpha.research_lab.promotion import (
    build_promotion_decisions,
)
from atlas.investment.alpha.research_lab.portfolio import (
    build_engine_portfolio_curves,
    summarize_portfolio_curves,
)
from atlas.investment.alpha.engines.historical import (
    load_historical_market_features,
)


OUT_DIR = Path(
    "output/investment_alpha_research_lab"
)

TRADES_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_non_overlapping_trades.csv"
)

INDEPENDENCE_CSV = Path(
    "output/investment_alpha_engines/"
    "historical_alpha_engine_independence.csv"
)

METRICS_CSV = (
    OUT_DIR
    / "alpha_research_engine_metrics.csv"
)

DECISIONS_CSV = (
    OUT_DIR
    / "alpha_research_promotion_decisions.csv"
)

PROMOTED_CSV = (
    OUT_DIR
    / "alpha_research_promoted_engines.csv"
)

CURVES_CSV = (
    OUT_DIR
    / "alpha_research_engine_curves.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "alpha_research_lab_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "alpha_research_lab_report.md"
)


def build_alpha_research_lab_report(
    *,
    transaction_cost_bps: float = 10.0,
    write_outputs: bool = True,
) -> dict[str, Any]:
    """Build the Alpha Research Lab report."""
    if (
        not TRADES_CSV.exists()
        or not TRADES_CSV.is_file()
        or TRADES_CSV.stat().st_size == 0
    ):
        report = {
            "success": False,
            "error": (
                "Missing historical non-overlapping "
                f"engine trades: {TRADES_CSV}"
            ),
        }

        if write_outputs:
            write_lab_outputs(
                report,
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
            )

        return report

    trades = pd.read_csv(
        TRADES_CSV
    )

    independence = safe_read_csv(
        INDEPENDENCE_CSV
    )

    metrics, legacy_curves = build_engine_metrics(
        trades,
        transaction_cost_bps=transaction_cost_bps,
    )

    market = load_historical_market_features()

    curves = build_engine_portfolio_curves(
        trades,
        market,
        transaction_cost_bps=transaction_cost_bps,
        gross_exposure=1.0,
    )

    portfolio_metrics = summarize_portfolio_curves(
        curves
    )

    if not portfolio_metrics.empty:
        metrics = metrics.merge(
            portfolio_metrics,
            on="engine_id",
            how="left",
        )

        metrics["max_drawdown"] = (
            metrics[
                "portfolio_max_drawdown"
            ].fillna(
                metrics["max_drawdown"]
            )
        )

        metrics["recovery_factor"] = (
            metrics[
                "portfolio_recovery_factor"
            ].fillna(
                metrics["recovery_factor"]
            )
        )

        metrics[
            "event_cumulative_return"
        ] = metrics[
            "portfolio_cumulative_return"
        ].fillna(
            metrics[
                "event_cumulative_return"
            ]
        )

    decisions = build_promotion_decisions(
        metrics,
        independence,
    )

    promoted = decisions[
        decisions["decision"].eq(
            "PROMOTE"
        )
    ].copy()

    decision_counts = {
        str(key): int(value)
        for key, value in decisions[
            "decision"
        ].value_counts().to_dict().items()
    }

    report = {
        "success": True,
        "lab_version": "1.0.0",
        "transaction_cost_bps": float(
            transaction_cost_bps
        ),
        "input_trade_rows": int(
            len(trades)
        ),
        "engine_count": int(
            metrics["engine_id"].nunique()
            if not metrics.empty
            else 0
        ),
        "decision_counts": decision_counts,
        "promoted_engine_count": int(
            len(promoted)
        ),
        "metrics": metrics.to_dict(
            orient="records"
        ),
        "decisions": decisions.to_dict(
            orient="records"
        ),
        "promoted_engines": promoted[
            [
                "engine_id",
                "family",
                "promotion_score",
                "profit_factor",
                "mean_return",
                "max_drawdown",
                "average_independence",
            ]
        ].to_dict(
            orient="records"
        )
        if not promoted.empty
        else [],
        "summary": (
            "Alpha Research Lab v1 evaluated "
            f"{len(metrics)} engine(s), promoted "
            f"{len(promoted)}, and produced "
            f"{len(decisions)} promotion decision(s)."
        ),
        "outputs": {
            "metrics_csv": str(
                METRICS_CSV
            ),
            "decisions_csv": str(
                DECISIONS_CSV
            ),
            "promoted_csv": str(
                PROMOTED_CSV
            ),
            "curves_csv": str(
                CURVES_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    if write_outputs:
        write_lab_outputs(
            report,
            metrics,
            decisions,
            promoted,
            curves,
        )

    return report


def write_lab_outputs(
    report: dict[str, Any],
    metrics: pd.DataFrame,
    decisions: pd.DataFrame,
    promoted: pd.DataFrame,
    curves: pd.DataFrame,
) -> None:
    """Write deterministic Research Lab artifacts."""
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics.to_csv(
        METRICS_CSV,
        index=False,
    )

    decisions.to_csv(
        DECISIONS_CSV,
        index=False,
    )

    promoted.to_csv(
        PROMOTED_CSV,
        index=False,
    )

    curves.to_csv(
        CURVES_CSV,
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
    """Render Alpha Research Lab results."""
    lines = [
        "# Alpha Research Lab v1",
        "",
        report.get(
            "summary",
            report.get("error", ""),
        ),
        "",
        "## Lab State",
        "",
        f"- Success: `{report.get('success')}`",
        f"- Version: `{report.get('lab_version')}`",
        (
            "- Transaction cost: "
            f"`{report.get('transaction_cost_bps')} bps`"
        ),
        (
            "- Input trade rows: "
            f"`{report.get('input_trade_rows', 0)}`"
        ),
        (
            "- Engines evaluated: "
            f"`{report.get('engine_count', 0)}`"
        ),
        (
            "- Promoted engines: "
            f"`{report.get('promoted_engine_count', 0)}`"
        ),
        (
            "- Decision counts: "
            f"`{report.get('decision_counts', {})}`"
        ),
        "",
        "## Promotion Decisions",
        "",
    ]

    for row in report.get(
        "decisions",
        [],
    ):
        lines.extend([
            f"### {row.get('engine_id')}",
            "",
            f"- Family: `{row.get('family')}`",
            f"- Decision: `{row.get('decision')}`",
            (
                "- Promotion score: "
                f"`{row.get('promotion_score')}`"
            ),
            (
                "- Performance score: "
                f"`{row.get('performance_score')}`"
            ),
            (
                "- Stability score: "
                f"`{row.get('stability_score')}`"
            ),
            (
                "- Risk score: "
                f"`{row.get('risk_score')}`"
            ),
            (
                "- Independence score: "
                f"`{row.get('independence_score')}`"
            ),
            f"- Trades: `{row.get('trade_count')}`",
            (
                "- Mean return: "
                f"`{row.get('mean_return')}`"
            ),
            (
                "- Profit factor: "
                f"`{row.get('profit_factor')}`"
            ),
            (
                "- Max drawdown: "
                f"`{row.get('max_drawdown')}`"
            ),
            (
                "- Hard failures: "
                f"`{row.get('hard_failures')}`"
            ),
            (
                "- Reason codes: "
                f"`{row.get('reason_codes')}`"
            ),
            "",
        ])

    lines.extend([
        "## Promoted Engine Set",
        "",
    ])

    promoted = report.get(
        "promoted_engines",
        [],
    )

    if not promoted:
        lines.append(
            "- No engines currently satisfy the promotion policy."
        )

    for row in promoted:
        lines.append(
            "- "
            f"`{row.get('engine_id')}` — "
            f"score `{row.get('promotion_score')}`, "
            f"profit factor `{row.get('profit_factor')}`, "
            f"mean return `{row.get('mean_return')}`"
        )

    lines.append("")

    return "\n".join(lines)


def safe_read_csv(
    path: Path,
) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        return pd.DataFrame()


__all__ = [
    "build_alpha_research_lab_report",
]


