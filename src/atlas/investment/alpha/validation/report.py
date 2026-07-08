
"""Alpha Validation Report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.validation.promotion import promote_alpha_strategies
from atlas.investment.alpha.validation.validator import validate_alpha_strategies


OUT_DIR = Path("output/investment_alpha")
TRADES_CSV = OUT_DIR / "alpha_backtest_trades.csv"
RANKINGS_CSV = OUT_DIR / "alpha_rankings.csv"

VALIDATION_JSON = OUT_DIR / "alpha_validation_report.json"
VALIDATION_MD = OUT_DIR / "alpha_validation_report.md"
PROMOTED_JSON = OUT_DIR / "promoted_alpha_strategies.json"
PROMOTED_CSV = OUT_DIR / "promoted_alpha_strategies.csv"
REJECTED_JSON = OUT_DIR / "rejected_alpha_strategies.json"


def build_alpha_validation_report(top_n: int = 25) -> dict[str, Any]:
    trades = pd.read_csv(TRADES_CSV) if TRADES_CSV.exists() else pd.DataFrame()
    rankings = pd.read_csv(RANKINGS_CSV) if RANKINGS_CSV.exists() else pd.DataFrame()

    validations = validate_alpha_strategies(trades, rankings, top_n=top_n)
    promotion = promote_alpha_strategies(validations)

    report = {
        "success": True,
        "top_n": top_n,
        "validated_count": len(validations),
        "validations": validations,
        "promotion": promotion,
        "summary": promotion.get("summary", ""),
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    VALIDATION_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    VALIDATION_MD.write_text(build_markdown(report), encoding="utf-8")

    promotion = report.get("promotion", {}) or {}
    PROMOTED_JSON.write_text(json.dumps(promotion.get("promoted", []), indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REJECTED_JSON.write_text(json.dumps(promotion.get("rejected", []), indent=2, ensure_ascii=False, default=str), encoding="utf-8")

    rows = []
    for item in promotion.get("promoted", []):
        conf = item.get("confidence", {})
        robust = item.get("validation", {}).get("robustness", {})
        metrics = item.get("metrics", {})
        rows.append({
            "hypothesis_id": item.get("hypothesis_id"),
            "alpha_confidence": conf.get("alpha_confidence"),
            "confidence_label": conf.get("confidence_label"),
            "trade_count": robust.get("trade_count"),
            "asset_concentration": robust.get("asset_concentration"),
            "alpha_score": metrics.get("alpha_score"),
            "non_overlap_avg_return": metrics.get("non_overlap_avg_return"),
            "non_overlap_profit_factor": metrics.get("non_overlap_profit_factor"),
        })

    pd.DataFrame(rows).to_csv(PROMOTED_CSV, index=False)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Validation Report v1",
        "",
        report.get("summary", ""),
        "",
        f"- Validated: `{report.get('validated_count')}`",
        f"- Promoted: `{report.get('promotion', {}).get('promoted_count', 0)}`",
        f"- Rejected: `{report.get('promotion', {}).get('rejected_count', 0)}`",
        "",
        "## Promoted Strategies",
        "",
    ]

    for item in report.get("promotion", {}).get("promoted", []):
        conf = item.get("confidence", {})
        robust = item.get("validation", {}).get("robustness", {})
        lines.extend([
            f"### {item.get('hypothesis_id')}",
            "",
            f"- Confidence: `{conf.get('alpha_confidence')}`",
            f"- Label: `{conf.get('confidence_label')}`",
            f"- Trades: `{robust.get('trade_count')}`",
            f"- Asset concentration: `{robust.get('asset_concentration')}`",
            f"- Components: `{conf.get('components')}`",
            "",
        ])

    lines.extend(["## Top Validated Strategies", ""])

    for item in report.get("validations", [])[:15]:
        conf = item.get("confidence", {})
        lines.extend([
            f"### {item.get('hypothesis_id')}",
            "",
            f"- Promoted: `{item.get('promoted')}`",
            f"- Confidence: `{conf.get('alpha_confidence')}`",
            f"- Label: `{conf.get('confidence_label')}`",
            f"- Components: `{conf.get('components')}`",
            "",
        ])

    return "\n".join(lines)
