
"""Systems Engineering Report builder."""

from __future__ import annotations

from typing import Any

from atlas.systems_report.behavior import build_behavior_section
from atlas.systems_report.cognition import build_cognition_section
from atlas.systems_report.consensus import build_consensus_section
from atlas.systems_report.diagrams import build_diagrams_section
from atlas.systems_report.evidence_matrix import build_evidence_matrix
from atlas.systems_report.evolution import build_evolution_section
from atlas.synthesis.explainability import build_explainability_report
from atlas.systems_report.executive import build_executive_summary
from atlas.systems_report.population import build_population_section
from atlas.systems_report.reasoning import build_reasoning_section
from atlas.systems_report.symbolism import build_symbolism_section
from atlas.systems_report.tensions import build_tensions_section


SYSTEMS_ENGINEERING_REPORT_VERSION = "1.0"


def build_systems_engineering_report(payload: dict[str, Any]) -> dict[str, Any]:
    """Build full Systems Engineering Report from compiled profile payload."""
    return {
        "success": True,
        "version": SYSTEMS_ENGINEERING_REPORT_VERSION,
        "profile_key": payload.get("profile_key"),
        "executive": build_executive_summary(payload),
        "evidence_matrix": build_evidence_matrix(payload),
        "consensus": build_consensus_section(payload),
        "reasoning": build_reasoning_section(payload),
        "explainability": build_explainability_report(payload.get("synthesis", {})),
        "tensions": build_tensions_section(payload),
        "cognition": build_cognition_section(payload),
        "behavior": build_behavior_section(payload),
        "symbolism": build_symbolism_section(payload),
        "population": build_population_section(payload),
        "evolution": build_evolution_section(payload),
        "diagrams": build_diagrams_section(payload),
    }
