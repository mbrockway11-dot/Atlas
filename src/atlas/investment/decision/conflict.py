
"""Decision conflict resolution."""

from __future__ import annotations


def resolve_conflict(evidence: dict) -> dict:
    long_evidence = float(evidence.get("long_evidence") or 0.0)
    short_evidence = float(evidence.get("short_evidence") or 0.0)
    flat_evidence = float(evidence.get("flat_evidence") or 0.0)

    total = long_evidence + short_evidence + flat_evidence

    if total <= 0:
        return {
            "decision_bias": "CASH",
            "conflict_score": 0.0,
            "net_evidence": 0.0,
            "evidence_confidence": 0.0,
        }

    net = long_evidence - short_evidence
    conflict = min(long_evidence, short_evidence) / max(long_evidence, short_evidence, 1e-9)

    if abs(net) < flat_evidence:
        bias = "NEUTRAL"
    elif net > 0:
        bias = "LONG"
    elif net < 0:
        bias = "SHORT"
    else:
        bias = "CASH"

    confidence = abs(net) / total

    return {
        "decision_bias": bias,
        "conflict_score": round(float(conflict), 6),
        "net_evidence": round(float(net), 6),
        "evidence_confidence": round(float(confidence), 6),
    }
