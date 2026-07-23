"""Deterministic question and hypothesis planning for relationship research.

The planner converts evidence-bounded relationship cohorts into a staged line
of inquiry.  It deliberately separates symbolic features from historical
outcomes and always generates null and confounder alternatives.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable


RESEARCH_VERSION = "atlas.autonomous.relationship-research.v1"

FEATURE_FAMILIES = {
    "kamea_shape": [
        "mean_consensus_shape_jaccard",
        "mean_directional_shape_jaccard",
        "mean_tortuosity_delta",
        "self_intersection_delta",
    ],
    "vedic": [
        "sidereal_contact_count",
        "nakshatra_relation_class",
        "timing_stable_contact_count",
    ],
    "numerology_gematria": [
        "numerology_similarity",
        "gematria_similarity",
        "name_length_matched_residual",
    ],
    "temporal": [
        "pre_event_transit_exposure",
        "event_window_transit_exposure",
        "post_event_transit_exposure",
    ],
}


def build_relationship_research_program(
    cohorts: Iterable[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
    top_n: int = 10,
) -> dict[str, Any]:
    """Build a ranked, preregistration-ready relationship research program."""
    normalized = [normalize_cohort(row) for row in cohorts]
    ranked_cohorts = sorted(
        (score_cohort(row) for row in normalized),
        key=lambda row: (-row["readiness_score"], row["pair_id"]),
    )

    questions: list[dict[str, Any]] = []
    for cohort in ranked_cohorts:
        cohort_questions = generate_relationship_questions(cohort, memory=memory)
        questions.extend(cohort_questions)
        questions.extend(generate_adaptive_followups(cohort_questions, memory))

    questions.extend(generate_cross_cohort_questions(ranked_cohorts, memory=memory))
    ranked_questions = sorted(
        questions,
        key=lambda row: (-row["priority_score"], row["question_id"]),
    )
    selected = [
        row for row in ranked_questions
        if not row.get("already_in_memory") and row.get("selection_eligible", True)
    ][: max(0, top_n)]
    hypotheses = [
        hypothesis
        for question in selected
        for hypothesis in build_competing_hypotheses(question)
    ]

    return {
        "success": True,
        "schema_version": RESEARCH_VERSION,
        "research_only": True,
        "causal_claims_allowed": False,
        "cohort_count": len(ranked_cohorts),
        "question_count": len(ranked_questions),
        "selected_count": len(selected),
        "hypothesis_count": len(hypotheses),
        "cohorts": ranked_cohorts,
        "questions": ranked_questions,
        "selected_questions": selected,
        "hypotheses": hypotheses,
        "next_actions": build_next_actions(ranked_cohorts, selected),
        "summary": (
            f"Generated {len(ranked_questions)} relationship question(s), selected "
            f"{len(selected)}, and preregistered {len(hypotheses)} competing "
            "hypotheses including null and confounder alternatives."
        ),
    }


def normalize_cohort(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize one pair without inventing missing evidence."""
    profile_a = str(row.get("profile_a") or "").strip()
    profile_b = str(row.get("profile_b") or "").strip()
    if not profile_a or not profile_b:
        raise ValueError("Each cohort requires profile_a and profile_b")

    pair_id = str(row.get("pair_id") or stable_id(profile_a, profile_b))
    return {
        **row,
        "pair_id": pair_id,
        "profile_a": profile_a,
        "profile_b": profile_b,
        "relationship_type": str(row.get("relationship_type") or "unknown"),
        "event_count": max(0, int(row.get("event_count") or 0)),
        "source_count": max(0, int(row.get("source_count") or 0)),
        "birth_time_status_a": str(row.get("birth_time_status_a") or "unknown"),
        "birth_time_status_b": str(row.get("birth_time_status_b") or "unknown"),
        "evidence_status": str(row.get("evidence_status") or "sources_required"),
    }


def score_cohort(cohort: dict[str, Any]) -> dict[str, Any]:
    """Score feasibility while exposing every component."""
    event_score = min(1.0, cohort["event_count"] / 8.0)
    source_score = min(1.0, cohort["source_count"] / 6.0)
    time_score = (
        birth_time_score(cohort["birth_time_status_a"])
        + birth_time_score(cohort["birth_time_status_b"])
    ) / 2.0
    evidence_score = {
        "locked": 1.0,
        "evidence_backed": 0.9,
        "in_progress": 0.55,
        "sources_required": 0.2,
    }.get(cohort["evidence_status"].lower(), 0.2)
    readiness = (
        event_score * 0.35
        + source_score * 0.25
        + time_score * 0.20
        + evidence_score * 0.20
    )
    blockers = []
    if cohort["event_count"] < 4:
        blockers.append("INSUFFICIENT_DATED_EVENTS")
    if cohort["source_count"] < 3:
        blockers.append("INSUFFICIENT_INDEPENDENT_SOURCES")
    if time_score < 0.5:
        blockers.append("BIRTH_TIME_SENSITIVITY_REQUIRED")
    if cohort["evidence_status"].lower() not in {"locked", "evidence_backed"}:
        blockers.append("EVENT_REGISTRY_NOT_LOCKED")

    return {
        **cohort,
        "readiness_score": round(readiness, 6),
        "readiness_components": {
            "dated_events": round(event_score, 6),
            "sources": round(source_score, 6),
            "birth_time": round(time_score, 6),
            "evidence": round(evidence_score, 6),
        },
        "blockers": blockers,
        "eligible_for_outcome_testing": not blockers,
    }


def generate_relationship_questions(
    cohort: dict[str, Any],
    *,
    memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate the next questions for one pair based on readiness and memory."""
    pair = cohort["pair_id"]
    questions: list[dict[str, Any]] = []
    if not cohort["eligible_for_outcome_testing"]:
        questions.append(question(
            pair,
            "evidence_completion",
            "What dated, citation-backed interaction events and matched control dates are missing?",
            stage="data_acquisition",
            outcome="registry_completeness",
            metrics=["event_count", "source_count", "date_precision"],
            controls=["source independence", "event selection audit"],
            cohort=cohort,
            memory=memory,
        ))

    questions.extend([
        question(
            pair,
            "birth_time_robustness",
            "Which relationship features remain stable across each profile's birth-time uncertainty interval?",
            stage="robustness",
            outcome="feature_stability",
            metrics=["stable_feature_ratio", "moon_longitude_span", "house_sign_change_count"],
            controls=["00:00/12:00/23:59 bounds", "timing-insensitive feature subset"],
            cohort=cohort,
            memory=memory,
        ),
        question(
            pair,
            "event_window_contrast",
            "Do preregistered features differ before, during, and after documented interaction events versus matched control dates?",
            stage="association_test",
            outcome="documented_event_window",
            metrics=FEATURE_FAMILIES["temporal"],
            controls=["matched non-event dates", "multiple-testing correction", "event-family clustering"],
            cohort=cohort,
            memory=memory,
        ),
        question(
            pair,
            "shape_outcome_contrast",
            "Do normalized Kamea route metrics distinguish collaborative, conflict, and neutral outcomes?",
            stage="association_test",
            outcome="relationship_outcome_class",
            metrics=FEATURE_FAMILIES["kamea_shape"],
            controls=["name-length matching", "cipher permutation", "random-pair baseline"],
            cohort=cohort,
            memory=memory,
        ),
        question(
            pair,
            "incremental_value",
            "Do symbolic feature families add held-out predictive value beyond historical and demographic baselines?",
            stage="incremental_validation",
            outcome="held_out_relationship_transition",
            metrics=[*FEATURE_FAMILIES["kamea_shape"], *FEATURE_FAMILIES["vedic"], *FEATURE_FAMILIES["numerology_gematria"]],
            controls=["history-only baseline", "demographic baseline", "family ablation", "held-out pairs"],
            cohort=cohort,
            memory=memory,
        ),
    ])
    return questions


def generate_cross_cohort_questions(
    cohorts: list[dict[str, Any]],
    *,
    memory: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Generate questions that can distinguish case anecdotes from replication."""
    if len(cohorts) < 2:
        return []
    ready = sum(bool(row["eligible_for_outcome_testing"]) for row in cohorts)
    payload = {
        "pair_id": "cross_cohort",
        "readiness_score": min(1.0, ready / 3.0),
        "eligible_for_outcome_testing": ready >= 2,
        "blockers": [] if ready >= 2 else ["FEWER_THAN_TWO_READY_COHORTS"],
    }
    return [question(
        "cross_cohort",
        "replication",
        "Which preregistered effects replicate across cooperative, adversarial, and rupture relationship cohorts?",
        stage="replication",
        outcome="cross_pair_effect_replication",
        metrics=["effect_direction_consistency", "corrected_effect_size", "holdout_accuracy"],
        controls=["leave-one-pair-out validation", "relationship-type strata", "random-pair baseline"],
        cohort=payload,
        memory=memory,
    )]


def question(
    pair_id: str,
    suffix: str,
    text: str,
    *,
    stage: str,
    outcome: str,
    metrics: list[str],
    controls: list[str],
    cohort: dict[str, Any],
    memory: dict[str, Any] | None,
) -> dict[str, Any]:
    question_id = f"relationship::{pair_id}::{suffix}"
    novelty = memory_novelty(question_id, memory)
    readiness = float(cohort.get("readiness_score") or 0.0)
    if stage in {"data_acquisition", "robustness"}:
        feasibility = 1.0
    else:
        feasibility = 1.0 if cohort.get("eligible_for_outcome_testing") else 0.25
    priority = 0.45 * readiness + 0.30 * novelty + 0.25 * feasibility
    return {
        "question_id": question_id,
        "pair_id": pair_id,
        "question": text,
        "kind": "relationship_hypothesis_program",
        "stage": stage,
        "outcome": outcome,
        "metrics": metrics,
        "controls": controls,
        "readiness": round(readiness, 6),
        "novelty": round(novelty, 6),
        "already_in_memory": novelty < 1.0,
        "feasibility": round(feasibility, 6),
        "selection_eligible": feasibility >= 1.0,
        "priority_score": round(priority, 6),
        "status": "generated",
    }


def build_competing_hypotheses(question_row: dict[str, Any]) -> list[dict[str, Any]]:
    """Create association, null, and confounder branches for a question."""
    base = question_row["question_id"]
    common = {
        "question_id": base,
        "pair_id": question_row["pair_id"],
        "stage": question_row["stage"],
        "outcome": question_row["outcome"],
        "metrics": question_row["metrics"],
        "controls": question_row["controls"],
        "status": "preregistered_candidate",
        "source": "autonomous_relationship_research",
        "locked_before_run": True,
        "research_only": True,
        "causal_claim": False,
        "promotion_requirements": [
            "minimum four dated events per relationship pair",
            "matched negative-control dates",
            "multiple-testing correction",
            "independent-pair replication",
            "held-out evaluation for predictive claims",
        ],
    }
    return [
        {
            **common,
            "hypothesis_id": f"{base}::association",
            "model_role": "candidate_association",
            "statement": "The preregistered metrics are associated with the documented outcome beyond matched controls.",
            "disconfirmation_rule": "Reject when corrected effects fail to exceed matched controls or reverse out of sample.",
        },
        {
            **common,
            "hypothesis_id": f"{base}::null",
            "model_role": "null",
            "statement": "The preregistered metrics do not distinguish the documented outcome from matched controls.",
            "disconfirmation_rule": "Reject only after a corrected effect replicates in an independent held-out pair.",
        },
        {
            **common,
            "hypothesis_id": f"{base}::confounder",
            "model_role": "rival_confounder",
            "statement": "Any apparent association is explained by event selection, name construction, birth-time uncertainty, or shared historical context.",
            "disconfirmation_rule": "Reject only when the association survives all listed controls and feature-family ablations.",
        },
    ]


def generate_adaptive_followups(
    questions: list[dict[str, Any]],
    memory: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    """Branch the next question from completed results in research memory."""
    followups = []
    for prior in questions:
        status = completed_question_status(prior["question_id"], memory)
        if status in {"supported", "retained", "promoted", "replicated"}:
            suffix = "independent_replication"
            prompt = (
                "Does the previously supported effect replicate in an unseen "
                "relationship pair and a held-out event interval?"
            )
            stage = "replication"
            controls = ["unseen pair", "held-out interval", "locked metric specification"]
        elif status in {"rejected", "falsified", "failed"}:
            suffix = "rival_model_ablation"
            prompt = (
                "Which rival explanation accounts for the failed effect after "
                "feature-family ablation and matched controls?"
            )
            stage = "falsification_followup"
            controls = ["one-family-at-a-time ablation", "random-pair baseline", "selection audit"]
        elif status in {"inconclusive", "underpowered", "blocked"}:
            suffix = "evidence_repair"
            prompt = (
                "What additional events, controls, or timing bounds would make "
                "the inconclusive question identifiable?"
            )
            stage = "evidence_repair"
            controls = ["power estimate", "missingness audit", "date-precision threshold"]
        else:
            continue

        followup_id = f"{prior['question_id']}::{suffix}"
        novelty = memory_novelty(followup_id, memory)
        followups.append({
            **prior,
            "question_id": followup_id,
            "question": prompt,
            "stage": stage,
            "controls": controls,
            "novelty": novelty,
            "already_in_memory": novelty < 1.0,
            "selection_eligible": True,
            "priority_score": round(0.70 + 0.20 * novelty, 6),
            "status": "adaptive_followup",
            "derived_from_question_id": prior["question_id"],
            "derived_from_status": status,
        })
    return followups


def completed_question_status(
    question_id: str,
    memory: dict[str, Any] | None,
) -> str:
    """Return a completed result label without treating planned work as evidence."""
    if not memory:
        return ""
    matches = []
    for record in (memory.get("experiments", {}) or {}).values():
        if str(record.get("question_id") or "") != question_id:
            continue
        status = str(record.get("decision") or record.get("result_status") or record.get("status") or "").lower()
        if status and status not in {"planned", "queued", "scheduled", "generated"}:
            matches.append(status)
    return matches[-1] if matches else ""


def build_next_actions(
    cohorts: list[dict[str, Any]],
    selected: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    actions = []
    for cohort in cohorts:
        if cohort["blockers"]:
            actions.append({
                "pair_id": cohort["pair_id"],
                "action": "complete_and_lock_event_registry",
                "reasons": cohort["blockers"],
            })
    if selected:
        actions.append({
            "pair_id": selected[0]["pair_id"],
            "action": "preregister_then_execute_highest_priority_question",
            "question_id": selected[0]["question_id"],
        })
    return actions


def birth_time_score(status: str) -> float:
    lowered = status.strip().lower()
    if lowered in {"verified", "documented", "recorded"}:
        return 1.0
    if lowered in {"reported", "reported_unverified", "estimated_historical"}:
        return 0.65
    if lowered in {"date_only", "unknown", "", "normalized"}:
        return 0.2
    return 0.35


def memory_novelty(question_id: str, memory: dict[str, Any] | None) -> float:
    if not memory:
        return 1.0
    serialized = json.dumps(memory, sort_keys=True, default=str).lower()
    return 0.1 if question_id.lower() in serialized else 1.0


def stable_id(left: str, right: str) -> str:
    names = sorted([left.strip().lower(), right.strip().lower()])
    digest = hashlib.sha256("::".join(names).encode("utf-8")).hexdigest()[:10]
    return f"{names[0]}__{names[1]}__{digest}"
