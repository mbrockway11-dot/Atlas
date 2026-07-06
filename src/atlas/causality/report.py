
"""Causal Hypothesis Engine report."""

from __future__ import annotations

from typing import Any

from atlas.causality.candidate_models import build_candidate_models
from atlas.causality.confidence import score_causal_confidence
from atlas.causality.interventions import simulate_interventions
from atlas.causality.scanner import scan_causal_candidates


CAUSAL_REPORT_VERSION = "1.0.0"


def build_causal_hypothesis_report(
    records: list[dict[str, Any]],
    *,
    extra_candidates: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build full causal hypothesis report."""
    candidates = build_candidate_models(extra_candidates)
    scans = scan_causal_candidates(records, candidates)
    interventions = simulate_interventions(records, scans)
    scored = score_causal_confidence(scans, interventions)

    return {
        "success": True,
        "version": CAUSAL_REPORT_VERSION,
        "record_count": len(records),
        "candidate_count": len(candidates),
        "candidates": candidates,
        "scans": scans,
        "interventions": interventions,
        "causal_hypotheses": scored,
        "summary": build_summary(scored),
    }


def build_summary(scored: list[dict[str, Any]]) -> str:
    """Build report summary."""
    if not scored:
        return "Causal Hypothesis Engine found no candidate models."

    strongest = scored[0]

    return (
        f"Causal Hypothesis Engine evaluated {len(scored)} candidate model(s). "
        f"Strongest candidate: {strongest.get('candidate_id')} "
        f"({strongest.get('causal_label')}, confidence {strongest.get('causal_confidence')})."
    )
