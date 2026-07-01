"""Temporal plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.services.temporal_service import get_temporal_section_from_path


@dataclass(frozen=True)
class TemporalCorePlugin:
    """Attach temporal section to ResearchContext."""

    name: str = "temporal"
    order: int = 25
    depends_on: tuple[str, ...] = ("research_session",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Build and attach temporal section."""
        config = IntelligenceEngineConfig(**context.config)

        temporal = get_temporal_section_from_path(
            context.profile_dir,
            transit_date=config.transit_date,
        )

        return (
            context.with_data("temporal", temporal)
            .with_provenance(
                [
                    {
                        "section": "temporal",
                        "source": "atlas.plugins.temporal.TemporalCorePlugin",
                        "role": "Extracts temporal data from the research session payload.",
                    }
                ]
            )
        )