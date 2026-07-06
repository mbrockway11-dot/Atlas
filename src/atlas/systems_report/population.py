
"""Population position section."""

from __future__ import annotations

from typing import Any


def build_population_section(payload: dict[str, Any]) -> dict[str, Any]:
    """Build population position section."""
    synthesis = payload.get("synthesis", {})
    evidence = synthesis.get("evidence", {}).get("evidence", [])

    population_evidence = [
        item for item in evidence
        if item.get("category") == "population_position"
        or str(item.get("engine", "")).startswith("population")
    ]

    return {
        "population_evidence_count": len(population_evidence),
        "strongest_themes": [
            theme for theme in synthesis.get("fusion", {}).get("themes", [])
            if theme.get("category") == "population_position"
        ],
        "evidence": population_evidence,
    }
