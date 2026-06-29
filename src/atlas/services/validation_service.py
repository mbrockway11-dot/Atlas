"""Validation service utilities."""

from __future__ import annotations

from atlas.research.validation import build_population_validation_report
from atlas.services.population_service import load_population_matrix


def build_current_population_validation_report() -> dict:
    """Build validation report for current profile library."""
    matrix = load_population_matrix()
    return build_population_validation_report(matrix)