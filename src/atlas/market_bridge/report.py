
"""Market Bridge report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.market_bridge.decision import build_market_decision
from atlas.market_bridge.market_state import build_market_state
from atlas.market_bridge.sigil_reader import read_latest_signal


DEFAULT_OUTPUT = Path("output/market_bridge/market_decision_report.json")


def build_market_bridge_report(
    signal_path: str | Path | None = None,
    *,
    paper_only: bool = True,
    min_confidence: float = 0.70,
    output_path: str | Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    """Build full Market Bridge v1 report."""
    signal_payload = read_latest_signal(signal_path)
    market_state = build_market_state(signal_payload)
    decision = build_market_decision(
        market_state,
        paper_only=paper_only,
        min_confidence=min_confidence,
    )

    report = {
        "success": True,
        "bridge": "market_bridge_v1",
        "paper_only": paper_only,
        "signal_payload": signal_payload,
        "market_state": market_state,
        "decision": decision,
        "summary": decision.get("reason", ""),
    }

    report["export"] = export_market_bridge_report(report, output_path)
    return report


def export_market_bridge_report(
    report: dict[str, Any],
    output_path: str | Path = DEFAULT_OUTPUT,
) -> dict[str, Any]:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    return {
        "success": True,
        "path": str(path),
    }
