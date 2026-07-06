
"""Autonomous Theory Engine report."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.theory.builder import build_theory_candidates
from atlas.autonomous.theory.clustering import cluster_theories
from atlas.autonomous.theory.promotion import promote_theories
from atlas.autonomous.theory.scoring import score_theory_candidates


THEORY_ENGINE_VERSION = "1.0.0"


def build_theory_report(
    evidence_records: list[dict[str, Any]],
    *,
    hypotheses: list[dict[str, Any]] | None = None,
    promotion_threshold: float = 0.58,
) -> dict[str, Any]:
    """Build full autonomous theory report."""
    candidates = build_theory_candidates(evidence_records, hypotheses=hypotheses)
    scored = score_theory_candidates(candidates)
    promoted = promote_theories(scored, threshold=promotion_threshold)
    clusters = cluster_theories(promoted)

    return {
        "success": True,
        "version": THEORY_ENGINE_VERSION,
        "evidence_count": len(evidence_records),
        "candidate_count": len(candidates),
        "promoted_count": sum(1 for item in promoted if item.get("status") == "promoted"),
        "theories": promoted,
        "clusters": clusters,
        "summary": build_summary(promoted),
    }


def build_summary(theories: list[dict[str, Any]]) -> str:
    """Build summary."""
    promoted = [item for item in theories if item.get("status") == "promoted"]

    if promoted:
        top = promoted[0]
        return (
            f"Theory Engine produced {len(theories)} theory candidate(s) and promoted {len(promoted)}. "
            f"Top promoted theory: {top.get('label')} ({top.get('theory_strength')})."
        )

    return f"Theory Engine produced {len(theories)} theory candidate(s), with none promoted yet."
