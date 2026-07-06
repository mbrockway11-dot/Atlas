
"""Build Cognitive Digital Twin states from systems report."""

from __future__ import annotations

from typing import Any

from atlas.cognitive_twin.states import CognitiveState


def build_cognitive_states(systems_report: dict[str, Any]) -> list[CognitiveState]:
    """Build cognitive states from reasoning and evidence."""
    executive = systems_report.get("executive", {})
    reasoning = systems_report.get("reasoning", {}).get("strongest_inferences", [])
    tensions = systems_report.get("tensions", {}).get("tensions", [])

    states: list[CognitiveState] = []

    inference_names = {item.get("inference") for item in reasoning}

    if "long_term_system_builder" in inference_names:
        states.append(
            CognitiveState(
                state_id="stable_builder",
                label="Stable Builder",
                category="baseline",
                confidence=confidence_for(reasoning, "long_term_system_builder"),
                triggers=("clear objective", "long horizon", "system continuity", "mission alignment"),
                behaviors=("plans in layers", "protects continuity", "builds durable systems", "compounds effort"),
                risks=("overholding structure", "delayed release", "carrying too much alone"),
                stabilizers=("defined scope", "visible progress markers", "trusted collaborators"),
            )
        )

    if "cross_domain_systems_thinker" in inference_names:
        states.append(
            CognitiveState(
                state_id="synthesis_mode",
                label="Cross-Domain Synthesis",
                category="cognitive",
                confidence=confidence_for(reasoning, "cross_domain_systems_thinker"),
                triggers=("complex problem", "multiple knowledge domains", "pattern mismatch", "novel connection"),
                behaviors=("routes information across domains", "builds frameworks", "compresses complexity", "maps relationships"),
                risks=("overextension", "too many active contexts", "difficulty simplifying"),
                stabilizers=("externalized diagrams", "clear decision criteria", "single active objective"),
            )
        )

    if "symbolic_pattern_compression" in inference_names:
        states.append(
            CognitiveState(
                state_id="symbolic_compression",
                label="Symbolic Compression",
                category="symbolic",
                confidence=confidence_for(reasoning, "symbolic_pattern_compression"),
                triggers=("abstract pattern", "symbolic material", "recursive motif", "hidden structure"),
                behaviors=("encodes meaning", "finds recurrence", "compresses themes", "builds symbolic maps"),
                risks=("over-symbolizing", "pattern saturation", "difficulty grounding"),
                stabilizers=("empirical check", "plain-language summary", "artifact output"),
            )
        )

    if "visible_authorship_through_structure" in inference_names:
        states.append(
            CognitiveState(
                state_id="visible_author",
                label="Visible Authorship",
                category="expression",
                confidence=confidence_for(reasoning, "visible_authorship_through_structure"),
                triggers=("audience", "finished structure", "teaching moment", "need to transmit"),
                behaviors=("explains systems", "creates public artifacts", "activates others", "turns structure into message"),
                risks=("performance pressure", "visibility fatigue", "overexplaining"),
                stabilizers=("prepared structure", "clear audience", "bounded delivery"),
            )
        )

    if tensions:
        states.append(
            CognitiveState(
                state_id="innovation_pressure",
                label="Innovation Pressure",
                category="tension",
                confidence=0.68,
                triggers=("old structure stops fitting", "novel opportunity", "constraint conflict", "stagnation"),
                behaviors=("tests discontinuity", "questions assumptions", "restructures system", "breaks stale patterns"),
                risks=("destabilizing continuity", "premature pivot", "internal contradiction"),
                stabilizers=("prototype first", "preserve core architecture", "controlled experiment"),
            )
        )

    if not states:
        states.append(
            CognitiveState(
                state_id="unresolved_baseline",
                label="Unresolved Baseline",
                category="baseline",
                confidence=0.5,
                triggers=("general task",),
                behaviors=("mixed response",),
                risks=("low model confidence",),
                stabilizers=("more evidence",),
            )
        )

    return states


def confidence_for(reasoning: list[dict[str, Any]], name: str) -> float:
    """Find inference confidence."""
    for item in reasoning:
        if item.get("inference") == name:
            return float(item.get("confidence") or 0.0)
    return 0.5
