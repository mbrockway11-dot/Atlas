"""Atlas cross-domain validation engine.

Synthesizes validation results across independent validation domains.

The Cross-Domain Engine does not run domains itself.
It consumes ValidationResult objects and evaluates agreement, conflict, unknowns,
and scientific confidence across domains.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.validation.base import (
    Confidence,
    ValidationResult,
    ValidationSignal,
)


CROSS_DOMAIN_ENGINE_VERSION = "1.0"


def build_cross_domain_payload(
    results: list[ValidationResult],
    *,
    profile_key: str = "",
) -> dict[str, Any]:
    """Build cross-domain validation payload."""
    model = build_cross_domain_model(results, profile_key=profile_key)

    return {
        "success": True,
        "version": CROSS_DOMAIN_ENGINE_VERSION,
        "profile_key": profile_key,
        "errors": collect_errors(results),
        "warnings": collect_warnings(results),
        "data": {
            "cross_domain_model": model,
        },
        "exports": {
            "cross_domain_json": model,
            "markdown": render_cross_domain_markdown(model),
        },
        "metrics": build_cross_domain_metrics(model),
    }


def build_cross_domain_model(
    results: list[ValidationResult],
    *,
    profile_key: str = "",
) -> dict[str, Any]:
    """Build cross-domain model."""
    domain_summaries = [summarize_domain_result(result) for result in results]

    agreement_signals = collect_signals(results, "agreement")
    conflict_signals = collect_signals(results, "conflict")
    unknown_signals = collect_signals(results, "unknown")

    scientific_confidence = build_scientific_confidence(results)
    consensus = build_consensus_model(results)
    tension = build_tension_model(results)
    recommendations = build_cross_domain_recommendations(
        results=results,
        consensus=consensus,
        tension=tension,
    )

    return {
        "version": CROSS_DOMAIN_ENGINE_VERSION,
        "profile_key": profile_key,
        "definition": (
            "Cross-domain validation evaluates how independent validation domains "
            "agree, conflict, or remain unresolved relative to the Canonical "
            "Structural Model."
        ),
        "domain_count": len(results),
        "successful_domain_count": sum(1 for result in results if result.success),
        "failed_domain_count": sum(1 for result in results if not result.success),
        "domain_summaries": domain_summaries,
        "signal_counts": {
            "agreement": len(agreement_signals),
            "conflict": len(conflict_signals),
            "unknown": len(unknown_signals),
        },
        "consensus": consensus,
        "tension": tension,
        "scientific_confidence": scientific_confidence.to_dict(),
        "recommended_followup": recommendations,
        "interpretation": build_cross_domain_interpretation(
            scientific_confidence=scientific_confidence,
            consensus=consensus,
            tension=tension,
            results=results,
        ),
    }


def summarize_domain_result(result: ValidationResult) -> dict[str, Any]:
    """Summarize one validation-domain result."""
    return {
        "domain": result.domain,
        "domain_type": result.domain_type,
        "version": result.version,
        "success": result.success,
        "agreement_signal_count": len(result.agreement_signals),
        "conflict_signal_count": len(result.conflict_signals),
        "unknown_signal_count": len(result.unknown_signals),
        "confidence": result.confidence.to_dict(),
        "agreement_score": result.agreement_score.to_dict(),
        "interpretation": result.interpretation,
        "recommended_followup": result.recommended_followup,
    }


def build_scientific_confidence(results: list[ValidationResult]) -> Confidence:
    """Build cross-domain scientific confidence."""
    successful = [result for result in results if result.success]

    if not successful:
        return Confidence.from_score(0.0)

    agreement_scores = [result.agreement_score.score for result in successful]
    confidence_scores = [result.confidence.score for result in successful]

    average_agreement = sum(agreement_scores) / len(agreement_scores)
    average_confidence = sum(confidence_scores) / len(confidence_scores)

    agreement_count = sum(len(result.agreement_signals) for result in results)
    conflict_count = sum(len(result.conflict_signals) for result in results)
    unknown_count = sum(len(result.unknown_signals) for result in results)

    total_signals = agreement_count + conflict_count + unknown_count
    signal_ratio = agreement_count / total_signals if total_signals else 0.0

    domain_coverage = len(successful) / len(results) if results else 0.0

    score = (
        average_agreement * 0.35
        + average_confidence * 0.25
        + signal_ratio * 0.25
        + domain_coverage * 0.15
    )

    if conflict_count > agreement_count:
        score *= 0.80

    if unknown_count > agreement_count:
        score *= 0.90

    return Confidence.from_score(score)


def build_consensus_model(results: list[ValidationResult]) -> dict[str, Any]:
    """Build consensus model across domains."""
    successful = [result for result in results if result.success]

    agreement_domains = [
        result.domain
        for result in successful
        if len(result.agreement_signals)
        > max(len(result.conflict_signals), len(result.unknown_signals))
    ]

    conflict_domains = [
        result.domain
        for result in successful
        if len(result.conflict_signals) >= len(result.agreement_signals)
        and len(result.conflict_signals) > 0
    ]

    unknown_domains = [
        result.domain
        for result in successful
        if len(result.unknown_signals) > len(result.agreement_signals)
    ]

    score = len(agreement_domains) / len(successful) if successful else 0.0

    return {
        "agreement_domains": agreement_domains,
        "conflict_domains": conflict_domains,
        "unknown_domains": unknown_domains,
        "consensus_score": Confidence.from_score(score).to_dict(),
        "consensus_label": consensus_label(score),
    }


def build_tension_model(results: list[ValidationResult]) -> dict[str, Any]:
    """Build cross-domain tension model."""
    agreement_count = sum(len(result.agreement_signals) for result in results)
    conflict_count = sum(len(result.conflict_signals) for result in results)
    unknown_count = sum(len(result.unknown_signals) for result in results)

    total = agreement_count + conflict_count + unknown_count

    if total <= 0:
        tension_score = 0.0
    else:
        tension_score = (conflict_count + unknown_count * 0.5) / total

    return {
        "tension_score": Confidence.from_score(tension_score).to_dict(),
        "tension_label": tension_label(tension_score),
        "agreement_signal_count": agreement_count,
        "conflict_signal_count": conflict_count,
        "unknown_signal_count": unknown_count,
    }


def build_cross_domain_recommendations(
    *,
    results: list[ValidationResult],
    consensus: dict[str, Any],
    tension: dict[str, Any],
) -> list[str]:
    """Build cross-domain follow-up recommendations."""
    recommendations: list[str] = []

    if not results:
        recommendations.append("Register validation domains before cross-domain synthesis.")
        return recommendations

    if consensus.get("consensus_label") in {"strong", "moderate"}:
        recommendations.append(
            "Compare agreement signals against canonical graph intelligence claims."
        )

    if tension.get("tension_label") in {"high", "moderate"}:
        recommendations.append(
            "Prioritize conflict and unknown signals as falsification targets."
        )

    for result in results:
        for item in result.recommended_followup:
            recommendations.append(item)

    if not recommendations:
        recommendations.append("Add additional independent validation domains.")

    return dedupe(recommendations)


def build_cross_domain_interpretation(
    *,
    scientific_confidence: Confidence,
    consensus: dict[str, Any],
    tension: dict[str, Any],
    results: list[ValidationResult],
) -> str:
    """Build cross-domain interpretation."""
    if not results:
        return "No validation domains were available for cross-domain synthesis."

    return (
        "Cross-domain validation produced "
        f"{scientific_confidence.label} scientific confidence "
        f"({scientific_confidence.percent}%). Consensus is "
        f"{consensus.get('consensus_label', 'unknown')} and tension is "
        f"{tension.get('tension_label', 'unknown')}."
    )


def collect_signals(
    results: list[ValidationResult],
    signal_type: str,
) -> list[ValidationSignal]:
    """Collect signals by type."""
    signals: list[ValidationSignal] = []

    for result in results:
        if signal_type == "agreement":
            signals.extend(result.agreement_signals)
        elif signal_type == "conflict":
            signals.extend(result.conflict_signals)
        elif signal_type == "unknown":
            signals.extend(result.unknown_signals)

    return signals


def build_cross_domain_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build cross-domain metrics."""
    markdown = render_cross_domain_markdown(model)
    signal_counts = model.get("signal_counts", {})

    return {
        "domain_count": model.get("domain_count", 0),
        "successful_domain_count": model.get("successful_domain_count", 0),
        "failed_domain_count": model.get("failed_domain_count", 0),
        "agreement_signal_count": signal_counts.get("agreement", 0),
        "conflict_signal_count": signal_counts.get("conflict", 0),
        "unknown_signal_count": signal_counts.get("unknown", 0),
        "scientific_confidence": model.get("scientific_confidence", {}),
        "consensus_label": model.get("consensus", {}).get("consensus_label"),
        "tension_label": model.get("tension", {}).get("tension_label"),
        "word_count": len(markdown.split()),
    }


def render_cross_domain_markdown(model: dict[str, Any]) -> str:
    """Render cross-domain model as Markdown."""
    confidence = model.get("scientific_confidence", {})
    consensus = model.get("consensus", {})
    tension = model.get("tension", {})

    lines = [
        f"# Cross-Domain Validation: {model.get('profile_key', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', CROSS_DOMAIN_ENGINE_VERSION)}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Summary",
        f"- Domains: {model.get('domain_count', 0)}",
        f"- Successful domains: {model.get('successful_domain_count', 0)}",
        f"- Failed domains: {model.get('failed_domain_count', 0)}",
        f"- Scientific confidence: {confidence.get('percent', 0)}% {confidence.get('label', 'unknown')}",
        f"- Consensus: {consensus.get('consensus_label', 'unknown')}",
        f"- Tension: {tension.get('tension_label', 'unknown')}",
        "",
        "## Domain Summaries",
    ]

    for item in model.get("domain_summaries", []):
        score = item.get("agreement_score", {})
        lines.extend(
            [
                f"### {item.get('domain', 'unknown')}",
                f"- Success: {item.get('success')}",
                f"- Agreement score: {score.get('percent', 0)}% {score.get('label', 'unknown')}",
                f"- Interpretation: {item.get('interpretation', '')}",
                "",
            ]
        )

    lines.append("## Recommended Follow-up")

    for item in model.get("recommended_followup", []):
        lines.append(f"- {item}")

    return "\n".join(lines).strip() + "\n"


def collect_errors(results: list[ValidationResult]) -> list[Any]:
    """Collect errors from validation results."""
    errors: list[Any] = []

    for result in results:
        for error in result.errors:
            errors.append({"domain": result.domain, "error": error})

    return errors


def collect_warnings(results: list[ValidationResult]) -> list[str]:
    """Collect warnings from validation results."""
    warnings: list[str] = []

    for result in results:
        for warning in result.warnings:
            text = f"{result.domain}: {warning}"
            if text not in warnings:
                warnings.append(text)

    return warnings


def consensus_label(score: float) -> str:
    """Resolve consensus label."""
    if score >= 0.75:
        return "strong"

    if score >= 0.50:
        return "moderate"

    if score > 0:
        return "limited"

    return "none"


def tension_label(score: float) -> str:
    """Resolve tension label."""
    if score >= 0.60:
        return "high"

    if score >= 0.35:
        return "moderate"

    if score > 0:
        return "limited"

    return "none"


def dedupe(values: list[str]) -> list[str]:
    """Dedupe strings while preserving order."""
    seen = set()
    result = []

    for value in values:
        if value not in seen:
            result.append(value)
            seen.add(value)

    return result


def json_export(data: Any) -> str:
    """Serialize cross-domain data."""
    return json.dumps(data, indent=2, sort_keys=True)