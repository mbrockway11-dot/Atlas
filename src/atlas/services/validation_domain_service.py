"""Atlas Validation Domain service.

Compares the Canonical Structural Model against independent validation domains.

This service does not construct canonical structure.
It evaluates whether independent domains produce agreement, conflict, or unknown
signals relative to the canonical Kamea-derived structural model.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_intelligence_service import (
    build_profile_graph_intelligence_payload,
)
from atlas.services.profile_report_service import build_profile_report_payload
from atlas.services.vedic_behavior_service import build_vedic_behavior_payload


VALIDATION_DOMAIN_VERSION = "1.0"

DEFAULT_DOMAINS = [
    "vedic_behavior",
]


def list_validation_profiles() -> list[str]:
    """Return profiles available for validation-domain workflows."""
    return list_saved_profiles()


def build_validation_domain_payload(
    profile_key: str,
    *,
    domains: list[str] | None = None,
) -> dict[str, Any]:
    """Build validation-domain payload for one profile."""
    requested_domains = domains or DEFAULT_DOMAINS

    profile_payload = safe_call(
        "profile_report",
        lambda: build_profile_report_payload(profile_key),
    )
    graph_payload = safe_call(
        "graph_intelligence",
        lambda: build_profile_graph_intelligence_payload(profile_key),
    )

    canonical_summary = build_canonical_structure_summary(
        profile_payload=profile_payload,
        graph_payload=graph_payload,
    )

    domain_results = []

    for domain in requested_domains:
        if domain == "vedic_behavior":
            domain_results.append(
                evaluate_vedic_behavior_domain(
                    profile_key=profile_key,
                    canonical_summary=canonical_summary,
                )
            )
        else:
            domain_results.append(
                unsupported_domain_result(
                    domain=domain,
                    canonical_summary=canonical_summary,
                )
            )

    model = {
        "version": VALIDATION_DOMAIN_VERSION,
        "profile_key": profile_key,
        "definition": (
            "Validation domains compare the Canonical Structural Model against "
            "independent observations. They do not construct or modify canonical "
            "structure."
        ),
        "canonical_summary": canonical_summary,
        "domains_requested": requested_domains,
        "domain_results": domain_results,
        "validation_summary": build_validation_summary(domain_results),
    }

    return {
        "success": True,
        "version": VALIDATION_DOMAIN_VERSION,
        "profile_key": profile_key,
        "errors": collect_errors([profile_payload, graph_payload], domain_results),
        "warnings": collect_warnings([profile_payload, graph_payload], domain_results),
        "data": {
            "validation_model": model,
        },
        "exports": {
            "validation_json": model,
            "markdown": render_validation_markdown(model),
        },
        "metrics": build_validation_metrics(model),
    }


def build_canonical_structure_summary(
    *,
    profile_payload: dict[str, Any],
    graph_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build compact canonical-structure summary."""
    profile_metrics = profile_payload.get("metrics", {})
    graph_metrics = graph_payload.get("metrics", {})

    return {
        "source": "canonical_structural_model",
        "profile_report_success": profile_payload.get("success", False),
        "graph_intelligence_success": graph_payload.get("success", False),
        "profile_metrics": {
            "acf": profile_metrics.get("acf"),
            "intake": profile_metrics.get("intake"),
            "temporal": profile_metrics.get("temporal"),
            "graph": profile_metrics.get("graph"),
            "missing_artifacts": profile_metrics.get("missing_artifacts", []),
        },
        "graph_metrics": {
            "section_count": graph_metrics.get("section_count", 0),
            "claim_count": graph_metrics.get("claim_count", 0),
            "evidence_count": graph_metrics.get("evidence_count", 0),
            "priority_count": graph_metrics.get("priority_count", 0),
            "overall_confidence": graph_metrics.get("overall_confidence", {}),
            "source_warnings": graph_metrics.get("source_warnings", 0),
            "source_errors": graph_metrics.get("source_errors", 0),
        },
        "canonical_claims": build_canonical_claims(
            profile_metrics=profile_metrics,
            graph_metrics=graph_metrics,
        ),
    }


def build_canonical_claims(
    *,
    profile_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build canonical structural claims to validate."""
    claims = []

    if profile_metrics.get("graph"):
        claims.append(
            {
                "claim_id": "canonical_graph_available",
                "claim": "Canonical graph structure is available for validation.",
                "layer": "canonical_structure",
                "expected_validation": "Independent domains may be compared against graph-derived observations.",
            }
        )

    if profile_metrics.get("temporal"):
        claims.append(
            {
                "claim_id": "temporal_layer_available",
                "claim": "Temporal layer is available as an independent validation domain input.",
                "layer": "observed_reality",
                "expected_validation": "Temporal and Vedic-derived observations may be compared with structural observations.",
            }
        )

    graph_confidence = graph_metrics.get("overall_confidence", {})
    if graph_confidence:
        claims.append(
            {
                "claim_id": "graph_intelligence_confidence",
                "claim": (
                    "Graph intelligence produced an interpretation confidence record."
                ),
                "layer": "interpretive_reality",
                "expected_validation": (
                    "Validation domains should not overwrite this confidence, but may "
                    "support, conflict with, or leave it unresolved."
                ),
                "confidence": graph_confidence,
            }
        )

    if not claims:
        claims.append(
            {
                "claim_id": "canonical_structure_limited",
                "claim": "Canonical structure is limited or under-resolved.",
                "layer": "canonical_structure",
                "expected_validation": "Validation should remain conservative.",
            }
        )

    return claims


def evaluate_vedic_behavior_domain(
    *,
    profile_key: str,
    canonical_summary: dict[str, Any],
) -> dict[str, Any]:
    """Evaluate Vedic Behavior as a validation domain."""
    vedic_payload = safe_call(
        "vedic_behavior",
        lambda: build_vedic_behavior_payload(profile_key),
    )
    vedic_metrics = vedic_payload
    vedic_metrics = vedic_payload.get("metrics", {})
    vedic_confidence = vedic_metrics.get("overall_confidence", {})

    agreement_signals = []
    conflict_signals = []
    unknown_signals = []

    if vedic_payload.get("success"):
        agreement_signals.append(
            "Vedic Behavior produced a bounded validation-domain payload."
        )
    else:
        conflict_signals.append("Vedic Behavior service failed.")

    if vedic_metrics.get("assumption_count", 0) > 0:
        agreement_signals.append(
            f"Vedic Behavior produced {vedic_metrics.get('assumption_count')} behavioral assumptions."
        )
    else:
        unknown_signals.append("No Vedic behavioral assumptions were produced.")

    if vedic_metrics.get("planet_count", 0) > 0:
        agreement_signals.append(
            f"Vedic layer resolved {vedic_metrics.get('planet_count')} planetary records."
        )
    else:
        unknown_signals.append("Planetary records were unavailable or unresolved.")

    if vedic_metrics.get("dasha_periods", 0) > 0:
        agreement_signals.append(
            f"Vimshottari dasha periods available: {vedic_metrics.get('dasha_periods')}."
        )
    else:
        unknown_signals.append("Dasha periods were unavailable.")

    if not vedic_metrics.get("moon_nakshatra"):
        conflict_signals.append(
            "Moon nakshatra is unresolved, limiting Vedic validation precision."
        )

    if vedic_confidence.get("label") in {"limited", "low"}:
        conflict_signals.append(
            "Vedic Behavior confidence is limited or low and should remain hypothesis-level."
        )

    canonical_claims = canonical_summary.get("canonical_claims", [])

    domain_result = {
        "domain": "vedic_behavior",
        "domain_type": "validation_domain",
        "success": vedic_payload.get("success", False),
        "definition": (
            "Vedic Behavior is treated as an independent validation domain. "
            "It evaluates whether temporal and behavioral assumptions correspond "
            "with the Canonical Structural Model without modifying that structure."
        ),
        "canonical_claims_evaluated": len(canonical_claims),
        "agreement_signals": agreement_signals,
        "conflict_signals": conflict_signals,
        "unknown_signals": unknown_signals,
        "agreement_score": build_agreement_score(
            agreement_count=len(agreement_signals),
            conflict_count=len(conflict_signals),
            unknown_count=len(unknown_signals),
            domain_confidence=vedic_confidence,
        ),
        "domain_confidence": vedic_confidence,
        "domain_metrics": vedic_metrics,
        "warnings": vedic_payload.get("warnings", []),
        "errors": vedic_payload.get("errors", []),
        "interpretation": build_domain_interpretation(
            domain="vedic_behavior",
            agreement_count=len(agreement_signals),
            conflict_count=len(conflict_signals),
            unknown_count=len(unknown_signals),
            confidence=vedic_confidence,
        ),
        "recommended_followup": build_domain_followup(
            domain="vedic_behavior",
            agreement_signals=agreement_signals,
            conflict_signals=conflict_signals,
            unknown_signals=unknown_signals,
        ),
    }

    return domain_result


def unsupported_domain_result(
    *,
    domain: str,
    canonical_summary: dict[str, Any],
) -> dict[str, Any]:
    """Build result for unsupported validation domain."""
    return {
        "domain": domain,
        "domain_type": "unsupported_validation_domain",
        "success": False,
        "definition": (
            "Requested validation domain is not currently registered with the "
            "Validation Domain service."
        ),
        "canonical_claims_evaluated": len(canonical_summary.get("canonical_claims", [])),
        "agreement_signals": [],
        "conflict_signals": [],
        "unknown_signals": [f"Unsupported validation domain: {domain}"],
        "agreement_score": confidence_record(0.0),
        "domain_confidence": confidence_record(0.0),
        "domain_metrics": {},
        "warnings": [f"Unsupported validation domain requested: {domain}"],
        "errors": [],
        "interpretation": (
            f"{domain} could not be evaluated because it is not registered."
        ),
        "recommended_followup": [
            f"Register {domain} before requesting it as a validation domain."
        ],
    }


def build_validation_summary(domain_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate validation summary."""
    successful = [item for item in domain_results if item.get("success")]
    failed = [item for item in domain_results if not item.get("success")]

    agreement_scores = [
        safe_float(item.get("agreement_score", {}).get("score"))
        for item in successful
    ]

    if agreement_scores:
        average_agreement = sum(agreement_scores) / len(agreement_scores)
    else:
        average_agreement = 0.0

    agreement_count = sum(len(item.get("agreement_signals", [])) for item in domain_results)
    conflict_count = sum(len(item.get("conflict_signals", [])) for item in domain_results)
    unknown_count = sum(len(item.get("unknown_signals", [])) for item in domain_results)

    return {
        "domain_count": len(domain_results),
        "successful_domains": len(successful),
        "failed_domains": len(failed),
        "agreement_signal_count": agreement_count,
        "conflict_signal_count": conflict_count,
        "unknown_signal_count": unknown_count,
        "average_agreement": confidence_record(average_agreement),
        "validation_readiness": validation_readiness_label(
            agreement_count=agreement_count,
            conflict_count=conflict_count,
            unknown_count=unknown_count,
            average_agreement=average_agreement,
        ),
    }


def validation_readiness_label(
    *,
    agreement_count: int,
    conflict_count: int,
    unknown_count: int,
    average_agreement: float,
) -> str:
    """Resolve validation readiness label."""
    if conflict_count == 0 and unknown_count == 0 and average_agreement >= 0.75:
        return "strong_validation_candidate"

    if average_agreement >= 0.55 and conflict_count <= agreement_count:
        return "moderate_validation_candidate"

    if unknown_count > agreement_count or conflict_count > agreement_count:
        return "limited_validation_candidate"

    return "caution"


def build_agreement_score(
    *,
    agreement_count: int,
    conflict_count: int,
    unknown_count: int,
    domain_confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build deterministic agreement score."""
    total = agreement_count + conflict_count + unknown_count

    if total == 0:
        return confidence_record(0.0)

    raw = agreement_count / total
    confidence_weight = safe_float(domain_confidence.get("score"))

    score = clamp((raw * 0.70) + (confidence_weight * 0.30))

    if conflict_count > agreement_count:
        score *= 0.75

    if unknown_count > agreement_count:
        score *= 0.85

    return confidence_record(score)


def build_domain_interpretation(
    *,
    domain: str,
    agreement_count: int,
    conflict_count: int,
    unknown_count: int,
    confidence: dict[str, Any],
) -> str:
    """Build readable domain interpretation."""
    label = confidence.get("label", "unknown")

    if agreement_count > conflict_count and agreement_count > unknown_count:
        return (
            f"{domain} provides more agreement signals than conflict or unknown "
            f"signals, but interpretation remains bounded by {label} domain confidence."
        )

    if conflict_count >= agreement_count and conflict_count > 0:
        return (
            f"{domain} currently produces meaningful conflict or limitation signals. "
            "This should be treated as a research target rather than confirmation."
        )

    if unknown_count > 0:
        return (
            f"{domain} contains unresolved information. Validation should remain "
            "conservative until missing inputs are repaired."
        )

    return f"{domain} did not produce enough information for validation."


def build_domain_followup(
    *,
    domain: str,
    agreement_signals: list[str],
    conflict_signals: list[str],
    unknown_signals: list[str],
) -> list[str]:
    """Build follow-up recommendations for a validation domain."""
    followup = []

    if domain == "vedic_behavior":
        if any("Moon nakshatra" in signal for signal in conflict_signals):
            followup.append("Resolve Moon nakshatra and rerun Vedic Behavior validation.")

        if any("confidence is limited" in signal for signal in conflict_signals):
            followup.append(
                "Keep Vedic Behavior as hypothesis-level validation until temporal inputs improve."
            )

        if unknown_signals:
            followup.append("Repair unresolved Vedic or temporal inputs before strong validation claims.")

        if agreement_signals:
            followup.append(
                "Compare Vedic agreement signals against graph intelligence claims."
            )

    if not followup:
        followup.append("Inspect validation-domain output and determine next repair action.")

    return dedupe(followup)


def collect_errors(
    source_payloads: list[dict[str, Any]],
    domain_results: list[dict[str, Any]],
) -> list[Any]:
    """Collect errors from source payloads and domain results."""
    errors = []

    for payload in source_payloads:
        errors.extend(payload.get("errors", []))

    for result in domain_results:
        errors.extend(result.get("errors", []))

    return errors


def collect_warnings(
    source_payloads: list[dict[str, Any]],
    domain_results: list[dict[str, Any]],
) -> list[str]:
    """Collect warnings from source payloads and domain results."""
    warnings = []

    for payload in source_payloads:
        for warning in payload.get("warnings", []):
            warnings.append(str(warning))

    for result in domain_results:
        for warning in result.get("warnings", []):
            warnings.append(str(warning))

    return dedupe(warnings)


def build_validation_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build validation-domain metrics."""
    domain_results = model.get("domain_results", [])
    summary = model.get("validation_summary", {})
    markdown = render_validation_markdown(model)

    return {
        "domain_count": len(domain_results),
        "successful_domains": summary.get("successful_domains", 0),
        "failed_domains": summary.get("failed_domains", 0),
        "agreement_signal_count": summary.get("agreement_signal_count", 0),
        "conflict_signal_count": summary.get("conflict_signal_count", 0),
        "unknown_signal_count": summary.get("unknown_signal_count", 0),
        "average_agreement": summary.get("average_agreement", {}),
        "validation_readiness": summary.get("validation_readiness", "unknown"),
        "canonical_claim_count": len(
            model.get("canonical_summary", {}).get("canonical_claims", [])
        ),
        "word_count": len(markdown.split()),
    }


def render_validation_markdown(model: dict[str, Any]) -> str:
    """Render validation model as Markdown."""
    lines = [
        f"# Atlas Validation Domains: {model.get('profile_key', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', VALIDATION_DOMAIN_VERSION)}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Validation Summary",
    ]

    summary = model.get("validation_summary", {})
    agreement = summary.get("average_agreement", {})

    lines.extend(
        [
            f"- Domains requested: {summary.get('domain_count', 0)}",
            f"- Successful domains: {summary.get('successful_domains', 0)}",
            f"- Failed domains: {summary.get('failed_domains', 0)}",
            f"- Agreement signals: {summary.get('agreement_signal_count', 0)}",
            f"- Conflict signals: {summary.get('conflict_signal_count', 0)}",
            f"- Unknown signals: {summary.get('unknown_signal_count', 0)}",
            (
                f"- Average agreement: {agreement.get('percent', 0)}% "
                f"{agreement.get('label', 'unknown')}"
            ),
            f"- Validation readiness: {summary.get('validation_readiness', 'unknown')}",
            "",
            "## Canonical Claims",
        ]
    )

    for claim in model.get("canonical_summary", {}).get("canonical_claims", []):
        lines.append(f"- **{claim.get('claim_id', 'claim')}**: {claim.get('claim', '')}")

    lines.append("")
    lines.append("## Domain Results")

    for result in model.get("domain_results", []):
        score = result.get("agreement_score", {})
        confidence = result.get("domain_confidence", {})

        lines.extend(
            [
                f"### {result.get('domain', 'unknown')}",
                "",
                result.get("definition", ""),
                "",
                (
                    f"Agreement score: {score.get('percent', 0)}% "
                    f"{score.get('label', 'unknown')}"
                ),
                (
                    f"Domain confidence: {confidence.get('percent', 0)}% "
                    f"{confidence.get('label', 'unknown')}"
                ),
                "",
                "Agreement signals:",
            ]
        )

        for signal in result.get("agreement_signals", []):
            lines.append(f"- {signal}")

        lines.append("")
        lines.append("Conflict signals:")

        for signal in result.get("conflict_signals", []):
            lines.append(f"- {signal}")

        lines.append("")
        lines.append("Unknown signals:")

        for signal in result.get("unknown_signals", []):
            lines.append(f"- {signal}")

        lines.append("")
        lines.append("Recommended follow-up:")

        for item in result.get("recommended_followup", []):
            lines.append(f"- {item}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def safe_call(name: str, fn) -> dict[str, Any]:
    """Safely execute a service call."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": VALIDATION_DOMAIN_VERSION,
            "errors": [f"{name} failed: {exc}"],
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
    if score >= 0.80:
        return "high"

    if score >= 0.60:
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
    """Serialize validation-domain JSON."""
    return json.dumps(data, indent=2, sort_keys=True)