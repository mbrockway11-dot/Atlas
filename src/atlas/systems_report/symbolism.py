
"""Symbolic architecture section."""

from __future__ import annotations

from typing import Any


SYMBOLIC_ENGINES = ("gematria", "numerology", "astrology", "kamea")


def build_symbolism_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build symbolic architecture section."""
    evidence = payload.get("synthesis", {}).get("evidence", {}).get("evidence", [])

    symbolic = [
        item for item in evidence
        if str(item.get("engine", "")).split(".")[0] in SYMBOLIC_ENGINES
    ]

    return {
        "symbolic_evidence_count": len(symbolic),
        "engines": sorted({str(item.get("engine", "")).split(".")[0] for item in symbolic}),
        "evidence": symbolic,
    }
