
"""Decision candidate generation for simulation."""

from __future__ import annotations

from typing import Any


DECISION_MAP = {
    "compound_systems_builder": ("structure_plan", "protect_continuity", "sequence_work"),
    "cross_domain_synthesizer": ("map_relationships", "gather_information", "connect_domains"),
    "symbolic_system_builder": ("compress_into_model", "build_symbolic_artifact", "name_the_pattern"),
    "visible_structural_author": ("explain_publicly", "teach_framework", "publish_artifact"),
    "stable_executor": ("reduce_noise", "stabilize_environment", "execute_conservatively"),
}


def build_decision_candidates(propagated: dict[str, float]) -> dict[str, Any]:
    """Generate ranked decision candidates from activated inference nodes."""
    candidates: dict[str, float] = {}

    for node_id, activation in propagated.items():
        inference = str(node_id).replace("inference:", "")

        for action in DECISION_MAP.get(inference, ()):
            candidates[action] = max(candidates.get(action, 0.0), float(activation))

    ranked = sorted(
        [
            {"action": action, "score": round(score, 6)}
            for action, score in candidates.items()
        ],
        key=lambda item: item["score"],
        reverse=True,
    )

    return {
        "candidate_count": len(ranked),
        "ranked_candidates": ranked,
        "likely_action": ranked[0] if ranked else None,
    }
