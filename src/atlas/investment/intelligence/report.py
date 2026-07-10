
"""Investment Intelligence Layer v1 report and exports."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.intelligence.changes import (
    build_change_summary,
)
from atlas.investment.intelligence.confidence import (
    build_confidence_assessment,
)
from atlas.investment.intelligence.explanations import (
    build_asset_explanations,
    build_decision_chain,
    build_portfolio_explanation,
    build_trade_explanations,
)
from atlas.investment.intelligence.health import (
    build_health_checks,
    summarize_health,
)
from atlas.investment.intelligence.loader import (
    load_investment_intelligence_inputs,
)


OUT_DIR = Path("output/investment_intelligence")
REPORT_JSON = OUT_DIR / "investment_intelligence_report.json"
REPORT_MD = OUT_DIR / "investment_intelligence_report.md"
ASSETS_CSV = OUT_DIR / "asset_explanations.csv"
TRADES_CSV = OUT_DIR / "trade_explanations.csv"
HEALTH_CSV = OUT_DIR / "portfolio_health.csv"
CHAIN_CSV = OUT_DIR / "decision_chain.csv"
HISTORY_CSV = OUT_DIR / "intelligence_history.csv"


def build_investment_intelligence_report() -> dict[str, Any]:
    inputs = load_investment_intelligence_inputs()

    confidence = build_confidence_assessment(inputs)
    health_checks = build_health_checks(inputs)
    health_summary = summarize_health(health_checks)

    portfolio_explanation = build_portfolio_explanation(
        inputs,
        confidence,
    )

    asset_explanations = build_asset_explanations(inputs)
    trade_explanations = build_trade_explanations(inputs)
    decision_chain = build_decision_chain(inputs)

    changes = build_change_summary(
        inputs.get("prior_intelligence", {}) or {},
        confidence,
        portfolio_explanation,
        asset_explanations,
    )

    generated_at = datetime.now(UTC).isoformat()

    summary = (
        "Investment Intelligence v1 assessed portfolio confidence "
        f"as {confidence['confidence_label']} "
        f"({confidence['overall_confidence']:.3f}), "
        f"system health as {health_summary['health_label']}, "
        f"and explained {len(asset_explanations)} asset(s) and "
        f"{len(trade_explanations)} trade action(s)."
    )

    report = {
        "success": health_summary["failure_count"] == 0,
        "version": "investment_intelligence_v1",
        "generated_at": generated_at,
        "summary": summary,
        "text_summary": summary,
        "confidence": confidence,
        "health": health_summary,
        "health_checks": health_checks,
        "portfolio_explanation": portfolio_explanation,
        "asset_explanations": asset_explanations,
        "trade_explanations": trade_explanations,
        "decision_chain": decision_chain,
        "changes_since_prior": changes,
        "recommendations": build_recommendations(
            confidence,
            health_summary,
            portfolio_explanation,
        ),
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "assets_csv": str(ASSETS_CSV),
            "trades_csv": str(TRADES_CSV),
            "health_csv": str(HEALTH_CSV),
            "decision_chain_csv": str(CHAIN_CSV),
            "history_csv": str(HISTORY_CSV),
        },
    }

    write_outputs(report)
    return report


def build_recommendations(
    confidence: dict,
    health: dict,
    portfolio: dict,
) -> list[str]:
    recommendations = []

    if not health.get("healthy"):
        recommendations.append(
            "Pause execution until failed portfolio-system health "
            "checks are resolved."
        )

    if confidence.get("confidence_label") in {"LOW", "LIMITED"}:
        recommendations.append(
            "Maintain reduced exposure until confidence and "
            "broker-authoritative history improve."
        )

    if portfolio.get("learning_regime") == "insufficient_history":
        recommendations.append(
            "Continue paper observations before promoting strategy "
            "weights or enabling live capital."
        )

    if portfolio.get("drawdown", 0.0) <= -0.10:
        recommendations.append(
            "Preserve capital and investigate drawdown attribution."
        )

    if not recommendations:
        recommendations.append(
            "Maintain current controls and continue monitoring."
        )

    return recommendations


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(
        report.get("asset_explanations", [])
    ).to_csv(ASSETS_CSV, index=False)

    pd.DataFrame(
        report.get("trade_explanations", [])
    ).to_csv(TRADES_CSV, index=False)

    pd.DataFrame(
        report.get("health_checks", [])
    ).to_csv(HEALTH_CSV, index=False)

    pd.DataFrame(
        report.get("decision_chain", [])
    ).to_csv(CHAIN_CSV, index=False)

    append_history(report)

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


def append_history(report: dict[str, Any]) -> None:
    portfolio = report.get("portfolio_explanation", {}) or {}
    confidence = report.get("confidence", {}) or {}
    health = report.get("health", {}) or {}

    row = {
        "generated_at": report.get("generated_at"),
        "overall_confidence": confidence.get(
            "overall_confidence"
        ),
        "confidence_label": confidence.get(
            "confidence_label"
        ),
        "health_label": health.get("health_label"),
        "current_equity": portfolio.get("current_equity"),
        "pnl_pct": portfolio.get("pnl_pct"),
        "drawdown": portfolio.get("drawdown"),
        "risky_weight": portfolio.get("risky_weight"),
        "cash_weight": portfolio.get("cash_weight"),
        "learning_regime": portfolio.get(
            "learning_regime"
        ),
        "risk_label": portfolio.get("risk_label"),
        "rebalance_order_count": portfolio.get(
            "rebalance_order_count"
        ),
    }

    history = pd.DataFrame()

    if HISTORY_CSV.exists() and HISTORY_CSV.stat().st_size > 0:
        try:
            history = pd.read_csv(HISTORY_CSV)
        except Exception:
            history = pd.DataFrame()

    updated = pd.concat(
        [history, pd.DataFrame([row])],
        ignore_index=True,
    )

    updated.to_csv(HISTORY_CSV, index=False)


def build_markdown(report: dict[str, Any]) -> str:
    confidence = report.get("confidence", {}) or {}
    health = report.get("health", {}) or {}
    portfolio = report.get("portfolio_explanation", {}) or {}

    lines = [
        "# Atlas Investment Intelligence v1",
        "",
        report.get("summary", ""),
        "",
        "## Executive Assessment",
        "",
        f"- Overall confidence: `{confidence.get('overall_confidence')}`",
        f"- Confidence label: `{confidence.get('confidence_label')}`",
        f"- System health: `{health.get('health_label')}`",
        f"- Equity: `{portfolio.get('current_equity')}`",
        f"- Risky exposure: `{portfolio.get('risky_weight')}`",
        f"- Cash exposure: `{portfolio.get('cash_weight')}`",
        f"- Learning regime: `{portfolio.get('learning_regime')}`",
        f"- Risk label: `{portfolio.get('risk_label')}`",
        "",
        "## Portfolio Explanation",
        "",
        portfolio.get("explanation", ""),
        "",
        "## Recommendations",
        "",
    ]

    for row in report.get("recommendations", []):
        lines.append(f"- {row}")

    lines.extend([
        "",
        "## Health Checks",
        "",
    ])

    for row in report.get("health_checks", []):
        lines.append(
            f"- `{row.get('status')}` "
            f"**{row.get('name')}** ? "
            f"{row.get('message')}"
        )

    lines.extend([
        "",
        "## Asset Explanations",
        "",
    ])

    for row in report.get("asset_explanations", []):
        lines.append(
            f"### {row.get('asset')}"
        )
        lines.append("")
        lines.append(row.get("explanation", ""))
        lines.append("")
        lines.append(
            f"- Ensemble score: `{row.get('ensemble_score')}`"
        )
        lines.append(
            f"- Current weight: `{row.get('current_weight')}`"
        )
        lines.append(
            f"- Target weight: `{row.get('target_weight')}`"
        )
        lines.append(
            f"- Registry status: `{row.get('registry_status')}`"
        )
        lines.append("")

    lines.extend([
        "## Trade Explanations",
        "",
    ])

    trades = report.get("trade_explanations", [])

    if not trades:
        lines.append("No portfolio trades are currently required.")
    else:
        for row in trades:
            lines.append(
                f"- **{row.get('action')} "
                f"{row.get('asset')}** ? "
                f"{row.get('explanation')}"
            )

    lines.extend([
        "",
        "## Changes Since Prior Run",
        "",
    ])

    for change in (
        report.get("changes_since_prior", {}) or {}
    ).get("changes", []):
        lines.append(f"- {change}")

    return "\n".join(lines) + "\n"
