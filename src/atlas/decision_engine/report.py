
"""Decision report builder."""

from __future__ import annotations

from typing import Any

from atlas.decision_engine.choice import DecisionChoice, choice_to_dict
from atlas.decision_engine.comparison import compare_decision_paths
from atlas.decision_engine.narrative import build_decision_narrative
from atlas.decision_engine.scoring import score_decision_path
from atlas.simulation import build_simulation_report


DECISION_REPORT_VERSION = "1.0"


def build_decision_report(
    systems_report: dict[str, Any],
    choices: list[DecisionChoice],
) -> dict[str, Any]:
    """Build decision report by simulating and comparing choices."""
    results = []

    for choice in choices:
        simulation = build_simulation_report(
            systems_report,
            scenario=choice.scenario,
            environment=choice.environment or None,
        )

        results.append(
            {
                "choice": choice_to_dict(choice),
                "simulation": simulation,
                "score": score_decision_path(simulation),
            }
        )

    comparison = compare_decision_paths(results)

    report = {
        "success": True,
        "version": DECISION_REPORT_VERSION,
        "profile_key": systems_report.get("profile_key"),
        "choice_count": len(choices),
        "results": results,
        "comparison": comparison,
    }

    report["narrative"] = build_decision_narrative(report)

    return report
