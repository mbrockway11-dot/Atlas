"""Validation plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.services.validation_service import get_population_validation_report


@dataclass(frozen=True)
class ValidationCorePlugin:
    """Attach population validation report to ResearchContext."""

    name: str = "validation"
    order: int = 30
    depends_on: tuple[str, ...] = ("identity",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Build and attach validation section."""
        report = get_population_validation_report()

        return (
            context.with_data("validation", report)
            .with_provenance(
                [
                    {
                        "section": "validation",
                        "source": "atlas.plugins.validation.ValidationCorePlugin",
                        "role": "Adds current population validation report.",
                    }
                ]
            )
        )