"""Narrative Intelligence service v2.

This layer converts existing Atlas report outputs into richer narrative sections.

It does not introduce new symbolic algorithms.
It synthesizes existing profile report, temporal, graph, warning, and metric data
into claims, evidence, confidence, cautions, and readable Markdown.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.profile_report_service import build_profile_report_payload


NARRATIVE_VERSION = "2.0"


def list_narrative_profiles() -> list[str]:
    """Return profiles available for narrative intelligence."""
    return list_saved_profiles()


def build_profile_narrative_payload(profile_key: str) -> dict[str, Any]:
    """Build deterministic narrative intelligence payload for one profile."""
    profile_report = build_profile_report_payload(profile_key)

    if not profile_report.get("success"):
        return {
            "success": False,
            "profile_key": profile_key,
            "errors": profile_report.get("errors", []),
            "warnings": profile_report.get("warnings", []),
            "data": {},
            "exports": {},
            "metrics": {},
        }

    narrative = build_profile_narrative(profile_report)

    payload = {
        "success": True,
        "profile_key": profile_key,
        "errors": profile_report.get("errors", []),
        "warnings": profile_report.get("warnings", []),
        "data": {
            "profile_report": build_safe_profile_report_summary(profile_report),
            "narrative": narrative,
        },
        "exports": {
            "markdown": render_narrative_markdown(narrative),
            "narrative_json": narrative,
        },
        "metrics": build_narrative_metrics(profile_report, narrative),
    }

    return payload


def build_profile_narrative(profile_report: dict[str, Any]) -> dict[str, Any]:
    """Build structured narrative sections with claims and evidence."""
    profile_key = profile_report.get("profile_key", "profile")
    name = resolve_profile_name(profile_key, profile_report)

    metrics = profile_report.get("metrics", {})
    temporal_metrics = metrics.get("temporal_metrics", {})
    graph_metrics = metrics.get("graph_metrics", {})
    warnings = profile_report.get("warnings", [])
    errors = profile_report.get("errors", [])

    confidence = build_confidence_summary(
        metrics=metrics,
        temporal_metrics=temporal_metrics,
        graph_metrics=graph_metrics,
        warnings=warnings,
        errors=errors,
    )

    sections = [
        build_executive_narrative(
            name,
            metrics,
            temporal_metrics,
            graph_metrics,
            confidence,
        ),
        build_identity_pattern(
            name,
            metrics,
            temporal_metrics,
            graph_metrics,
            confidence,
        ),
        build_temporal_pattern(
            name,
            temporal_metrics,
            confidence,
        ),
        build_topology_pattern(
            name,
            graph_metrics,
            confidence,
        ),
        build_strengths_section(
            name,
            temporal_metrics,
            graph_metrics,
            confidence,
        ),
        build_blind_spots_section(
            name,
            temporal_metrics,
            graph_metrics,
            warnings,
            confidence,
        ),
        build_integrated_synthesis(
            name,
            metrics,
            temporal_metrics,
            graph_metrics,
            warnings,
            confidence,
        ),
        build_research_cautions_section(
            warnings,
            errors,
            confidence,
        ),
    ]

    return {
        "version": NARRATIVE_VERSION,
        "name": name,
        "profile_key": profile_key,
        "confidence": confidence,
        "sections": sections,
        "summary": {
            "section_count": len(sections),
            "claim_count": count_claims(sections),
            "evidence_count": count_evidence(sections),
            "has_temporal": metrics.get("has_temporal", False),
            "has_graph": metrics.get("has_graph", False),
            "warning_count": len(warnings),
            "error_count": len(errors),
            "overall_confidence": confidence.get("overall", {}).get("score", 0.0),
            "overall_confidence_label": confidence.get("overall", {}).get("label", "unknown"),
        },
    }


def build_confidence_summary(
    *,
    metrics: dict[str, Any],
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    warnings: list[str],
    errors: list[Any],
) -> dict[str, Any]:
    """Build deterministic confidence summary."""
    identity_score = confidence_from_booleans(
        [
            metrics.get("has_acf", False),
            metrics.get("has_intake", False),
        ]
    )

    temporal_score = confidence_from_temporal(temporal_metrics)
    graph_score = confidence_from_graph(graph_metrics)

    warning_penalty = min(len(warnings) * 0.04, 0.24)
    error_penalty = min(len(errors) * 0.10, 0.40)

    overall = (
        identity_score * 0.30
        + temporal_score * 0.30
        + graph_score * 0.25
        + max(0.0, 1.0 - warning_penalty - error_penalty) * 0.15
    )

    overall = clamp(overall)

    return {
        "identity": confidence_record(identity_score),
        "temporal": confidence_record(temporal_score),
        "graph": confidence_record(graph_score),
        "warnings": {
            "count": len(warnings),
            "penalty": warning_penalty,
        },
        "errors": {
            "count": len(errors),
            "penalty": error_penalty,
        },
        "overall": confidence_record(overall),
    }


def confidence_from_booleans(values: list[bool]) -> float:
    """Build confidence score from boolean availability."""
    if not values:
        return 0.0

    return sum(1 for value in values if value) / len(values)


def confidence_from_temporal(temporal_metrics: dict[str, Any]) -> float:
    """Build temporal confidence from temporal layer availability."""
    if not temporal_metrics:
        return 0.0

    score = 0.0

    if temporal_metrics.get("birth_date"):
        score += 0.20

    if temporal_metrics.get("birth_place"):
        score += 0.15

    if temporal_metrics.get("birth_time") not in {"", "Unknown", None}:
        score += 0.15
    else:
        score += 0.05

    if temporal_metrics.get("planet_count", 0) > 0:
        score += 0.15

    if temporal_metrics.get("dasha_periods", 0) > 0:
        score += 0.15

    if temporal_metrics.get("transit_contacts", 0) > 0:
        score += 0.10

    if temporal_metrics.get("moon_nakshatra"):
        score += 0.10

    return clamp(score)


def confidence_from_graph(graph_metrics: dict[str, Any]) -> float:
    """Build graph confidence from graph layer availability."""
    if not graph_metrics:
        return 0.0

    score = 0.20

    if graph_metrics.get("audit_status") in {"passed", "warning"}:
        score += 0.20

    if graph_metrics.get("cig_nodes", 0) > 0:
        score += 0.20

    if graph_metrics.get("stg_nodes", 0) > 0:
        score += 0.20

    if graph_metrics.get("motif_count", 0) > 0:
        score += 0.10

    if graph_metrics.get("name"):
        score += 0.10

    return clamp(score)


def confidence_record(score: float) -> dict[str, Any]:
    """Build confidence record."""
    score = clamp(score)

    return {
        "score": round(score, 4),
        "percent": round(score * 100, 2),
        "label": confidence_label(score),
    }


def confidence_label(score: float) -> str:
    """Convert confidence score to label."""
    if score >= 0.85:
        return "high"

    if score >= 0.65:
        return "moderate"

    if score >= 0.40:
        return "limited"

    return "low"


def build_executive_narrative(
    name: str,
    metrics: dict[str, Any],
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build executive narrative section."""
    birth_date = temporal_metrics.get("birth_date", "unknown")
    birth_place = temporal_metrics.get("birth_place", "unknown")
    graph_status = graph_metrics.get("audit_status", "unknown")
    overall = confidence.get("overall", {})

    summary = (
        f"{name} is represented in Atlas as a multi-layer profile combining "
        "intake metadata, ACF structure, temporal intelligence, graph structure, "
        "and report-level interpretation. The current synthesis should be read "
        f"with {overall.get('label', 'unknown')} overall confidence."
    )

    claims = [
        claim(
            "The profile is available as a multi-layer Atlas object.",
            confidence.get("identity", {}),
            [
                f"ACF available: {metrics.get('has_acf', False)}",
                f"Intake available: {metrics.get('has_intake', False)}",
            ],
        ),
        claim(
            "Temporal intelligence can contribute to interpretation.",
            confidence.get("temporal", {}),
            [
                f"Birth date: {birth_date}",
                f"Birth place: {birth_place}",
                f"Planet count: {temporal_metrics.get('planet_count', 0)}",
            ],
        ),
        claim(
            "Graph intelligence can contribute with current confidence limits.",
            confidence.get("graph", {}),
            [
                f"Graph audit status: {graph_status}",
                f"CIG nodes: {graph_metrics.get('cig_nodes', 0)}",
                f"STG nodes: {graph_metrics.get('stg_nodes', 0)}",
            ],
        ),
    ]

    details = [
        f"Birth date: {birth_date}",
        f"Birth place: {birth_place}",
        f"Graph audit status: {graph_status}",
        f"Report sections generated: {metrics.get('section_count', 0)}",
        f"Overall confidence: {overall.get('percent', 0)}%",
    ]

    cautions = build_section_cautions(
        [
            "Confidence is reduced when profile artifacts, birth time, graph nodes, or Moon nakshatra are missing.",
        ]
    )

    return section("Executive Narrative", summary, details, claims, cautions)


def build_identity_pattern(
    name: str,
    metrics: dict[str, Any],
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build identity pattern section."""
    has_acf = metrics.get("has_acf", False)
    has_intake = metrics.get("has_intake", False)
    motif_count = graph_metrics.get("motif_count", 0)

    if has_acf and has_intake:
        grounding = "both intake metadata and ACF structure"
    elif has_acf:
        grounding = "ACF structure with limited intake metadata"
    elif has_intake:
        grounding = "intake metadata with limited ACF structure"
    else:
        grounding = "partial profile artifacts"

    summary = (
        f"{name}'s identity pattern is grounded in {grounding}. "
        "Atlas uses this identity layer as the baseline for temporal, graph, "
        "population, and narrative synthesis."
    )

    claims = [
        claim(
            "The identity layer is sufficient for baseline profile synthesis.",
            confidence.get("identity", {}),
            [
                f"ACF available: {has_acf}",
                f"Intake available: {has_intake}",
            ],
        ),
        claim(
            "Identity-stack motif interpretation is currently limited by graph metrics.",
            confidence.get("graph", {}),
            [
                f"Motif count: {motif_count}",
                f"CIG nodes: {graph_metrics.get('cig_nodes', 0)}",
                f"STG nodes: {graph_metrics.get('stg_nodes', 0)}",
            ],
        ),
    ]

    details = [
        f"ACF available: {has_acf}",
        f"Intake available: {has_intake}",
        f"Motif count: {motif_count}",
        f"Missing artifacts: {', '.join(metrics.get('missing_artifacts', [])) or 'none'}",
    ]

    cautions = build_section_cautions(
        [
            "Identity claims should remain conservative when profile interpretation or research session artifacts are missing.",
        ]
    )

    return section("Identity Pattern", summary, details, claims, cautions)


def build_temporal_pattern(
    name: str,
    temporal_metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build temporal pattern section."""
    birth_time = temporal_metrics.get("birth_time", "Unknown")
    moon_nakshatra = temporal_metrics.get("moon_nakshatra", "")
    transit_contacts = temporal_metrics.get("transit_contacts", 0)

    if moon_nakshatra:
        moon_text = (
            f"The Moon nakshatra resolves as {moon_nakshatra}, which supports "
            "more stable dasha interpretation."
        )
    else:
        moon_text = (
            "The Moon nakshatra was not resolved in the service metrics, so "
            "dasha interpretation should be treated cautiously."
        )

    summary = (
        f"{name}'s temporal pattern is available through natal, dasha, and "
        "transit layers. The strength of the interpretation depends on birth-time, "
        "coordinate, and Moon-nakshatra completeness."
    )

    claims = [
        claim(
            "Natal and transit layers are available for synthesis.",
            confidence.get("temporal", {}),
            [
                f"Planet count: {temporal_metrics.get('planet_count', 0)}",
                f"Transit contacts: {transit_contacts}",
                f"Transit aspects: {temporal_metrics.get('transit_aspects', 0)}",
            ],
        ),
        claim(
            "Dasha timing is available but may need caution.",
            confidence.get("temporal", {}),
            [
                f"Dasha periods generated: {temporal_metrics.get('dasha_periods', 0)}",
                f"Moon nakshatra: {moon_nakshatra or 'unresolved'}",
            ],
        ),
    ]

    details = [
        f"Birth time: {birth_time}",
        moon_text,
        f"Planet count: {temporal_metrics.get('planet_count', 0)}",
        f"Dasha periods generated: {temporal_metrics.get('dasha_periods', 0)}",
        f"Transit contacts: {transit_contacts}",
        f"Transit aspects: {temporal_metrics.get('transit_aspects', 0)}",
    ]

    cautions: list[str] = []

    if birth_time == "Unknown":
        cautions.append(
            "Unknown birth time reduces confidence in house, ascendant, and timing-sensitive conclusions."
        )

    if not moon_nakshatra:
        cautions.append(
            "Unresolved Moon nakshatra weakens precision in dasha-specific conclusions."
        )

    return section("Temporal Pattern", summary, details, claims, cautions)


def build_topology_pattern(
    name: str,
    graph_metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build topology pattern section."""
    cig_nodes = graph_metrics.get("cig_nodes", 0)
    stg_nodes = graph_metrics.get("stg_nodes", 0)
    audit_status = graph_metrics.get("audit_status", "unknown")

    if cig_nodes or stg_nodes:
        summary = (
            f"{name}'s topology layer contains graph structure that can support "
            "identity-stack interpretation, morphology comparison, and relationship analysis."
        )
    else:
        summary = (
            f"{name}'s topology layer is present but sparse. The graph service is online, "
            "but current node and edge metrics limit topology-specific interpretation."
        )

    claims = [
        claim(
            "Graph service output is available for this profile.",
            confidence.get("graph", {}),
            [
                f"Audit status: {audit_status}",
                f"CIG nodes: {cig_nodes}",
                f"STG nodes: {stg_nodes}",
            ],
        ),
        claim(
            "Topology-specific claims should remain conservative.",
            confidence.get("graph", {}),
            [
                f"CIG edges: {graph_metrics.get('cig_edges', 0)}",
                f"STG edges: {graph_metrics.get('stg_edges', 0)}",
                f"Motif count: {graph_metrics.get('motif_count', 0)}",
            ],
        ),
    ]

    details = [
        f"CIG nodes: {cig_nodes}",
        f"CIG edges: {graph_metrics.get('cig_edges', 0)}",
        f"STG nodes: {stg_nodes}",
        f"STG edges: {graph_metrics.get('stg_edges', 0)}",
        f"Motif count: {graph_metrics.get('motif_count', 0)}",
        f"Audit status: {audit_status}",
    ]

    cautions: list[str] = []

    if cig_nodes == 0 and stg_nodes == 0:
        cautions.append("Sparse graph structure limits strong topology interpretation.")

    return section("Topology Pattern", summary, details, claims, cautions)


def build_strengths_section(
    name: str,
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build strengths section."""
    details: list[str] = []
    claims: list[dict[str, Any]] = []

    if temporal_metrics.get("planet_count", 0):
        details.append("Temporal layer is populated enough to support natal and transit synthesis.")
        claims.append(
            claim(
                "Temporal synthesis is one of the stronger available layers.",
                confidence.get("temporal", {}),
                [
                    f"Planet count: {temporal_metrics.get('planet_count', 0)}",
                    f"Transit contacts: {temporal_metrics.get('transit_contacts', 0)}",
                ],
            )
        )

    if temporal_metrics.get("dasha_periods", 0):
        details.append("Dasha sequence is generated, allowing long-form timing interpretation.")

    if graph_metrics.get("audit_status") in {"passed", "warning"}:
        details.append("Graph layer is available for structural interpretation and morphology comparison.")
        claims.append(
            claim(
                "Graph output is usable as a secondary interpretive layer.",
                confidence.get("graph", {}),
                [
                    f"Audit status: {graph_metrics.get('audit_status')}",
                    f"Graph name: {graph_metrics.get('name', 'n/a')}",
                ],
            )
        )

    if not details:
        details.append("Strengths cannot be strongly inferred yet because available service metrics are sparse.")

    summary = (
        f"{name}'s strongest current Atlas advantage is the presence of multiple "
        "service-backed layers that can be synthesized together rather than read in isolation."
    )

    return section("Strengths", summary, details, claims, [])


def build_blind_spots_section(
    name: str,
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    warnings: list[str],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build blind spots section."""
    details: list[str] = []

    if temporal_metrics.get("birth_time", "Unknown") == "Unknown":
        details.append("Unknown birth time reduces confidence in house, ascendant, and timing-sensitive conclusions.")

    if not temporal_metrics.get("moon_nakshatra"):
        details.append("Unresolved Moon nakshatra weakens precision in dasha-based interpretation.")

    if graph_metrics.get("cig_nodes", 0) == 0:
        details.append("Sparse CIG graph limits topology-specific interpretation.")

    if warnings:
        details.append(f"{len(warnings)} warning(s) are attached to the profile report.")

    if not details:
        details.append("No major blind spots were surfaced by the current service metrics.")

    summary = (
        f"{name}'s current interpretive blind spots are not failures of the system; "
        "they are confidence boundaries created by incomplete or sparse source layers."
    )

    claims = [
        claim(
            "Interpretive boundaries are visible and should be preserved in the report.",
            confidence.get("overall", {}),
            details,
        )
    ]

    return section("Blind Spots", summary, details, claims, details)


def build_integrated_synthesis(
    name: str,
    metrics: dict[str, Any],
    temporal_metrics: dict[str, Any],
    graph_metrics: dict[str, Any],
    warnings: list[str],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build integrated cross-layer synthesis section."""
    temporal_ready = metrics.get("has_temporal", False)
    graph_ready = metrics.get("has_graph", False)
    overall = confidence.get("overall", {})

    if temporal_ready and graph_ready:
        summary = (
            f"{name} can currently be read through a combined temporal-and-graph lens. "
            "The temporal layer supplies timing and symbolic placement context, while the "
            "graph layer supplies structural comparison capacity. Because confidence is "
            f"{overall.get('label', 'unknown')}, the synthesis should emphasize evidence-backed "
            "patterns over absolute claims."
        )
    elif temporal_ready:
        summary = (
            f"{name} currently has stronger temporal support than graph support. Narrative "
            "interpretation should emphasize natal, transit, and dasha evidence."
        )
    elif graph_ready:
        summary = (
            f"{name} currently has stronger graph support than temporal support. Narrative "
            "interpretation should emphasize topology and morphology evidence."
        )
    else:
        summary = (
            f"{name} currently requires more complete source layers before strong integrated "
            "narrative synthesis is appropriate."
        )

    details = [
        f"Temporal ready: {temporal_ready}",
        f"Graph ready: {graph_ready}",
        f"Overall confidence: {overall.get('percent', 0)}%",
        f"Warnings: {len(warnings)}",
    ]

    claims = [
        claim(
            "Integrated synthesis is available but should remain evidence-bounded.",
            overall,
            details,
        )
    ]

    cautions = []

    if warnings:
        cautions.append("Warnings should be surfaced alongside narrative claims.")

    return section("Integrated Synthesis", summary, details, claims, cautions)


def build_research_cautions_section(
    warnings: list[str],
    errors: list[Any],
    confidence: dict[str, Any],
) -> dict[str, Any]:
    """Build research cautions section."""
    details: list[str] = []

    for warning in warnings:
        details.append(f"Warning: {warning}")

    for error in errors:
        details.append(f"Error: {error}")

    if not details:
        details.append("No warnings or errors were reported.")

    summary = (
        "Narrative Intelligence is deterministic and should be read as a synthesis "
        "of available Atlas outputs, not as an independent symbolic engine."
    )

    claims = [
        claim(
            "The narrative is generated from service outputs rather than a separate symbolic engine.",
            confidence.get("overall", {}),
            [
                "Source: profile_report_service",
                "Source: temporal_intelligence_service",
                "Source: graph_service",
            ],
        )
    ]

    return section("Research Cautions", summary, details, claims, details)


def render_narrative_markdown(narrative: dict[str, Any]) -> str:
    """Render narrative as Markdown."""
    lines = [
        f"# Atlas Narrative Intelligence: {narrative.get('name', 'Profile')}",
        "",
        f"**Version:** {narrative.get('version', NARRATIVE_VERSION)}",
        "",
        "## Confidence",
    ]

    confidence = narrative.get("confidence", {})
    for key in ["identity", "temporal", "graph", "overall"]:
        record = confidence.get(key, {})
        lines.append(
            f"- {key.title()}: {record.get('label', 'unknown')} "
            f"({record.get('percent', 0)}%)"
        )

    lines.append("")

    for item in narrative.get("sections", []):
        lines.append(f"## {item.get('title', 'Untitled Section')}")
        lines.append(item.get("summary", ""))

        details = item.get("details", [])
        if details:
            lines.append("")
            lines.append("### Details")
            for detail in details:
                lines.append(f"- {detail}")

        claims = item.get("claims", [])
        if claims:
            lines.append("")
            lines.append("### Claims")
            for item_claim in claims:
                confidence_record_value = item_claim.get("confidence", {})
                lines.append(
                    f"- {item_claim.get('claim', '')} "
                    f"[{confidence_record_value.get('label', 'unknown')}, "
                    f"{confidence_record_value.get('percent', 0)}%]"
                )

                evidence = item_claim.get("evidence", [])
                for evidence_item in evidence:
                    lines.append(f"  - Evidence: {evidence_item}")

        cautions = item.get("cautions", [])
        if cautions:
            lines.append("")
            lines.append("### Cautions")
            for caution in cautions:
                lines.append(f"- {caution}")

        lines.append("")

    return "\n".join(lines).strip() + "\n"


def build_narrative_metrics(
    profile_report: dict[str, Any],
    narrative: dict[str, Any],
) -> dict[str, Any]:
    """Build narrative-level metrics."""
    markdown = render_narrative_markdown(narrative)

    return {
        "section_count": len(narrative.get("sections", [])),
        "claim_count": count_claims(narrative.get("sections", [])),
        "evidence_count": count_evidence(narrative.get("sections", [])),
        "word_count": len(markdown.split()),
        "source_report_sections": profile_report.get("metrics", {}).get("section_count", 0),
        "warning_count": len(profile_report.get("warnings", [])),
        "error_count": len(profile_report.get("errors", [])),
        "overall_confidence": narrative.get("confidence", {}).get("overall", {}),
    }


def build_safe_profile_report_summary(profile_report: dict[str, Any]) -> dict[str, Any]:
    """Build safe source report summary."""
    return {
        "success": profile_report.get("success"),
        "profile_key": profile_report.get("profile_key"),
        "profile_dir": profile_report.get("profile_dir"),
        "errors": profile_report.get("errors", []),
        "warnings": profile_report.get("warnings", []),
        "metrics": profile_report.get("metrics", {}),
        "report": profile_report.get("data", {}).get("report", {}),
        "interpretation": profile_report.get("data", {}).get("interpretation", {}),
    }


def resolve_profile_name(profile_key: str, profile_report: dict[str, Any]) -> str:
    """Resolve profile display name from profile report."""
    report = profile_report.get("data", {}).get("report", {})

    if report.get("name"):
        return str(report["name"])

    graph_name = (
        profile_report.get("metrics", {})
        .get("graph_metrics", {})
        .get("name")
    )

    if graph_name:
        return str(graph_name)

    return profile_key.replace("_", " ").title()


def section(
    title: str,
    summary: str,
    details: list[str],
    claims: list[dict[str, Any]],
    cautions: list[str],
) -> dict[str, Any]:
    """Build narrative section."""
    return {
        "title": title,
        "summary": summary,
        "details": details,
        "claims": claims,
        "cautions": cautions,
    }


def claim(
    text: str,
    confidence: dict[str, Any],
    evidence: list[str],
) -> dict[str, Any]:
    """Build evidence-backed claim."""
    return {
        "claim": text,
        "confidence": confidence,
        "evidence": evidence,
    }


def build_section_cautions(cautions: list[str]) -> list[str]:
    """Return normalized cautions."""
    return [caution for caution in cautions if caution]


def count_claims(sections: list[dict[str, Any]]) -> int:
    """Count claims in narrative sections."""
    return sum(len(section_item.get("claims", [])) for section_item in sections)


def count_evidence(sections: list[dict[str, Any]]) -> int:
    """Count evidence items in narrative sections."""
    return sum(
        len(claim_item.get("evidence", []))
        for section_item in sections
        for claim_item in section_item.get("claims", [])
    )


def clamp(value: float) -> float:
    """Clamp confidence value to 0..1."""
    return max(0.0, min(1.0, value))


def json_export(data: Any) -> str:
    """Serialize narrative JSON."""
    return json.dumps(data, indent=2, sort_keys=True)