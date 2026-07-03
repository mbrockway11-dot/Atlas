"""Atlas question-answer service.

This service turns normal user questions into readable Atlas interpretations.

It sits above the AI research runtime:

User Question
    -> Atlas QA Service
    -> AI Orchestrator
    -> Query Planner / Hypothesis / Falsification / Experiment / Discovery / Memory
    -> Plain-language answer

The goal is clarity, not pretending uncertainty is certainty.
"""

from __future__ import annotations

from typing import Any

from atlas.ai import run_research_pipeline


ATLAS_QA_SERVICE_VERSION = "3.0"


def answer_question(question: str) -> dict[str, Any]:
    """Answer a user question in clear, layered Atlas language."""
    clean_question = question.strip()

    if not clean_question:
        return failure_payload(
            question=question,
            error="Question is required.",
            answer="Ask Atlas a question first.",
        )

    runtime = run_research_pipeline(clean_question)

    stages = runtime.stages
    integrated = runtime.integrated

    query_plan = get_stage_model(stages, "query_planner", "plan")
    hypothesis_model = get_stage_model(stages, "hypothesis", "hypothesis_model")
    falsification_model = get_stage_model(stages, "falsification", "falsification_model")
    experiment_model = get_stage_model(stages, "experiment_planner", "experiment_model")
    discovery_model = get_stage_model(stages, "discovery", "discovery_model")
    memory_record = get_stage_model(stages, "research_memory", "memory_record")

    hypotheses = ensure_list(hypothesis_model.get("hypotheses"))
    best_hypothesis = (
        hypothesis_model.get("best_supported_hypothesis")
        or first(hypotheses)
    )

    falsification_cases = ensure_list(falsification_model.get("cases"))
    experiments = ensure_list(experiment_model.get("experiments"))
    discoveries = ensure_list(discovery_model.get("discoveries"))

    answer = build_layered_answer(
        question=clean_question,
        query_plan=query_plan,
        best_hypothesis=best_hypothesis,
        hypotheses=hypotheses,
        falsification_cases=falsification_cases,
        experiments=experiments,
        discoveries=discoveries,
        runtime=runtime,
    )

    return {
        "success": runtime.success,
        "version": ATLAS_QA_SERVICE_VERSION,
        "question": clean_question,
        "answer": answer,
        "key_points": build_key_points(
            best_hypothesis=best_hypothesis,
            hypotheses=hypotheses,
            falsification_cases=falsification_cases,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "confidence": resolve_confidence(best_hypothesis),
        "evidence": collect_evidence(best_hypothesis, discoveries),
        "limitations": collect_limitations(falsification_cases, runtime),
        "suggested_next_questions": build_suggested_questions(
            question=clean_question,
            experiments=experiments,
            discoveries=discoveries,
        ),
        "metrics": {
            "completed_stages": len(integrated.get("completed_stages", [])),
            "failed_stages": len(integrated.get("failed_stages", [])),
            "hypotheses": len(hypotheses),
            "falsification_cases": len(falsification_cases),
            "experiments": len(experiments),
            "discoveries": len(discoveries),
            "has_research_memory": bool(memory_record),
        },
        "warnings": runtime.warnings,
        "errors": runtime.errors,
        "raw": {
            "runtime": runtime.to_dict(),
            "query_plan": query_plan,
            "hypothesis_model": hypothesis_model,
            "falsification_model": falsification_model,
            "experiment_model": experiment_model,
            "discovery_model": discovery_model,
            "memory_record": memory_record,
        },
    }


def build_layered_answer(
    *,
    question: str,
    query_plan: dict[str, Any],
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
    runtime: Any,
) -> str:
    """Build an eloquent, easy-to-understand Atlas answer."""
    if not runtime.success:
        return (
            "Atlas could not complete the full research pipeline for this question. "
            "The interpretation is incomplete because one or more AI stages failed. "
            "Review the warnings and errors before treating the result as usable."
        )

    intent = query_plan.get("intent", "interpretation")
    scope = query_plan.get("scope", "unknown")

    claim = extract_claim(best_hypothesis)

    if claim:
        synthesis = claim
    else:
        synthesis = (
            "Atlas processed the question successfully, but it did not identify one "
            "dominant hypothesis. The answer should be treated as provisional."
        )

    return f"""Atlas can answer this question through a layered interpretive frame.

Question

{question}

Data and Confidence

Atlas is using the information currently available in the project corpus and research runtime. If exact Kamea graphs, natal charts, transit overlays, or population comparisons are not present for the subjects involved, Atlas should not pretend those outputs exist. It should provide a rich interpretation from available data while clearly marking uncertain parts as probable rather than final.

Detected Intent

Atlas reads this as a {intent} question with {scope} scope.

Structural Layer

The structural layer describes how a person, pair, or system appears to organize reality. This is where Atlas looks for Driver, Amplifier, and Regulator tendencies.

- Driver describes what initiates movement.
- Amplifier describes what intensifies signal, meaning, emotion, or expression.
- Regulator describes what stabilizes, disciplines, delays, or contains the system.

In plain language, this layer asks: What role does this person or dynamic naturally play in a field?

Natal Layer

The natal layer explains why the structure may express itself in a particular way. Atlas treats natal influence as interpretive context rather than isolated prediction.

- Sun describes identity, vitality, and core orientation.
- Moon describes emotional regulation, instinct, and inner safety.
- Mercury describes cognition, language, perception, and communication.
- Venus describes values, attraction, taste, harmony, and relational tone.
- Mars describes action, pressure, conflict style, and execution.
- Jupiter describes growth, faith, scale, and expansion.
- Saturn describes discipline, limits, responsibility, and mastery.
- Uranus describes disruption, independence, and innovation.
- Neptune describes imagination, symbolism, longing, and ambiguity.
- Pluto describes transformation, intensity, power, and deep pressure.

This layer asks: Why does this structure tend to behave the way it does?

Integrated Interpretation

Atlas' best current synthesis is:

{synthesis}

This interpretation is supported by {len(hypotheses)} generated hypotheses, {len(falsification_cases)} falsification checks, {len(experiments)} proposed experiments, and {len(discoveries)} discovery signals.

Interaction Dynamics

When Atlas evaluates two people or a group, it should explain how their structures react against each other. Some people reinforce each other's signal. Some stabilize each other. Some amplify unresolved pressure. A strong interpretation should describe the likely feedback loop, not just each person separately.

In high alignment, Driver, Amplifier, and Regulator roles become complementary. One person may provide movement while another gives emotional meaning or containment. In stress, the same traits can polarize: Driver becomes force, Amplifier becomes overwhelm, and Regulator becomes rigidity or withdrawal.

Probable Outcomes

Atlas should present outcomes as scenarios, not certainties.

- High alignment: the available structures reinforce coherence, expression, and shared purpose.
- Moderate stress: differences in pacing, emotional need, communication style, or control strategy become visible.
- Low alignment: each person may interpret the other's natural function as resistance, intensity, distance, or instability.
- Growth path: the best outcome usually comes when each role is named consciously and used intentionally.

Evidence and Uncertainty

Computed outputs should be treated as evidence. Behavioral descriptions are interpretive synthesis. Exact Kamea node weights, natal placements, transit timing, graph metrics, and population comparisons increase confidence when available. Without those complete outputs, Atlas should still answer meaningfully, but it should speak in probabilities rather than final claims."""


def build_key_points(
    *,
    best_hypothesis: dict[str, Any] | None,
    hypotheses: list[dict[str, Any]],
    falsification_cases: list[dict[str, Any]],
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Build readable key points."""
    points: list[str] = []

    if best_hypothesis:
        title = best_hypothesis.get("title") or "Best supported hypothesis"
        points.append(f"Best hypothesis: {title}")

    points.append(f"Atlas generated {len(hypotheses)} hypotheses.")
    points.append(f"Atlas checked {len(falsification_cases)} ways the answer could be wrong.")
    points.append(f"Atlas proposed {len(experiments)} next experiments.")

    if discoveries:
        points.append(f"Atlas found {len(discoveries)} discovery signals.")

    return points


def collect_evidence(
    best_hypothesis: dict[str, Any] | None,
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Collect evidence snippets."""
    evidence: list[str] = []

    if best_hypothesis:
        for key in ("supporting_evidence", "evidence", "support"):
            value = best_hypothesis.get(key)

            if isinstance(value, list):
                evidence.extend(str(item) for item in value)
            elif value:
                evidence.append(str(value))

    for discovery in discoveries[:3]:
        summary = discovery.get("summary") or discovery.get("title")
        if summary:
            evidence.append(str(summary))

    return dedupe(evidence)[:10]


def collect_limitations(
    falsification_cases: list[dict[str, Any]],
    runtime: Any,
) -> list[str]:
    """Collect limitations and caveats."""
    limitations: list[str] = []

    for case in falsification_cases[:4]:
        title = case.get("title") or case.get("claim")
        if title:
            limitations.append(f"Needs falsification check: {title}")

        pressure = case.get("pressure") or case.get("falsification_pressure")
        if isinstance(pressure, dict) and pressure.get("label"):
            limitations.append(f"Falsification pressure: {pressure['label']}")

    limitations.extend(str(warning) for warning in runtime.warnings[:5])

    if not limitations:
        limitations.append(
            "Interpretive confidence depends on the completeness of available profile, natal, graph, and Kamea data."
        )

    return dedupe(limitations)[:10]


def build_suggested_questions(
    *,
    question: str,
    experiments: list[dict[str, Any]],
    discoveries: list[dict[str, Any]],
) -> list[str]:
    """Suggest useful follow-up questions."""
    suggestions: list[str] = []

    for experiment in experiments[:3]:
        title = experiment.get("title")
        if title:
            suggestions.append(f"What would confirm or disprove: {title}?")

    for discovery in discoveries[:2]:
        title = discovery.get("title")
        if title:
            suggestions.append(f"What does this discovery imply: {title}?")

    if not suggestions:
        suggestions = [
            f"What evidence supports this answer to: {question}?",
            f"What would falsify this answer to: {question}?",
            f"What natal factors would refine this answer to: {question}?",
            f"What Kamea outputs would increase confidence for: {question}?",
        ]

    return dedupe(suggestions)[:6]


def resolve_confidence(best_hypothesis: dict[str, Any] | None) -> str:
    """Resolve readable confidence label."""
    if not best_hypothesis:
        return "provisional"

    confidence = best_hypothesis.get("confidence")

    if isinstance(confidence, dict):
        return str(
            confidence.get("label")
            or confidence.get("score")
            or "unknown"
        )

    if confidence:
        return str(confidence)

    return "unknown"


def extract_claim(best_hypothesis: dict[str, Any] | None) -> str:
    """Extract the clearest claim text."""
    if not best_hypothesis:
        return ""

    for key in ("claim", "summary", "title"):
        value = best_hypothesis.get(key)
        if value:
            return str(value)

    return ""


def get_stage_model(
    stages: dict[str, Any],
    stage_name: str,
    model_key: str,
) -> dict[str, Any]:
    """Read a stage model from runtime stages."""
    stage = stages.get(stage_name)
    if not stage:
        return {}

    payload = getattr(stage, "payload", {}) or {}
    data = payload.get("data", {})

    model = data.get(model_key)
    return model if isinstance(model, dict) else {}


def ensure_list(value: Any) -> list[Any]:
    """Normalize values to a list."""
    if value is None:
        return []

    if isinstance(value, list):
        return value

    return [value]


def first(values: list[Any]) -> Any:
    """Return first item or None."""
    return values[0] if values else None


def dedupe(values: list[str]) -> list[str]:
    """Preserve order while removing duplicates."""
    seen: set[str] = set()
    result: list[str] = []

    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)

    return result


def failure_payload(*, question: str, error: str, answer: str) -> dict[str, Any]:
    """Build a failed QA payload."""
    return {
        "success": False,
        "version": ATLAS_QA_SERVICE_VERSION,
        "question": question,
        "answer": answer,
        "key_points": [],
        "confidence": "none",
        "evidence": [],
        "limitations": [error],
        "suggested_next_questions": [],
        "metrics": {
            "completed_stages": 0,
            "failed_stages": 0,
            "hypotheses": 0,
            "falsification_cases": 0,
            "experiments": 0,
            "discoveries": 0,
            "has_research_memory": False,
        },
        "warnings": [],
        "errors": [error],
        "raw": {},
    }