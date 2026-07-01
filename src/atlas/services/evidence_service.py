"""Evidence & Explainability service.

Normalizes claims from Narrative Intelligence and Relationship Intelligence
into inspectable evidence records.

No new symbolic algorithms are introduced here.
"""

from __future__ import annotations

import json
from typing import Any

from atlas.library.profile_library import list_saved_profiles
from atlas.services.narrative_intelligence_service import (
    build_profile_narrative_payload,
)
from atlas.services.relationship_report_service import (
    build_relationship_report_payload,
)


EVIDENCE_VERSION = "1.0"


def list_evidence_profiles() -> list[str]:
    """Return profiles available for evidence inspection."""
    return list_saved_profiles()


def build_profile_evidence_payload(profile_key: str) -> dict[str, Any]:
    """Build evidence payload from Narrative Intelligence claims."""
    narrative_payload = build_profile_narrative_payload(profile_key)

    if not narrative_payload.get("success"):
        return failure_payload(
            scope="profile",
            errors=narrative_payload.get("errors", []),
            warnings=narrative_payload.get("warnings", []),
        )

    narrative = narrative_payload.get("data", {}).get("narrative", {})
    records = extract_claim_records(
        source_type="profile_narrative",
        source_label=profile_key,
        structured_payload=narrative,
    )

    return {
        "success": True,
        "version": EVIDENCE_VERSION,
        "scope": "profile",
        "profile_key": profile_key,
        "errors": narrative_payload.get("errors", []),
        "warnings": narrative_payload.get("warnings", []),
        "data": {
            "records": records,
            "source_summary": summarize_source_payload(narrative_payload),
        },
        "exports": {
            "evidence_json": records,
            "markdown": render_evidence_markdown(
                title=f"Atlas Evidence Report: {profile_key}",
                records=records,
            ),
        },
        "metrics": build_evidence_metrics(records, narrative_payload),
    }


def build_relationship_evidence_payload(
    profile_a: str,
    profile_b: str,
) -> dict[str, Any]:
    """Build evidence payload from Relationship Intelligence claims."""
    relationship_payload = build_relationship_report_payload(profile_a, profile_b)

    if not relationship_payload.get("success"):
        return failure_payload(
            scope="relationship",
            errors=relationship_payload.get("errors", []),
            warnings=relationship_payload.get("warnings", []),
        )

    structured = relationship_payload.get("data", {}).get(
        "structured_interpretation",
        {},
    )

    records = extract_claim_records(
        source_type="relationship",
        source_label=f"{profile_a}__{profile_b}",
        structured_payload=structured,
    )

    return {
        "success": True,
        "version": EVIDENCE_VERSION,
        "scope": "relationship",
        "profile_a": profile_a,
        "profile_b": profile_b,
        "errors": relationship_payload.get("errors", []),
        "warnings": relationship_payload.get("warnings", []),
        "data": {
            "records": records,
            "source_summary": summarize_source_payload(relationship_payload),
        },
        "exports": {
            "evidence_json": records,
            "markdown": render_evidence_markdown(
                title=f"Atlas Relationship Evidence: {profile_a} ↔ {profile_b}",
                records=records,
            ),
        },
        "metrics": build_evidence_metrics(records, relationship_payload),
    }


def extract_claim_records(
    *,
    source_type: str,
    source_label: str,
    structured_payload: dict[str, Any],
) -> list[dict[str, Any]]:
    """Extract normalized claim/evidence records from structured intelligence output."""
    records: list[dict[str, Any]] = []

    for section_index, section in enumerate(structured_payload.get("sections", []), start=1):
        section_title = section.get("title", f"Section {section_index}")
        section_summary = section.get("summary", "")
        section_cautions = section.get("cautions", [])

        for claim_index, claim_item in enumerate(section.get("claims", []), start=1):
            confidence = claim_item.get("confidence", {})

            records.append(
                {
                    "id": build_record_id(
                        source_type=source_type,
                        source_label=source_label,
                        section_index=section_index,
                        claim_index=claim_index,
                    ),
                    "source_type": source_type,
                    "source_label": source_label,
                    "section": section_title,
                    "section_summary": section_summary,
                    "claim": claim_item.get("claim", ""),
                    "confidence": confidence,
                    "confidence_label": confidence.get("label", "unknown"),
                    "confidence_percent": confidence.get("percent", 0),
                    "evidence": claim_item.get("evidence", []),
                    "evidence_count": len(claim_item.get("evidence", [])),
                    "cautions": section_cautions,
                    "caution_count": len(section_cautions),
                    "trace": {
                        "section_index": section_index,
                        "claim_index": claim_index,
                        "source_service": resolve_source_service(source_type),
                    },
                }
            )

    return records


def build_record_id(
    *,
    source_type: str,
    source_label: str,
    section_index: int,
    claim_index: int,
) -> str:
    """Build stable evidence record ID."""
    safe_label = "".join(
        character.lower() if character.isalnum() else "_"
        for character in source_label
    ).strip("_")

    while "__" in safe_label:
        safe_label = safe_label.replace("__", "_")

    return f"{source_type}:{safe_label}:s{section_index}:c{claim_index}"


def resolve_source_service(source_type: str) -> str:
    """Resolve source service name."""
    if source_type == "profile_narrative":
        return "atlas.services.narrative_intelligence_service"

    if source_type == "relationship":
        return "atlas.services.relationship_report_service"

    return "unknown"


def build_evidence_metrics(
    records: list[dict[str, Any]],
    source_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build evidence metrics."""
    confidence_values = [
        safe_float(record.get("confidence_percent")) for record in records
    ]

    average_confidence = (
        sum(confidence_values) / len(confidence_values)
        if confidence_values
        else 0.0
    )

    return {
        "record_count": len(records),
        "claim_count": len(records),
        "evidence_count": sum(record.get("evidence_count", 0) for record in records),
        "caution_count": sum(record.get("caution_count", 0) for record in records),
        "average_confidence_percent": round(average_confidence, 2),
        "high_confidence_claims": count_confidence_label(records, "high"),
        "moderate_confidence_claims": count_confidence_label(records, "moderate"),
        "limited_confidence_claims": count_confidence_label(records, "limited"),
        "low_confidence_claims": count_confidence_label(records, "low"),
        "source_warnings": len(source_payload.get("warnings", [])),
        "source_errors": len(source_payload.get("errors", [])),
    }


def count_confidence_label(records: list[dict[str, Any]], label: str) -> int:
    """Count records by confidence label."""
    return sum(1 for record in records if record.get("confidence_label") == label)


def summarize_source_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Build circular-safe source payload summary."""
    return {
        "success": payload.get("success"),
        "version": payload.get("version"),
        "errors": payload.get("errors", []),
        "warnings": payload.get("warnings", []),
        "metrics": payload.get("metrics", {}),
        "data_keys": sorted(list((payload.get("data") or {}).keys())),
        "export_keys": sorted(list((payload.get("exports") or {}).keys())),
    }


def render_evidence_markdown(
    *,
    title: str,
    records: list[dict[str, Any]],
) -> str:
    """Render evidence records as Markdown."""
    lines = [
        f"# {title}",
        "",
        f"**Evidence records:** {len(records)}",
        "",
    ]

    for record in records:
        lines.append(f"## {record.get('section', 'Untitled Section')}")
        lines.append(f"**Claim:** {record.get('claim', '')}")
        lines.append("")
        lines.append(
            f"**Confidence:** {record.get('confidence_label', 'unknown')} "
            f"({record.get('confidence_percent', 0)}%)"
        )
        lines.append("")

        evidence = record.get("evidence", [])
        if evidence:
            lines.append("### Evidence")
            for item in evidence:
                lines.append(f"- {item}")
            lines.append("")

        cautions = record.get("cautions", [])
        if cautions:
            lines.append("### Cautions")
            for caution in cautions:
                lines.append(f"- {caution}")
            lines.append("")

        lines.append(f"**Trace:** `{record.get('id')}`")
        lines.append("")

    return "\n".join(lines).strip() + "\n"


def failure_payload(
    *,
    scope: str,
    errors: list[Any],
    warnings: list[str],
) -> dict[str, Any]:
    """Build failure payload."""
    return {
        "success": False,
        "version": EVIDENCE_VERSION,
        "scope": scope,
        "errors": errors,
        "warnings": warnings,
        "data": {},
        "exports": {},
        "metrics": {},
    }


def safe_float(value: Any) -> float:
    """Convert value to float safely."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def json_export(data: Any) -> str:
    """Serialize evidence JSON."""
    return json.dumps(data, indent=2, sort_keys=True)