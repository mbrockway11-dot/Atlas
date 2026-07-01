"""Atlas Hypothesis Engine service.

Generates competing, evidence-bounded hypotheses from Atlas Reasoning output.

The Hypothesis Engine does not replace the Reasoning service.
It takes a reasoning payload and produces:
- competing hypotheses
- supporting evidence
- counter-evidence
- falsification tests
- next experiments
- best-supported explanation
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.reasoning_service import build_reasoning_payload


HYPOTHESIS_ENGINE_VERSION = "1.0"


def list_hypothesis_profiles() -> list[str]:
    """Return profiles available for hypothesis workflows."""
    return list_saved_profiles()


def build_hypothesis_payload(query: str) -> dict[str, Any]:
    """Build hypothesis payload from a natural-language query."""
    reasoning_payload = build_reasoning_payload(query)
    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})

    if not reasoning_payload.get("success"):
        return failure_payload(
            query=query,
            errors=reasoning_payload.get("errors", []),
            warnings=reasoning_payload.get("warnings", []),
        )

    hypotheses = build_hypotheses_from_reasoning(reasoning)
    best = select_best_supported_hypothesis(hypotheses)

    model = {
        "version": HYPOTHESIS_ENGINE_VERSION,
        "query": query,
        "subject": reasoning.get("subject", "unknown"),
        "intent": reasoning.get("intent", "unknown"),
        "scope": reasoning.get("scope", "unknown"),
        "hypotheses": hypotheses,
        "best_supported_hypothesis": best,
        "summary": {
            "hypothesis_count": len(hypotheses),
            "best_title": best.get("title", "n/a"),
            "best_confidence": best.get("confidence", {}),
            "reasoning_confidence": reasoning.get("confidence", {}).get("overall", {}),
        },
    }

    return {
        "success": True,
        "version": HYPOTHESIS_ENGINE_VERSION,
        "query": query,
        "errors": reasoning_payload.get("errors", []),
        "warnings": reasoning_payload.get("warnings", []),
        "data": {
            "hypothesis_model": model,
            "reasoning_summary": summarize_reasoning(reasoning_payload),
        },
        "exports": {
            "hypothesis_json": model,
            "markdown": render_hypothesis_markdown(model),
        },
        "metrics": build_hypothesis_metrics(model, reasoning_payload),
    }


def build_hypotheses_from_reasoning(reasoning: dict[str, Any]) -> list[dict[str, Any]]:
    """Build competing hypotheses from reasoning output."""
    scope = reasoning.get("scope", "unknown")

    if scope == "relationship":
        return build_relationship_hypotheses(reasoning)

    return build_profile_hypotheses(reasoning)


def build_profile_hypotheses(reasoning: dict[str, Any]) -> list[dict[str, Any]]:
    """Build profile-level hypotheses."""
    subject = reasoning.get("subject", "unknown")
    conclusions = reasoning.get("conclusions", [])
    limitations = reasoning.get("limitations", [])
    recommendations = reasoning.get("recommendations", [])
    confidence = reasoning.get("confidence", {})
    overall = confidence.get("overall", {})

    primary_evidence = collect_conclusion_evidence(conclusions)
    risk_evidence = limitations

    hypotheses = [
        hypothesis(
            title="Integrated Profile Hypothesis",
            claim=(
                f"{subject} is best understood through an integrated Atlas profile synthesis "
                "combining identity, narrative, evidence, graph, and temporal layers."
            ),
            confidence=overall,
            supporting_evidence=primary_evidence,
            counter_evidence=risk_evidence,
            falsification_tests=[
                "If core services disagree strongly, reduce confidence in integrated synthesis.",
                "If evidence records do not support narrative claims, downgrade this hypothesis.",
                "If graph and temporal layers are missing or sparse, treat the synthesis as partial.",
            ],
            next_experiments=recommendations[:6],
            source="reasoning_service",
        ),
        hypothesis(
            title="Graph-Limited Interpretation Hypothesis",
            claim=(
                f"{subject}'s interpretation may be constrained primarily by graph sparsity, "
                "graph confidence limits, or topology uncertainty."
            ),
            confidence=derive_hypothesis_confidence(
                base=overall,
                boost_keywords=risk_evidence,
                keywords=["graph", "topology", "motif", "edge", "node", "sparse"],
                mode="risk",
            ),
            supporting_evidence=filter_items(
                risk_evidence + primary_evidence,
                ["graph", "topology", "motif", "edge", "node", "sparse"],
            ),
            counter_evidence=filter_items(
                primary_evidence,
                ["temporal", "narrative", "evidence", "profile"],
            ),
            falsification_tests=[
                "Rebuild graph stack and check whether topology confidence improves.",
                "Compare profile against nearest graph neighbors.",
                "Inspect CIG/STG node and edge counts directly.",
            ],
            next_experiments=[
                "Open Graph Explorer for this profile.",
                "Run Graph Intelligence and inspect cautions.",
                "Compare graph topology with similar corpus profiles.",
            ],
            source="graph_reasoning",
        ),
        hypothesis(
            title="Temporal-Uncertainty Hypothesis",
            claim=(
                f"{subject}'s interpretation may be constrained by temporal uncertainty, "
                "birth-time limitations, nakshatra resolution, or dasha precision."
            ),
            confidence=derive_hypothesis_confidence(
                base=overall,
                boost_keywords=risk_evidence,
                keywords=["moon", "nakshatra", "birth", "dasha", "temporal", "transit"],
                mode="risk",
            ),
            supporting_evidence=filter_items(
                risk_evidence + primary_evidence,
                ["moon", "nakshatra", "birth", "dasha", "temporal", "transit"],
            ),
            counter_evidence=filter_items(
                primary_evidence,
                ["graph", "evidence", "narrative"],
            ),
            falsification_tests=[
                "Resolve Moon Nakshatra and rerun temporal intelligence.",
                "Improve birth metadata and check whether dasha confidence changes.",
                "Compare results with and without timing-sensitive layers.",
            ],
            next_experiments=[
                "Audit temporal metrics.",
                "Resolve missing birth time or place fields.",
                "Rerun Profile Report after temporal data correction.",
            ],
            source="temporal_intelligence",
        ),
    ]

    return rank_hypotheses(hypotheses)


def build_relationship_hypotheses(reasoning: dict[str, Any]) -> list[dict[str, Any]]:
    """Build relationship-level hypotheses."""
    subject = reasoning.get("subject", "unknown")
    conclusions = reasoning.get("conclusions", [])
    limitations = reasoning.get("limitations", [])
    recommendations = reasoning.get("recommendations", [])
    confidence = reasoning.get("confidence", {})
    overall = confidence.get("overall", {})

    primary_evidence = collect_conclusion_evidence(conclusions)
    risk_evidence = limitations

    hypotheses = [
        hypothesis(
            title="Transformation Hypothesis",
            claim=(
                f"{subject} is best interpreted as a structural transformation analysis, "
                "not a simple compatibility judgment."
            ),
            confidence=overall,
            supporting_evidence=primary_evidence,
            counter_evidence=risk_evidence,
            falsification_tests=[
                "If morphology metrics are sparse or low-confidence, downgrade transformation claims.",
                "If edge overlap remains very low, avoid strong alignment claims.",
                "If evidence records do not support relationship claims, downgrade synthesis.",
            ],
            next_experiments=recommendations[:6],
            source="relationship_reasoning",
        ),
        hypothesis(
            title="Limited Alignment Hypothesis",
            claim=(
                f"{subject} may have limited graph alignment because similarity, edge overlap, "
                "or relationship graph confidence is constrained."
            ),
            confidence=derive_hypothesis_confidence(
                base=overall,
                boost_keywords=risk_evidence + primary_evidence,
                keywords=["similarity", "edge overlap", "limited", "alignment", "graph"],
                mode="risk",
            ),
            supporting_evidence=filter_items(
                risk_evidence + primary_evidence,
                ["similarity", "edge overlap", "limited", "alignment", "graph"],
            ),
            counter_evidence=filter_items(
                primary_evidence,
                ["both profiles", "temporal", "morphology class"],
            ),
            falsification_tests=[
                "Inspect shared nodes and shared edges separately.",
                "Compare this pair against other pairs in the same archetype class.",
                "Check whether low edge overlap is unique or common in the population.",
            ],
            next_experiments=[
                "Open Relationship Report.",
                "Open Graph Intelligence relationship mode.",
                "Inspect relationship evidence records.",
            ],
            source="relationship_graph_intelligence",
        ),
        hypothesis(
            title="Temporal-Layer Caution Hypothesis",
            claim=(
                f"{subject} may be limited by unresolved temporal assumptions, "
                "especially if birth-time or nakshatra data is incomplete."
            ),
            confidence=derive_hypothesis_confidence(
                base=overall,
                boost_keywords=risk_evidence,
                keywords=["moon", "nakshatra", "birth", "dasha", "temporal"],
                mode="risk",
            ),
            supporting_evidence=filter_items(
                risk_evidence,
                ["moon", "nakshatra", "birth", "dasha", "temporal"],
            ),
            counter_evidence=filter_items(
                primary_evidence,
                ["graph", "morphology", "relationship"],
            ),
            falsification_tests=[
                "Resolve temporal warnings for both profiles.",
                "Rerun relationship report after temporal correction.",
                "Compare relationship graph-only output against temporal-inclusive output.",
            ],
            next_experiments=[
                "Audit both profile temporal payloads.",
                "Resolve missing research_session artifacts.",
                "Rebuild relationship report after artifact repair.",
            ],
            source="temporal_relationship",
        ),
    ]

    return rank_hypotheses(hypotheses)


def hypothesis(
    *,
    title: str,
    claim: str,
    confidence: dict[str, Any],
    supporting_evidence: list[str],
    counter_evidence: list[str],
    falsification_tests: list[str],
    next_experiments: list[str],
    source: str,
) -> dict[str, Any]:
    """Build one hypothesis."""
    support_count = len([item for item in supporting_evidence if item])
    counter_count = len([item for item in counter_evidence if item])

    base_score = safe_float(confidence.get("score"))
    evidence_bonus = min(support_count * 0.025, 0.15)
    counter_penalty = min(counter_count * 0.02, 0.16)

    score = clamp(base_score + evidence_bonus - counter_penalty)

    return {
        "title": title,
        "claim": claim,
        "confidence": confidence_record(score),
        "supporting_evidence": dedupe([item for item in supporting_evidence if item]),
        "counter_evidence": dedupe([item for item in counter_evidence if item]),
        "falsification_tests": falsification_tests,
        "next_experiments": next_experiments,
        "source": source,
        "metrics": {
            "supporting_evidence_count": support_count,
            "counter_evidence_count": counter_count,
            "falsification_test_count": len(falsification_tests),
            "next_experiment_count": len(next_experiments),
        },
    }


def derive_hypothesis_confidence(
    *,
    base: dict[str, Any],
    boost_keywords: list[str],
    keywords: list[str],
    mode: str,
) -> dict[str, Any]:
    """Derive hypothesis confidence from keyword support."""
    base_score = safe_float(base.get("score"))
    matches = filter_items(boost_keywords, keywords)
    match_bonus = min(len(matches) * 0.06, 0.24)

    if mode == "risk":
        score = clamp(base_score * 0.75 + match_bonus)
    else:
        score = clamp(base_score + match_bonus)

    return confidence_record(score)


def rank_hypotheses(hypotheses: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Rank hypotheses by confidence score."""
    return sorted(
        hypotheses,
        key=lambda item: safe_float(item.get("confidence", {}).get("score")),
        reverse=True,
    )


def select_best_supported_hypothesis(
    hypotheses: list[dict[str, Any]],
) -> dict[str, Any]:
    """Select best-supported hypothesis."""
    if not hypotheses:
        return {}

    return hypotheses[0]


def collect_conclusion_evidence(conclusions: list[dict[str, Any]]) -> list[str]:
    """Collect evidence from reasoning conclusions."""
    evidence: list[str] = []

    for item in conclusions:
        conclusion_text = item.get("conclusion", "")
        if conclusion_text:
            evidence.append(conclusion_text)

        for entry in item.get("evidence", []):
            evidence.append(str(entry))

    return dedupe(evidence)


def filter_items(items: list[str], keywords: list[str]) -> list[str]:
    """Filter items containing any keyword."""
    filtered = []

    for item in items:
        lowered = str(item).lower()
        if any(keyword.lower() in lowered for keyword in keywords):
            filtered.append(str(item))

    return dedupe(filtered)


def build_hypothesis_metrics(
    model: dict[str, Any],
    reasoning_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build hypothesis metrics."""
    hypotheses = model.get("hypotheses", [])
    markdown = render_hypothesis_markdown(model)

    return {
        "hypothesis_count": len(hypotheses),
        "best_hypothesis": model.get("best_supported_hypothesis", {}).get("title"),
        "best_confidence": model.get("best_supported_hypothesis", {}).get("confidence", {}),
        "supporting_evidence_count": sum(
            len(item.get("supporting_evidence", [])) for item in hypotheses
        ),
        "counter_evidence_count": sum(
            len(item.get("counter_evidence", [])) for item in hypotheses
        ),
        "falsification_test_count": sum(
            len(item.get("falsification_tests", [])) for item in hypotheses
        ),
        "next_experiment_count": sum(
            len(item.get("next_experiments", [])) for item in hypotheses
        ),
        "word_count": len(markdown.split()),
        "source_reasoning_confidence": (
            reasoning_payload.get("metrics", {}).get("overall_confidence", {})
        ),
        "source_warning_count": len(reasoning_payload.get("warnings", [])),
        "source_error_count": len(reasoning_payload.get("errors", [])),
    }


def render_hypothesis_markdown(model: dict[str, Any]) -> str:
    """Render hypothesis model as Markdown."""
    lines = [
        f"# Atlas Hypothesis Engine: {model.get('subject', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', HYPOTHESIS_ENGINE_VERSION)}",
        f"**Intent:** {model.get('intent', 'unknown')}",
        f"**Scope:** {model.get('scope', 'unknown')}",
        "",
        "## Best-Supported Hypothesis",
    ]

    best = model.get("best_supported_hypothesis", {})
    if best:
        confidence = best.get("confidence", {})
        lines.append(f"**{best.get('title', 'Untitled')}**")
        lines.append("")
        lines.append(best.get("claim", ""))
        lines.append("")
        lines.append(
            f"Confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )

    lines.append("")
    lines.append("## Competing Hypotheses")

    for item in model.get("hypotheses", []):
        confidence = item.get("confidence", {})
        lines.append(f"### {item.get('title', 'Untitled')}")
        lines.append(item.get("claim", ""))
        lines.append(
            f"Confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        )

        support = item.get("supporting_evidence", [])
        if support:
            lines.append("")
            lines.append("Supporting evidence:")
            for entry in support:
                lines.append(f"- {entry}")

        counter = item.get("counter_evidence", [])
        if counter:
            lines.append("")
            lines.append("Counter-evidence / limitations:")
            for entry in counter:
                lines.append(f"- {entry}")

        tests = item.get("falsification_tests", [])
        if tests:
            lines.append("")
            lines.append("Falsification tests:")
            for test in tests:
                lines.append(f"- {test}")

        experiments = item.get("next_experiments", [])
        if experiments:
            lines.append("")
            lines.append("Next experiments:")
            for experiment in experiments:
                lines.append(f"- {experiment}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def summarize_reasoning(reasoning_payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe reasoning summary."""
    reasoning = reasoning_payload.get("data", {}).get("reasoning", {})

    return {
        "success": reasoning_payload.get("success"),
        "warnings": reasoning_payload.get("warnings", []),
        "errors": reasoning_payload.get("errors", []),
        "metrics": reasoning_payload.get("metrics", {}),
        "reasoning_subject": reasoning.get("subject"),
        "reasoning_confidence": reasoning.get("confidence", {}).get("overall", {}),
        "conclusion_count": len(reasoning.get("conclusions", [])),
        "limitation_count": len(reasoning.get("limitations", [])),
        "conflict_count": len(reasoning.get("conflicts", [])),
        "recommendation_count": len(reasoning.get("recommendations", [])),
    }


def failure_payload(
    *,
    query: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": HYPOTHESIS_ENGINE_VERSION,
        "query": query,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Resolve confidence label."""
    if score >= 0.85:
        return "high"

    if score >= 0.65:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def clamp(value: float) -> float:
    """Clamp score to 0..1."""
    return max(0.0, min(1.0, value))


def dedupe(values: list[str]) -> list[str]:
    """Dedupe values while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def json_export(data: Any) -> str:
    """Serialize hypothesis JSON."""
    return json.dumps(data, indent=2, sort_keys=True)