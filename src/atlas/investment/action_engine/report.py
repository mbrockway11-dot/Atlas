
"""Action Engine report/export."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.action_engine.exposure_action import exposure_vote
from atlas.investment.action_engine.learning_action import learning_vote
from atlas.investment.action_engine.loader import load_action_engine_inputs
from atlas.investment.action_engine.performance_action import performance_vote
from atlas.investment.action_engine.position_manager_action import position_manager_votes
from atlas.investment.action_engine.signal_action import decision_alignment_vote
from atlas.investment.action_engine.voting import aggregate_votes


OUT_DIR = Path("output/investment_action_engine")
REPORT_JSON = OUT_DIR / "action_engine_report.json"
REPORT_MD = OUT_DIR / "action_engine_report.md"
ACTIONS_CSV = OUT_DIR / "action_engine_actions.csv"
VOTES_CSV = OUT_DIR / "action_engine_votes.csv"


def build_action_engine_report() -> dict[str, Any]:
    inputs = load_action_engine_inputs()

    lifecycle = inputs["lifecycle"]
    decision = inputs["decision"]
    learning = inputs["learning"]
    performance = inputs["performance"]
    portfolio_state = inputs["portfolio_state"]
    position_manager = inputs["position_manager"]

    if lifecycle.empty:
        report = {
            "success": False,
            "summary": "No lifecycle positions found.",
            "actions": [],
            "votes": [],
        }
        write_outputs(report)
        return report

    open_positions = lifecycle[lifecycle["state"] == "OPEN"].copy()

    actions = []
    all_votes = []

    for _, row in open_positions.iterrows():
        position = row.to_dict()
        pid = position.get("position_id")

        votes = []
        votes.append(decision_alignment_vote(position, decision))
        votes.append(learning_vote(position, learning))
        votes.append(performance_vote(position, performance))
        votes.append(exposure_vote(position, portfolio_state))
        votes.extend(position_manager_votes(position, position_manager))

        result = aggregate_votes(pid, votes)

        action_row = {
            "position_id": pid,
            "asset": position.get("asset"),
            "side": position.get("side"),
            "state": position.get("state"),
            "final_action": result["final_action"],
            "final_confidence": result["final_confidence"],
            "scores": result["scores"],
        }

        actions.append(action_row)

        for v in votes:
            vote_row = dict(v)
            vote_row["position_id"] = pid
            vote_row["asset"] = position.get("asset")
            all_votes.append(vote_row)

    report = {
        "success": True,
        "summary": f"Action Engine evaluated {len(actions)} open position(s).",
        "actions": actions,
        "votes": all_votes,
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "actions_csv": str(ACTIONS_CSV),
            "votes_csv": str(VOTES_CSV),
        },
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    pd.DataFrame(report.get("actions", [])).to_csv(ACTIONS_CSV, index=False)
    pd.DataFrame(report.get("votes", [])).to_csv(VOTES_CSV, index=False)

    REPORT_JSON.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    REPORT_MD.write_text(build_markdown(report), encoding="utf-8")


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Action Engine Report",
        "",
        report.get("summary", ""),
        "",
        "## Actions",
        "",
    ]

    for row in report.get("actions", []):
        lines.append(
            f"- `{row.get('asset')}` action=`{row.get('final_action')}` "
            f"confidence=`{row.get('final_confidence')}`"
        )

    return "\n".join(lines) + "\n"
