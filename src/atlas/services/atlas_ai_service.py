"""Atlas AI service.

Deterministic orchestration layer for Atlas services.

Atlas AI v1 is not a chatbot layer. It coordinates existing service outputs
and synthesizes an evidence-bounded executive view.
"""

from __future__ import annotations

import json
from typing import Any, Callable

from atlas.library.profile_library import list_saved_profiles
from atlas.services.evidence_service import (
    build_profile_evidence_payload,
    build_relationship_evidence_payload,
)
from atlas.services.graph_intelligence_service import (
    build_profile_graph_intelligence_payload,
    build_relationship_graph_intelligence_payload,
)
from atlas.services.narrative_intelligence_service import (
    build_profile_narrative_payload,
)
from atlas.services.profile_report_service import build_profile_report_payload
from atlas.services.relationship_report_service import build_relationship_report_payload
from atlas.services.temporal_intelligence_service import (
    build_temporal_intelligence_payload,
)


ATLAS_AI_VERSION = "1.0"

ProfileService = Callable[[str], dict[str, Any]]
RelationshipService = Callable[[str, str], dict[str, Any]]


PROFILE_SERVICE_REGISTRY: dict[str, ProfileService] = {
    "profile_report": build_profile_report_payload,
    "narrative": build_profile_narrative_payload,
    "evidence": build_profile_evidence_payload,
    "graph_intelligence": build_profile_graph_intelligence_payload,
    "temporal": build_temporal_intelligence_payload,
}


RELATIONSHIP_SERVICE_REGISTRY: dict[str, RelationshipService] = {
    "relationship_report": build_relationship_report_payload,
    "relationship_evidence": build_relationship_evidence_payload,
    "relationship_graph_intelligence": build_relationship_graph_intelligence_payload,
}


DEFAULT_PROFILE_SERVICES = [
    "profile_report",
    "narrative",
    "evidence",
    "graph_intelligence",
    "temporal",
]

DEFAULT_RELATIONSHIP_SERVICES = [
    "relationship_report",
    "relationship_evidence",
    "relationship_graph_intelligence",
]


def list_atlas_ai_profiles() -> list[str]:
    """Return profiles available to Atlas AI."""
    return list_saved_profiles()


def build_profile_ai_payload(
    profile_key: str,
    *,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Build Atlas AI profile orchestration payload."""
    selected_services = services or DEFAULT_PROFILE_SERVICES
    service_outputs = run_profile_services(profile_key, selected_services)

    synthesis = synthesize_profile_ai(
        profile_key=profile_key,
        service_outputs=service_outputs,
    )

    return {
        "success": synthesis.get("success", False),
        "version": ATLAS_AI_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "services_requested": selected_services,
        "errors": collect_service_errors(service_outputs),
        "warnings": collect_service_warnings(service_outputs),
        "data": {
            "synthesis": synthesis,
            "services": service_outputs,
        },
        "exports": {
            "ai_json": synthesis,
            "markdown": render_ai_markdown(synthesis),
        },
        "metrics": build_ai_metrics(synthesis, service_outputs),
    }


def build_relationship_ai_payload(
    profile_a: str,
    profile_b: str,
    *,
    services: list[str] | None = None,
) -> dict[str, Any]:
    """Build Atlas AI relationship orchestration payload."""
    selected_services = services or DEFAULT_RELATIONSHIP_SERVICES
    service_outputs = run_relationship_services(profile_a, profile_b, selected_services)

    synthesis = synthesize_relationship_ai(
        profile_a=profile_a,
        profile_b=profile_b,
        service_outputs=service_outputs,
    )

    return {
        "success": synthesis.get("success", False),
        "version": ATLAS_AI_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "services_requested": selected_services,
        "errors": collect_service_errors(service_outputs),
        "warnings": collect_service_warnings(service_outputs),
        "data": {
            "synthesis": synthesis,
            "services": service_outputs,
        },
        "exports": {
            "ai_json": synthesis,
            "markdown": render_ai_markdown(synthesis),
        },
        "metrics": build_ai_metrics(synthesis, service_outputs),
    }


def run_profile_services(
    profile_key: str,
    service_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Run selected profile services."""
    outputs: dict[str, dict[str, Any]] = {}

    for service_name in service_names:
        service = PROFILE_SERVICE_REGISTRY.get(service_name)

        if service is None:
            outputs[service_name] = missing_service_payload(service_name)
            continue

        try:
            outputs[service_name] = service(profile_key)
        except Exception as exc:  # noqa: BLE001
            outputs[service_name] = exception_payload(service_name, exc)

    return outputs


def run_relationship_services(
    profile_a: str,
    profile_b: str,
    service_names: list[str],
) -> dict[str, dict[str, Any]]:
    """Run selected relationship services."""
    outputs: dict[str, dict[str, Any]] = {}

    for service_name in service_names:
        service = RELATIONSHIP_SERVICE_REGISTRY.get(service_name)

        if service is None:
            outputs[service_name] = missing_service_payload(service_name)
            continue

        try:
            outputs[service_name] = service(profile_a, profile_b)
        except Exception as exc:  # noqa: BLE001
            outputs[service_name] = exception_payload(service_name, exc)

    return outputs


def synthesize_profile_ai(
    *,
    profile_key: str,
    service_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Synthesize profile-level Atlas AI output."""
    confidence = fuse_service_confidence(service_outputs)
    successes = count_successes(service_outputs)

    strengths = extract_profile_strengths(service_outputs)
    risks = extract_profile_risks(service_outputs)
    priorities = extract_profile_priorities(service_outputs)

    return {
        "success": successes > 0,
        "version": ATLAS_AI_VERSION,
        "scope": "profile",
        "subject": profile_key,
        "executive_summary": (
            f"Atlas AI synthesized {successes} successful service output(s) for "
            f"{profile_key}. The current synthesis carries "
            f"{confidence.get('overall', {}).get('label', 'unknown')} confidence."
        ),
        "confidence": confidence,
        "strengths": strengths,
        "risks": risks,
        "research_priorities": priorities,
        "service_summary": summarize_services(service_outputs),
    }


def synthesize_relationship_ai(
    *,
    profile_a: str,
    profile_b: str,
    service_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Synthesize relationship-level Atlas AI output."""
    confidence = fuse_service_confidence(service_outputs)
    successes = count_successes(service_outputs)

    strengths = extract_relationship_strengths(service_outputs)
    risks = extract_relationship_risks(service_outputs)
    priorities = extract_relationship_priorities(service_outputs)

    return {
        "success": successes > 0,
        "version": ATLAS_AI_VERSION,
        "scope": "relationship",
        "subject": f"{profile_a} ↔ {profile_b}",
        "executive_summary": (
            f"Atlas AI synthesized {successes} successful relationship service "
            f"output(s) for {profile_a} and {profile_b}. The current synthesis "
            f"carries {confidence.get('overall', {}).get('label', 'unknown')} confidence."
        ),
        "confidence": confidence,
        "strengths": strengths,
        "risks": risks,
        "research_priorities": priorities,
        "service_summary": summarize_services(service_outputs),
    }


def extract_profile_strengths(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract profile strengths from service outputs."""
    strengths: list[str] = []

    profile_metrics = service_outputs.get("profile_report", {}).get("metrics", {})
    narrative_metrics = service_outputs.get("narrative", {}).get("metrics", {})
    graph_metrics = service_outputs.get("graph_intelligence", {}).get("metrics", {})

    if profile_metrics.get("has_temporal"):
        strengths.append("Temporal layer is available.")

    if profile_metrics.get("has_graph"):
        strengths.append("Graph layer is available.")

    if narrative_metrics.get("claim_count", 0) > 0:
        strengths.append(
            f"Narrative layer produced {narrative_metrics.get('claim_count')} claims."
        )

    if graph_metrics.get("overall_confidence", {}).get("label") in {"high", "moderate"}:
        strengths.append("Graph intelligence is strong enough for synthesis.")

    return strengths or ["No major profile strengths were surfaced by Atlas AI v1."]


def extract_profile_risks(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract profile risks from service outputs."""
    risks = collect_service_warnings(service_outputs)

    graph_confidence = (
        service_outputs.get("graph_intelligence", {})
        .get("metrics", {})
        .get("overall_confidence", {})
    )

    if graph_confidence.get("label") in {"limited", "low"}:
        risks.append("Graph intelligence confidence is limited.")

    return risks or ["No major profile risks were surfaced by Atlas AI v1."]


def extract_profile_priorities(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract profile research priorities."""
    graph_intelligence = (
        service_outputs.get("graph_intelligence", {})
        .get("data", {})
        .get("intelligence", {})
    )

    priorities = collect_priorities_from_intelligence(graph_intelligence)

    if not priorities:
        priorities = [
            "Review Evidence Explorer for claim-level support.",
            "Compare this profile against population neighbors.",
            "Inspect graph intelligence before making topology-heavy claims.",
        ]

    return priorities


def extract_relationship_strengths(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract relationship strengths."""
    strengths: list[str] = []

    relationship_metrics = service_outputs.get("relationship_report", {}).get("metrics", {})

    if relationship_metrics.get("profile_a_temporal") and relationship_metrics.get("profile_b_temporal"):
        strengths.append("Both profiles have temporal layers available.")

    if relationship_metrics.get("profile_a_graph") and relationship_metrics.get("profile_b_graph"):
        strengths.append("Both profiles have graph layers available.")

    if relationship_metrics.get("morphology_class"):
        strengths.append(
            f"Morphology class is {relationship_metrics.get('morphology_class')}."
        )

    return strengths or ["No major relationship strengths were surfaced by Atlas AI v1."]


def extract_relationship_risks(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract relationship risks."""
    risks = collect_service_warnings(service_outputs)

    relationship_metrics = service_outputs.get("relationship_report", {}).get("metrics", {})
    similarity = safe_float(relationship_metrics.get("morphology_similarity"))

    if similarity and similarity < 0.40:
        risks.append("Relationship morphology similarity is limited.")

    graph_confidence = (
        service_outputs.get("relationship_graph_intelligence", {})
        .get("metrics", {})
        .get("overall_confidence", {})
    )

    if graph_confidence.get("label") in {"limited", "low"}:
        risks.append("Relationship graph intelligence confidence is limited.")

    return risks or ["No major relationship risks were surfaced by Atlas AI v1."]


def extract_relationship_priorities(service_outputs: dict[str, dict[str, Any]]) -> list[str]:
    """Extract relationship research priorities."""
    graph_intelligence = (
        service_outputs.get("relationship_graph_intelligence", {})
        .get("data", {})
        .get("intelligence", {})
    )

    priorities = collect_priorities_from_intelligence(graph_intelligence)

    if not priorities:
        priorities = [
            "Inspect shared nodes and shared edges.",
            "Review relationship evidence records.",
            "Compare this pair against similar profile pairs.",
        ]

    return priorities


def collect_priorities_from_intelligence(intelligence: dict[str, Any]) -> list[str]:
    """Collect priorities from intelligence sections."""
    priorities: list[str] = []

    for section in intelligence.get("sections", []):
        for priority in section.get("priorities", []):
            if priority not in priorities:
                priorities.append(priority)

    return priorities


def fuse_service_confidence(
    service_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Fuse available service confidence scores with warning-aware calibration."""
    scores: list[float] = []

    for payload in service_outputs.values():
        metrics = payload.get("metrics", {})
        score = extract_confidence_score(metrics)

        if score is not None:
            scores.append(score)

    base_score = sum(scores) / len(scores) if scores else 0.0

    warning_count = len(collect_service_warnings(service_outputs))
    error_count = len(collect_service_errors(service_outputs))
    failed_count = count_failures(service_outputs)

    warning_penalty = min(warning_count * 0.025, 0.20)
    error_penalty = min(error_count * 0.08, 0.40)
    failure_penalty = min(failed_count * 0.12, 0.48)

    low_confidence_penalty = min(
        count_low_confidence_services(service_outputs) * 0.06,
        0.24,
    )

    calibrated_score = clamp(
        base_score
        - warning_penalty
        - error_penalty
        - failure_penalty
        - low_confidence_penalty
    )

    return {
        "overall": confidence_record(calibrated_score),
        "base": confidence_record(base_score),
        "service_confidence_scores": [round(score, 4) for score in scores],
        "scored_service_count": len(scores),
        "penalties": {
            "warnings": {
                "count": warning_count,
                "penalty": round(warning_penalty, 4),
            },
            "errors": {
                "count": error_count,
                "penalty": round(error_penalty, 4),
            },
            "failures": {
                "count": failed_count,
                "penalty": round(failure_penalty, 4),
            },
            "low_confidence_services": {
                "count": count_low_confidence_services(service_outputs),
                "penalty": round(low_confidence_penalty, 4),
            },
        },
    }


def extract_confidence_score(metrics: dict[str, Any]) -> float | None:
    """Extract confidence score from service metrics."""
    confidence = metrics.get("overall_confidence")

    if isinstance(confidence, dict) and "score" in confidence:
        return safe_float(confidence.get("score"))

    if "average_confidence_percent" in metrics:
        return safe_float(metrics.get("average_confidence_percent")) / 100

    return None

def count_low_confidence_services(
    service_outputs: dict[str, dict[str, Any]],
) -> int:
    """Count services whose extracted confidence is limited or low."""
    count = 0

    for payload in service_outputs.values():
        metrics = payload.get("metrics", {})
        score = extract_confidence_score(metrics)

        if score is not None and score < 0.65:
            count += 1

    return count


def summarize_services(
    service_outputs: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    """Summarize service outputs safely."""
    summary: dict[str, dict[str, Any]] = {}

    for name, payload in service_outputs.items():
        summary[name] = {
            "success": payload.get("success", False),
            "error_count": len(payload.get("errors", [])),
            "warning_count": len(payload.get("warnings", [])),
            "metrics": payload.get("metrics", {}),
        }

    return summary


def build_ai_metrics(
    synthesis: dict[str, Any],
    service_outputs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Build Atlas AI metrics."""
    markdown = render_ai_markdown(synthesis)

    return {
        "service_count": len(service_outputs),
        "successful_services": count_successes(service_outputs),
        "failed_services": count_failures(service_outputs),
        "warning_count": len(collect_service_warnings(service_outputs)),
        "error_count": len(collect_service_errors(service_outputs)),
        "strength_count": len(synthesis.get("strengths", [])),
        "risk_count": len(synthesis.get("risks", [])),
        "priority_count": len(synthesis.get("research_priorities", [])),
        "word_count": len(markdown.split()),
        "overall_confidence": synthesis.get("confidence", {}).get("overall", {}),
    }


def render_ai_markdown(synthesis: dict[str, Any]) -> str:
    """Render Atlas AI synthesis Markdown."""
    lines = [
        f"# Atlas AI: {synthesis.get('subject', 'Unknown')}",
        "",
        f"**Version:** {synthesis.get('version', ATLAS_AI_VERSION)}",
        f"**Scope:** {synthesis.get('scope', 'unknown')}",
        "",
        "## Executive Summary",
        synthesis.get("executive_summary", ""),
        "",
        "## Confidence",
    ]

    overall = synthesis.get("confidence", {}).get("overall", {})
    lines.append(
        f"- Overall: {overall.get('label', 'unknown')} "
        f"({overall.get('percent', 0)}%)"
    )

    lines.append("")
    lines.append("## Strengths")
    for item in synthesis.get("strengths", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Risks")
    for item in synthesis.get("risks", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Research Priorities")
    for item in synthesis.get("research_priorities", []):
        lines.append(f"- {item}")

    lines.append("")
    lines.append("## Service Summary")

    for name, summary in synthesis.get("service_summary", {}).items():
        lines.append(
            f"- {name}: success={summary.get('success')} "
            f"errors={summary.get('error_count')} "
            f"warnings={summary.get('warning_count')}"
        )

    return "\n".join(lines).strip() + "\n"


def collect_service_errors(
    service_outputs: dict[str, dict[str, Any]],
) -> list[Any]:
    """Collect errors from service outputs."""
    errors: list[Any] = []

    for name, payload in service_outputs.items():
        for error in payload.get("errors", []):
            errors.append({"service": name, "error": error})

    return errors


def collect_service_warnings(
    service_outputs: dict[str, dict[str, Any]],
) -> list[str]:
    """Collect warnings from service outputs."""
    warnings: list[str] = []

    for name, payload in service_outputs.items():
        for warning in payload.get("warnings", []):
            text = f"{name}: {warning}"
            if text not in warnings:
                warnings.append(text)

    return warnings


def count_successes(service_outputs: dict[str, dict[str, Any]]) -> int:
    """Count successful services."""
    return sum(1 for payload in service_outputs.values() if payload.get("success"))


def count_failures(service_outputs: dict[str, dict[str, Any]]) -> int:
    """Count failed services."""
    return sum(1 for payload in service_outputs.values() if not payload.get("success"))


def missing_service_payload(service_name: str) -> dict[str, Any]:
    """Build payload for unknown service."""
    return {
        "success": False,
        "errors": [f"Unknown Atlas AI service: {service_name}"],
        "warnings": [],
        "data": {},
        "exports": {},
        "metrics": {},
    }


def exception_payload(service_name: str, exc: Exception) -> dict[str, Any]:
    """Build payload for service exception."""
    return {
        "success": False,
        "errors": [f"{service_name} failed: {exc}"],
        "warnings": [],
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
    """Clamp value to 0..1."""
    return max(0.0, min(1.0, value))


def json_export(data: Any) -> str:
    """Serialize Atlas AI JSON."""
    return json.dumps(data, indent=2, sort_keys=True)