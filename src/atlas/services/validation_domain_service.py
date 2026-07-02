"""Atlas Validation Domain service.

Public service wrapper around the Atlas validation framework.

This service:
- builds canonical context
- runs registered validation domains
- runs cross-domain synthesis
- returns a service-compatible payload

It does not construct or mutate canonical structure.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.graph_intelligence_service import (
    build_profile_graph_intelligence_payload,
)
from atlas.services.profile_report_service import build_profile_report_payload
from atlas.validation.base import ValidationContext
from atlas.validation.cross_domain_engine import build_cross_domain_payload
from atlas.validation.registry import get_default_validation_registry


VALIDATION_DOMAIN_SERVICE_VERSION = "2.0"


def list_validation_profiles() -> list[str]:
    """Return profiles available for validation-domain workflows."""
    return list_saved_profiles()


def build_validation_domain_payload(
    profile_key: str,
    *,
    domains: list[str] | None = None,
) -> dict[str, Any]:
    """Build validation-domain payload for one profile."""
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

    context = ValidationContext(
        profile_key=profile_key,
        canonical_summary=canonical_summary,
        profile_payload=profile_payload,
        graph_payload=graph_payload,
        metadata={
            "service_version": VALIDATION_DOMAIN_SERVICE_VERSION,
            "domains_requested": domains,
        },
    )

    registry = get_default_validation_registry()
    results = registry.validate(context, domains=domains)

    cross_domain_payload = build_cross_domain_payload(
        results,
        profile_key=profile_key,
    )

    model = {
        "version": VALIDATION_DOMAIN_SERVICE_VERSION,
        "profile_key": profile_key,
        "definition": (
            "Validation domains compare the Canonical Structural Model against "
            "independent observations. The service delegates domain execution to "
            "the validation registry and delegates synthesis to the cross-domain "
            "engine."
        ),
        "canonical_summary": canonical_summary,
        "registry": registry.to_dict(),
        "domains_requested": domains or registry.names(enabled_only=True),
        "domain_results": [result.to_dict() for result in results],
        "cross_domain": cross_domain_payload.get("data", {}).get(
            "cross_domain_model",
            {},
        ),
    }

    return {
        "success": True,
        "version": VALIDATION_DOMAIN_SERVICE_VERSION,
        "profile_key": profile_key,
        "errors": collect_errors(
            source_payloads=[profile_payload, graph_payload],
            cross_domain_payload=cross_domain_payload,
        ),
        "warnings": collect_warnings(
            source_payloads=[profile_payload, graph_payload],
            cross_domain_payload=cross_domain_payload,
        ),
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
            "has_temporal": profile_metrics.get("has_temporal"),
            "has_graph": profile_metrics.get("has_graph"),
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

    if profile_metrics.get("has_graph") or profile_metrics.get("graph"):
        claims.append(
            {
                "claim_id": "canonical_graph_available",
                "claim": "Canonical graph structure is available for validation.",
                "layer": "canonical_structure",
                "expected_validation": (
                    "Independent domains may be compared against graph-derived "
                    "observations."
                ),
            }
        )

    if profile_metrics.get("has_temporal") or profile_metrics.get("temporal"):
        claims.append(
            {
                "claim_id": "temporal_layer_available",
                "claim": (
                    "Temporal layer is available as an independent validation input."
                ),
                "layer": "observed_reality",
                "expected_validation": (
                    "Temporal and Vedic-derived observations may be compared "
                    "with structural observations."
                ),
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
                    "Validation domains may support, conflict with, or leave this "
                    "confidence unresolved, but may not overwrite canonical structure."
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


def build_validation_metrics(model: dict[str, Any]) -> dict[str, Any]:
    """Build validation-domain service metrics."""
    cross_domain = model.get("cross_domain", {})
    signal_counts = cross_domain.get("signal_counts", {})
    markdown = render_validation_markdown(model)

    return {
        "domain_count": cross_domain.get("domain_count", 0),
        "successful_domains": cross_domain.get("successful_domain_count", 0),
        "failed_domains": cross_domain.get("failed_domain_count", 0),
        "agreement_signal_count": signal_counts.get("agreement", 0),
        "conflict_signal_count": signal_counts.get("conflict", 0),
        "unknown_signal_count": signal_counts.get("unknown", 0),
        "scientific_confidence": cross_domain.get("scientific_confidence", {}),
        "overall_confidence": cross_domain.get("scientific_confidence", {}),
        "consensus_label": cross_domain.get("consensus", {}).get("consensus_label"),
        "tension_label": cross_domain.get("tension", {}).get("tension_label"),
        "canonical_claim_count": len(
            model.get("canonical_summary", {}).get("canonical_claims", [])
        ),
        "registry_domain_count": model.get("registry", {}).get("domain_count", 0),
        "word_count": len(markdown.split()),
    }


def render_validation_markdown(model: dict[str, Any]) -> str:
    """Render validation model as Markdown."""
    cross_domain = model.get("cross_domain", {})
    confidence = cross_domain.get("scientific_confidence", {})
    consensus = cross_domain.get("consensus", {})
    tension = cross_domain.get("tension", {})
    signal_counts = cross_domain.get("signal_counts", {})

    lines = [
        f"# Atlas Validation Domains: {model.get('profile_key', 'Unknown')}",
        "",
        f"**Version:** {model.get('version', VALIDATION_DOMAIN_SERVICE_VERSION)}",
        "",
        "## Definition",
        model.get("definition", ""),
        "",
        "## Cross-Domain Summary",
        f"- Domains: {cross_domain.get('domain_count', 0)}",
        f"- Successful domains: {cross_domain.get('successful_domain_count', 0)}",
        f"- Failed domains: {cross_domain.get('failed_domain_count', 0)}",
        f"- Agreement signals: {signal_counts.get('agreement', 0)}",
        f"- Conflict signals: {signal_counts.get('conflict', 0)}",
        f"- Unknown signals: {signal_counts.get('unknown', 0)}",
        (
            f"- Scientific confidence: {confidence.get('percent', 0)}% "
            f"{confidence.get('label', 'unknown')}"
        ),
        f"- Consensus: {consensus.get('consensus_label', 'unknown')}",
        f"- Tension: {tension.get('tension_label', 'unknown')}",
        "",
        "## Canonical Claims",
    ]

    for claim in model.get("canonical_summary", {}).get("canonical_claims", []):
        lines.append(f"- **{claim.get('claim_id', 'claim')}**: {claim.get('claim', '')}")

    lines.append("")
    lines.append("## Domain Results")

    for result in model.get("domain_results", []):
        score = result.get("agreement_score", {})
        confidence = result.get("confidence", {})

        lines.extend(
            [
                f"### {result.get('domain', 'unknown')}",
                f"- Success: {result.get('success')}",
                (
                    f"- Agreement score: {score.get('percent', 0)}% "
                    f"{score.get('label', 'unknown')}"
                ),
                (
                    f"- Domain confidence: {confidence.get('percent', 0)}% "
                    f"{confidence.get('label', 'unknown')}"
                ),
                f"- Interpretation: {result.get('interpretation', '')}",
                "",
            ]
        )

    lines.append("## Recommended Follow-up")

    for item in cross_domain.get("recommended_followup", []):
        lines.append(f"- {item}")

    return "\n".join(lines).strip() + "\n"


def collect_errors(
    *,
    source_payloads: list[dict[str, Any]],
    cross_domain_payload: dict[str, Any],
) -> list[Any]:
    """Collect errors from source payloads and cross-domain payload."""
    errors: list[Any] = []

    for payload in source_payloads:
        errors.extend(payload.get("errors", []))

    errors.extend(cross_domain_payload.get("errors", []))

    return errors


def collect_warnings(
    *,
    source_payloads: list[dict[str, Any]],
    cross_domain_payload: dict[str, Any],
) -> list[str]:
    """Collect warnings from source payloads and cross-domain payload."""
    warnings: list[str] = []

    for payload in source_payloads:
        for warning in payload.get("warnings", []):
            text = str(warning)
            if text not in warnings:
                warnings.append(text)

    for warning in cross_domain_payload.get("warnings", []):
        text = str(warning)
        if text not in warnings:
            warnings.append(text)

    return warnings


def safe_call(name: str, fn) -> dict[str, Any]:
    """Safely execute a source service call."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001
        return {
            "success": False,
            "version": VALIDATION_DOMAIN_SERVICE_VERSION,
            "errors": [f"{name} failed: {exc}"],
            "warnings": [],
            "data": {},
            "exports": {},
            "metrics": {},
        }


def json_export(data: Any) -> str:
    """Serialize validation-domain JSON."""
    return json.dumps(data, indent=2, sort_keys=True)