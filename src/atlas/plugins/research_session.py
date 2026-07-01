"""Research Session plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.services.research_session_service import get_research_session_from_path


@dataclass(frozen=True)
class ResearchSessionCorePlugin:
    """Attach research session payload to ResearchContext."""

    name: str = "research_session"
    order: int = 20
    depends_on: tuple[str, ...] = ("identity",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Build and attach research session."""
        config = IntelligenceEngineConfig(**context.config)
        session = get_research_session_from_path(
            context.profile_dir,
            transit_date=config.transit_date,
        )

        return (
            context.with_data("research_session", session)
            .with_provenance(
                [
                    {
                        "section": "research_session",
                        "source": "atlas.plugins.research_session.ResearchSessionCorePlugin",
                        "role": "Adds canonical research session payload.",
                    }
                ]
            )
        )