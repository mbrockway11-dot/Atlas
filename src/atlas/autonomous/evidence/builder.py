
"""Evidence builder."""

from __future__ import annotations

from typing import Any

from atlas.autonomous.evidence.models import EvidenceRecord, evidence_to_dict


def build_evidence_from_discovery(discovery_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build standardized evidence records from Discovery Engine output."""
    records = []

    for scan in discovery_report.get("correlation_scans", []) or []:
        records.append(
            evidence_to_dict(
                EvidenceRecord(
                    evidence_id=f"evidence::discovery::{scan.get('question_id')}",
                    source_engine="discovery",
                    question=str(scan.get("question", "")),
                    observation=build_observation(scan),
                    variables=[str(scan.get("x_field")), str(scan.get("y_field"))],
                    sample_size=int(scan.get("sample_size") or 0),
                    confidence=confidence_from_scan(scan),
                    effect_size=abs(float(scan.get("correlation") or 0.0)),
                    status="active" if scan.get("strength") not in {"minimal", "insufficient_sample"} else "weak",
                    metadata={
                        "correlation": scan.get("correlation"),
                        "strength": scan.get("strength"),
                        "direction": scan.get("direction"),
                    },
                )
            )
        )

    return records


def build_evidence_from_causality(causal_report: dict[str, Any]) -> list[dict[str, Any]]:
    """Build standardized evidence records from Causal Hypothesis Engine output."""
    records = []

    for item in causal_report.get("causal_hypotheses", []) or []:
        records.append(
            evidence_to_dict(
                EvidenceRecord(
                    evidence_id=f"evidence::causality::{item.get('candidate_id')}",
                    source_engine="causality",
                    question=str(item.get("claim", "")),
                    observation=str(item.get("mechanism", "")),
                    variables=[str(item.get("cause")), str(item.get("effect"))],
                    sample_size=int(item.get("sample_size") or 0),
                    confidence=float(item.get("causal_confidence") or 0.0),
                    effect_size=abs(float(item.get("correlation") or 0.0)),
                    status="active" if item.get("causal_label") != "unsupported_causal_candidate" else "weak",
                    metadata={
                        "candidate_id": item.get("candidate_id"),
                        "causal_label": item.get("causal_label"),
                        "direction": item.get("direction"),
                        "caution": item.get("caution"),
                    },
                )
            )
        )

    return records


def build_observation(scan: dict[str, Any]) -> str:
    """Build observation text from scan."""
    return (
        f"{scan.get('x_field')} and {scan.get('y_field')} showed "
        f"{scan.get('strength')} {scan.get('direction')} association "
        f"with correlation {scan.get('correlation')}."
    )


def confidence_from_scan(scan: dict[str, Any]) -> float:
    """Convert scan strength into confidence."""
    base = {
        "strong": 0.80,
        "moderate": 0.62,
        "weak": 0.42,
        "minimal": 0.15,
        "insufficient_sample": 0.05,
    }.get(scan.get("strength"), 0.10)

    sample_bonus = min(0.15, int(scan.get("sample_size") or 0) / 1000)

    return round(min(0.95, base + sample_bonus), 6)
