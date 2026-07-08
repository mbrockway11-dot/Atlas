
"""Alpha Ensemble report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.ensemble.loader import load_alpha_trades, load_promoted_strategies
from atlas.investment.alpha.ensemble.signal import build_ensemble_signals


OUT_DIR = Path("output/investment_alpha")
ENSEMBLE_JSON = OUT_DIR / "alpha_ensemble_report.json"
ENSEMBLE_MD = OUT_DIR / "alpha_ensemble_report.md"
ENSEMBLE_SIGNALS_CSV = OUT_DIR / "alpha_ensemble_signals.csv"
ENSEMBLE_WEIGHTS_CSV = OUT_DIR / "alpha_ensemble_weights.csv"


def build_alpha_ensemble_report() -> dict[str, Any]:
    """Build and export alpha ensemble report."""
    strategies = load_promoted_strategies()
    trades = load_alpha_trades()

    result = build_ensemble_signals(strategies, trades)

    signals: pd.DataFrame = result.pop("signals")
    votes: pd.DataFrame = result.pop("votes")
    weights = result.get("weights", {})

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not signals.empty:
        signals.to_csv(ENSEMBLE_SIGNALS_CSV, index=False)
    else:
        pd.DataFrame().to_csv(ENSEMBLE_SIGNALS_CSV, index=False)

    pd.DataFrame(weights.get("weights", [])).to_csv(ENSEMBLE_WEIGHTS_CSV, index=False)

    report = {
        "success": True,
        "summary": result.get("summary"),
        "promoted_strategy_count": len(strategies),
        "signal_count": int(len(signals)),
        "vote_count": int(len(votes)),
        "latest_signal": sanitize(result.get("latest_signal", {})),
        "weights": weights,
        "outputs": {
            "signals_csv": str(ENSEMBLE_SIGNALS_CSV),
            "weights_csv": str(ENSEMBLE_WEIGHTS_CSV),
            "json": str(ENSEMBLE_JSON),
            "markdown": str(ENSEMBLE_MD),
        },
    }

    ENSEMBLE_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    ENSEMBLE_MD.write_text(build_markdown(report), encoding="utf-8")

    return report


def sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: sanitize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitize(v) for v in value]
    try:
        if pd.isna(value):
            return None
    except Exception:
        pass
    return value


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Alpha Ensemble Report",
        "",
        report.get("summary", ""),
        "",
        "## Summary",
        "",
        f"- Promoted strategies: `{report.get('promoted_strategy_count')}`",
        f"- Signal rows: `{report.get('signal_count')}`",
        f"- Vote rows: `{report.get('vote_count')}`",
        "",
        "## Latest Signal",
        "",
        "```json",
        json.dumps(report.get("latest_signal", {}), indent=2, default=str),
        "```",
        "",
        "## Strategy Weights",
        "",
    ]

    for row in (report.get("weights", {}) or {}).get("weights", []):
        lines.append(
            f"- `{row.get('hypothesis_id')}` weight=`{round(row.get('weight', 0), 6)}` "
            f"confidence=`{row.get('alpha_confidence')}` trades=`{row.get('trade_count')}`"
        )

    lines.append("")
    return "\n".join(lines)
