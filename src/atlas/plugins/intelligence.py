"""Intelligence plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext
from atlas.intelligence.engine import build_intelligence_payload
from atlas.intelligence.models import IntelligenceEngineConfig


@dataclass(frozen=True)
class IntelligenceCorePlugin:
    """Attach Intelligence Engine payload to ResearchContext."""

    name: str = "intelligence"
    order: int = 50
    depends_on: tuple[str, ...] = ("identity",)

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Run Intelligence Engine and attach payload/evidence/provenance."""
        config = IntelligenceEngineConfig(**context.config)
        payload = build_intelligence_payload(
            context.profile_dir,
            config=config,
        )

        return (
            context.with_data("intelligence", payload)
            .with_evidence(payload.get("evidence", []))
            .with_provenance(payload.get("provenance", []))
        )