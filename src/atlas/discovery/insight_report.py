
"""Discovery Engine report builder."""

from __future__ import annotations

from typing import Any

from atlas.discovery.correlation_scanner import scan_correlations
from atlas.discovery.evidence_ranker import rank_discovery_evidence
from atlas.discovery.hypotheses import build_hypotheses
from atlas.discovery.questions import build_discovery_questions


DISCOVERY_VERSION = "1.0.0"


def build_discovery_report(
    records: list[dict[str, Any]],
    *,
    extra_questions: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build Discovery Engine report."""
    questions = build_discovery_questions(extra_questions)
    scans = scan_correlations(records, questions)
    hypotheses = build_hypotheses(scans)
    ranked = rank_discovery_evidence(hypotheses)

    return {
        "success": True,
        "version": DISCOVERY_VERSION,
        "record_count": len(records),
        "question_count": len(questions),
        "scan_count": len(scans),
        "hypothesis_count": len(hypotheses),
        "questions": questions,
        "correlation_scans": scans,
        "hypotheses": hypotheses,
        "ranked_evidence": ranked,
        "summary": build_summary(records, scans, hypotheses),
    }


def build_summary(
    records: list[dict[str, Any]],
    scans: list[dict[str, Any]],
    hypotheses: list[dict[str, Any]],
) -> str:
    """Build report summary."""
    strongest = hypotheses[0] if hypotheses else None

    if strongest:
        return (
            f"Discovery Engine scanned {len(scans)} question(s) across {len(records)} record(s) "
            f"and generated {len(hypotheses)} hypothesis/hypotheses. Strongest: "
            f"{strongest.get('hypothesis')}"
        )

    return (
        f"Discovery Engine scanned {len(scans)} question(s) across {len(records)} record(s), "
        "but no hypothesis crossed the current evidence threshold."
    )
