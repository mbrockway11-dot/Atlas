"""Statistics plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.services.statistical_service import (
    get_statistical_intelligence_report,
    get_statistical_profile_features,
)


@dataclass(frozen=True)
class StatisticsCorePlugin:
    """Attach statistical intelligence report to ResearchContext."""

    name: str = "statistics"
    order: int = 40
    depends_on: tuple[str, ...] = ("validation",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Build and attach statistics section."""
        profile_features = get_statistical_profile_features()
        report = get_statistical_intelligence_report(profile_features)

        return (
            context.with_data("statistics", report)
            .with_provenance(
                [
                    {
                        "section": "statistics",
                        "source": "atlas.plugins.statistics.StatisticsCorePlugin",
                        "role": "Adds current statistical intelligence report.",
                    }
                ]
            )
        )