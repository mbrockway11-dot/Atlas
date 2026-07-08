
"""Sigil V32 adapter report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.adapters.sigil_v32.loader import (
    DEFAULT_SIGIL_ROOT,
    load_combined_decision,
    load_engine_states,
    load_signal_snapshot,
)
from atlas.investment.adapters.sigil_v32.translator import translate_engine_states


OUT_DIR = Path("output/investment_adapters/sigil_v32")
SIGNALS_CSV = OUT_DIR / "sigil_v32_strategy_signals.csv"
REPORT_JSON = OUT_DIR / "sigil_v32_adapter_report.json"
REPORT_MD = OUT_DIR / "sigil_v32_adapter_report.md"


def build_sigil_v32_adapter_report(root: str | Path = DEFAULT_SIGIL_ROOT) -> dict[str, Any]:
    root = Path(root)

    engine_states = load_engine_states(root)
    combined_decision = load_combined_decision(root)
    snapshot = load_signal_snapshot(root)

    signals = translate_engine_states(engine_states)
    signal_rows = [s.to_dict() for s in signals]

    report = {
        "success": True,
        "sigil_root": str(root),
        "engine_state_rows": int(len(engine_states)),
        "combined_decision_rows": int(len(combined_decision)),
        "snapshot_rows": int(len(snapshot)),
        "strategy_signal_count": int(len(signal_rows)),
        "signals": signal_rows,
        "summary": (
            f"Sigil V32 adapter translated {len(signal_rows)} engine state row(s) "
            f"from {root}."
        ),
        "outputs": {
            "signals_csv": str(SIGNALS_CSV),
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
        },
    }

    write_outputs(report, signal_rows)
    return report


def write_outputs(report: dict[str, Any], signal_rows: list[dict[str, Any]]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(signal_rows).to_csv(SIGNALS_CSV, index=False)
    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Sigil V32 Adapter Report",
        "",
        report.get("summary", ""),
        "",
        f"- Engine state rows: `{report.get('engine_state_rows')}`",
        f"- Combined decision rows: `{report.get('combined_decision_rows')}`",
        f"- Snapshot rows: `{report.get('snapshot_rows')}`",
        f"- Strategy signals: `{report.get('strategy_signal_count')}`",
        "",
        "## Signals",
        "",
    ]

    for row in report.get("signals", []):
        lines.append(
            f"- `{row.get('engine')}` asset=`{row.get('asset')}` "
            f"action=`{row.get('action')}` direction=`{row.get('direction')}` "
            f"exposure=`{row.get('target_exposure')}`"
        )

    return "\n".join(lines) + "\n"
