"""Atlas Falsification Engine service.

Builds explicit falsification tests from Atlas Hypothesis Engine output.

Purpose:
- Identify what could weaken or overturn each hypothesis.
- Convert hypotheses into testable research checks.
- Rank falsification pressure.
- Recommend the next confidence-improving observations.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.hypothesis_engine_service import build_hypothesis_payload


FALSIFICATION_ENGINE_VERSION = "1.0"


def list_falsification_profiles() -> list[str]:
    """Return profiles available for falsification workflows."""
    return list_saved_profiles()


def build_falsification_payload(query: str) -> dict[str, Any]:
    """Build falsification payload from a natural-language query."""
    hypothesis_payload = build_hypothesis_payload(query)

    if not hypothesis_payload.get("success"):
        return failure_payload(
            query=query,
            errors=hypothesis_payload.get("errors", []),
            warnings=hypothesis_payload.get("warnings", []),
        )

    hypothesis_model = hypothesis_payload.get("data", {}).get("hypothesis_model", {})
    falsification_model = build_falsification_model(
        query=query,
        hypothesis_model=hypothesis_model,
    )

    return {
        "success": True,
        "version": FALSIFICATION_ENGINE_VERSION,
        "query": query,
        "errors": hypothesis_payload.get("errors", []),
        "warnings": hypothesis_payload.get("warnings", []),
        "data": {
            "falsification_model": falsification_model,
            "hypothesis_summary": summarize_hypothesis_payload(hypothesis_payload),
        },
        "exports": {
            "falsification_json": falsification_model,
            "markdown": render_falsification_markdown(falsification_model),
        },
        "metrics": build_falsification_metrics(
            falsification_model,
            hypothesis_payload,
        ),
    }


def build_falsification_model(
    *,
    query: str,
    hypothesis_model: dict[str, Any],
) -> dict[str, Any]:
    """Build falsification model from hypothesis model."""
    hypotheses = hypothesis_model.get("hypotheses", [])
    falsification_cases = [
        build_falsification_case(hypothesis)
        for hypothesis in hypotheses
    ]

    ranked_cases = rank_falsification_cases(falsification_cases)

    return {
        "version": FALSIFICATION_ENGINE_VERSION,
        "query": query,
        "subject": hypothesis_model.get("subject", "unknown"),
        "intent": hypothesis_model.get("intent", "unknown"),
        "scope": hypothesis_model.get("scope", "unknown"),
        "definition": (
            "Falsification cases identify observations or computations that could "
            "weaken, overturn, or refine each hypothesis. They are designed to make "
            "Atlas conclusions testable rather than merely assertive."
        ),
        "cases": ranked_cases,
        "highest_priority_case": ranked_cases[0] if ranked_cases else {},
        "summary": {
            "case_count": len(ranked_cases),
            "test_count": sum(len(item.get("tests", [])) for item in ranked_cases),
            "observation_count": sum(
                len(item.get("required_observations", [])) for item in ranked_cases
            ),
            "repair_action_count": sum(
                len(item.get("repair_actions", [])) for item in ranked_cases
            ),
            "highest_priority": (
                ranked_cases[0].get("hypothesis_title", "n/a")
                if ranked_cases
                else "n/a"
            ),
        },
    }


def build_falsification_case(hypothesis: dict[str, Any]) -> dict[str, Any]:
    """Build one falsification case."""
    title = hypothesis.get("title", "Untitled Hypothesis")
    claim = hypothesis.get("claim", "")
    confidence = hypothesis.get("confidence", {})
    supporting = hypothesis.get("supporting_evidence", [])
    counter = hypothesis.get("counter_evidence", [])
    tests = hypothesis.get("falsification_tests", [])
    experiments = hypothesis.get("next_experiments", [])

    required_observations = build_required_observations(
        title=title,
        claim=claim,
        supporting=supporting,
        counter=counter,
        tests=tests,
    )

    disconfirming_signals = build_disconfirming_signals(
        title=title,
        claim=claim,
        counter=counter,
    )

    repair_actions = build_repair_actions(
        required_observations=required_observations,
        experiments=experiments,
    )

    pressure = build_falsification_pressure(
        confidence=confidence,
        supporting=supporting,
        counter=counter,
        tests=tests,
        observations=required_observations,
    )

    return {
        "hypothesis_title": title,
        "claim": claim,
        "current_confidence": confidence,
        "falsification_pressure": pressure,
        "tests": normalize_tests(tests),
        "required_observations": required_observations,
        "disconfirming_signals": disconfirming_signals,
        "repair_actions": repair_actions,
        "decision_rule": build_decision_rule(
            title=title,
            confidence=confidence,
            pressure=pressure,
        ),
        "source": hypothesis.get("source", "hypothesis_engine"),
        "metrics": {
            "supporting_evidence_count": len(supporting),
            "counter_evidence_count": len(counter),
            "test_count": len(tests),
            "required_observation_count": len(required_observations),
            "disconfirming_signal_count": len(disconfirming_signals),
            "repair_action_count": len(repair_actions),
        },
    }


def build_required_observations(
    *,
    title: str,
    claim: str,
    supporting: list[str],
    counter: list[str],
    tests: list[str],
) -> list[str]:
    """Build observations needed to test a hypothesis."""
    text_blob = " ".join([title, claim, *supporting, *counter, *tests]).lower()
    observations: list[str] = []

    if contains_any(text_blob, ["moon", "nakshatra", "dasha", "birth", "temporal", "transit"]):
        observations.extend(
            [
                "Resolve Moon Nakshatra and rerun temporal intelligence.",
                "Verify birth time and birth place metadata.",
                "Recompute dasha periods after temporal data repair.",
                "Compare results before and after temporal correction.",
            ]
        )

    if contains_any(text_blob, ["graph", "topology", "motif", "node", "edge", "sparse"]):
        observations.extend(
            [
                "Inspect CIG and STG node counts directly.",
                "Inspect CIG and STG edge counts directly.",
                "Rebuild or enrich graph artifacts if graph sparsity is detected.",
                "Compare graph intelligence before and after graph enrichment.",
            ]
        )

    if contains_any(text_blob, ["evidence", "claim", "narrative", "support"]):
        observations.extend(
            [
                "Open Evidence Explorer and inspect claim-level evidence.",
                "Check whether narrative claims have direct evidence support.",
                "Identify claims with high confidence but low evidence count.",
            ]
        )

    if contains_any(text_blob, ["similarity", "alignment", "relationship", "overlap", "morphology"]):
        observations.extend(
            [
                "Inspect shared nodes and shared edges separately.",
                "Compare morphology similarity against other pair baselines.",
                "Check whether low edge overlap is unique to this pair.",
                "Separate compatibility language from transformation language.",
            ]
        )

    if not observations:
        observations.append(
            "Inspect source service outputs and identify which evidence would most change confidence."
        )

    return dedupe(observations)


def build_disconfirming_signals(
    *,
    title: str,
    claim: str,
    counter: list[str],
) -> list[str]:
    """Build signals that would weaken the hypothesis."""
    text_blob = " ".join([title, claim, *counter]).lower()
    signals: list[str] = []

    if contains_any(text_blob, ["temporal", "moon", "nakshatra", "dasha", "birth"]):
        signals.extend(
            [
                "Temporal warnings disappear but hypothesis confidence does not change.",
                "Resolved Moon Nakshatra contradicts the current temporal interpretation.",
                "Verified birth metadata does not improve timing-sensitive confidence.",
            ]
        )

    if contains_any(text_blob, ["graph", "topology", "motif", "edge", "node"]):
        signals.extend(
            [
                "Graph enrichment does not change graph intelligence confidence.",
                "Node and edge counts are strong despite a graph-limitation hypothesis.",
                "Topology class remains stable after graph reconstruction.",
            ]
        )

    if contains_any(text_blob, ["relationship", "alignment", "similarity", "overlap"]):
        signals.extend(
            [
                "Pair similarity improves after correcting profile artifacts.",
                "Low edge overlap is normal across the comparison population.",
                "Relationship evidence supports strong alignment despite low morphology similarity.",
            ]
        )

    if contains_any(text_blob, ["evidence", "narrative", "claim"]):
        signals.extend(
            [
                "Evidence Explorer shows strong support for every major narrative claim.",
                "No high-confidence claim has weak or missing evidence.",
                "Counter-evidence does not materially affect the conclusion.",
            ]
        )

    if not signals:
        signals.append(
            "New source evidence directly contradicts the hypothesis claim."
        )

    return dedupe(signals)


def build_repair_actions(
    *,
    required_observations: list[str],
    experiments: list[str],
) -> list[str]:
    """Build concrete repair actions from observations and experiments."""
    actions = []

    for observation in required_observations:
        actions.append(f"Perform observation: {observation}")

    for experiment in experiments:
        actions.append(f"Run experiment: {experiment}")

    if not actions:
        actions.append("Run source service diagnostics and rebuild the hypothesis model.")

    return dedupe(actions)


def normalize_tests(tests: list[str]) -> list[dict[str, Any]]:
    """Normalize falsification tests into structured records."""
    records = []

    for index, test in enumerate(tests, start=1):
        records.append(
            {
                "id": f"test_{index}",
                "test": test,
                "status": "not_run",
                "expected_result_if_supported": "Hypothesis remains plausible.",
                "expected_result_if_falsified": "Hypothesis confidence should be reduced.",
            }
        )

    if not records:
        records.append(
            {
                "id": "test_1",
                "test": "Identify source evidence that would weaken this hypothesis.",
                "status": "not_run",
                "expected_result_if_supported": "Hypothesis remains plausible.",
                "expected_result_if_falsified": "Hypothesis confidence should be reduced.",
            }
        )

    return records


def build_falsification_pressure(
    *,
    confidence: dict[str, Any],
    supporting: list[str],
    counter: list[str],
    tests: list[str],
    observations: list[str],
) -> dict[str, Any]:
    """Score falsification pressure."""
    confidence_score = safe_float(confidence.get("score"))
    counter_pressure = min(len(counter) * 0.04, 0.32)
    test_pressure = min(len(tests) * 0.03, 0.18)
    observation_pressure = min(len(observations) * 0.02, 0.16)

    support_buffer = min(len(supporting) * 0.015, 0.18)

    pressure_score = clamp(
        (1.0 - confidence_score) * 0.35
        + counter_pressure
        + test_pressure
        + observation_pressure
        - support_buffer
    )

    return {
        "score": round(pressure_score, 4),
        "percent": round(pressure_score * 100, 2),
        "label": falsification_pressure_label(pressure_score),
        "components": {
            "confidence_inverse": round((1.0 - confidence_score) * 0.35, 4),
            "counter_pressure": round(counter_pressure, 4),
            "test_pressure": round(test_pressure, 4),
            "observation_pressure": round(observation_pressure, 4),
            "support_buffer": round(support_buffer, 4),
        },
    }


def falsification_pressure_label(score: float) -> str:
    """Resolve falsification pressure label."""
    if score >= 0.70:
        return "high"
    if score >= 0.45:
        return "moderate"
    if score >= 0.20:
        return "limited"
    return "low"


def build_decision_rule(
    *,
    title: str,
    confidence: dict[str, Any],
    pressure: dict[str, Any],
) -> str:
    """Build a decision rule for interpreting test results."""
    confidence_label = confidence.get("label", "unknown")
    pressure_label = pressure.get("label", "unknown")

    return (
        f"For {title}: if required observations resolve the main counter-evidence "
        f"without lowering support, preserve or raise the current {confidence_label} "
        f"confidence. If disconfirming signals appear, downgrade the hypothesis. "
        f"Current falsification pressure is {pressure_label}."
    )


def rank_falsification_cases(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank cases by falsification pressure."""
    return sorted(
        cases,
        key=lambda item: safe_float(item.get("falsification_pressure", {}).get("score")),
        reverse=True,
    )


def build_falsification_metrics(
    model: dict[str, Any],
    hypothesis_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build falsification metrics."""
    cases = model.get("cases", [])
    markdown = render_falsification_markdown(model)

    return {
        "case_count": len(cases),
        "test_count": sum(len(item.get("tests", [])) for item in cases),
        "observation_count": sum(
            len(item.get("required_observations", [])) for item in cases
        ),
        "disconfirming_signal_count": sum(
            len(item.get("disconfirming_signals", [])) for item in cases
        ),
        "repair_action_count": sum(
            len(item.get("repair_actions", [])) for item in cases
        ),
        "highest_priority_case": model.get("highest_priority_case", {}).get(
            "hypothesis_title"
        ),
        "highest_pressure": model.get("highest_priority_case", {}).get(
            "falsification_pressure",
            {},
        ),
        "word_count": len(markdown.split()),
        "source_hypothesis_count": hypothesis_payload.get("metrics", {}).get(
            "hypothesis_count",
            0,
        ),
        "source_warning_count": len(hypothesis_payload.get("warnings", [])),
        "source_error_count": len(hypothesis_payload.get("errors", [])),
    }


def render_falsification_markdown(model: dict[str, Any]) -> str:
    """Render falsification model as Markdown."""
    lines = [
        f"# Atlas Falsification Engine: {model.get('subject', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', FALSIFICATION_ENGINE_VERSION)}",
        f"**Intent:** {model.get('intent', 'unknown')}",
        f"**Scope:** {model.get('scope', 'unknown')}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Highest-Priority Falsification Case",
    ]

    highest = model.get("highest_priority_case", {})
    if highest:
        pressure = highest.get("falsification_pressure", {})
        lines.append(f"**{highest.get('hypothesis_title', 'Untitled')}**")
        lines.append("")
        lines.append(highest.get("claim", ""))
        lines.append("")
        lines.append(
            f"Falsification pressure: {pressure.get('percent', 0)}% "
            f"{pressure.get('label', 'unknown')}"
        )

    lines.append("")
    lines.append("## Falsification Cases")

    for case in model.get("cases", []):
        pressure = case.get("falsification_pressure", {})
        confidence = case.get("current_confidence", {})

        lines.append(f"### {case.get('hypothesis_title', 'Untitled')}")
        lines.append(case.get("claim", ""))
        lines.append(
            f"Current confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )
        lines.append(
            f"Falsification pressure: {pressure.get('percent', 0)}% "
            f"{pressure.get('label', 'unknown')}"
        )

        tests = case.get("tests", [])
        if tests:
            lines.append("")
            lines.append("Tests:")
            for test in tests:
                lines.append(f"- {test.get('test', '')}")

        observations = case.get("required_observations", [])
        if observations:
            lines.append("")
            lines.append("Required observations:")
            for observation in observations:
                lines.append(f"- {observation}")

        signals = case.get("disconfirming_signals", [])
        if signals:
            lines.append("")
            lines.append("Disconfirming signals:")
            for signal in signals:
                lines.append(f"- {signal}")

        actions = case.get("repair_actions", [])
        if actions:
            lines.append("")
            lines.append("Repair actions:")
            for action in actions:
                lines.append(f"- {action}")

        lines.append("")
        lines.append(f"Decision rule: {case.get('decision_rule', '')}")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def summarize_hypothesis_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe hypothesis summary."""
    model = payload.get("data", {}).get("hypothesis_model", {})

    return {
        "success": payload.get("success"),
        "warnings": payload.get("warnings", []),
        "errors": payload.get("errors", []),
        "metrics": payload.get("metrics", {}),
        "subject": model.get("subject"),
        "best_supported_hypothesis": model.get("best_supported_hypothesis", {}).get(
            "title"
        ),
        "hypothesis_count": len(model.get("hypotheses", [])),
    }


def contains_any(text: str, keywords: list[str]) -> bool:
    """Return whether text contains any keyword."""
    return any(keyword.lower() in text for keyword in keywords)


def dedupe(values: list[str]) -> list[str]:
    """Dedupe values while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
    return max(0.0, min(1.0, value))


def failure_payload(
    *,
    query: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": FALSIFICATION_ENGINE_VERSION,
        "query": query,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def json_export(data: Any) -> str:
    """Serialize falsification JSON."""
    return json.dumps(data, indent=2, sort_keys=True)