"""Plugin protocol and built-in plugins for Atlas Intelligence."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from atlas.intelligence.engine import build_intelligence_payload
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.intelligence.profile import AtlasProfile


@dataclass(frozen=True)
class PipelineContext:
    """Context shared by intelligence plugins."""

    config: IntelligenceEngineConfig


class IntelligencePlugin(Protocol):
    """Protocol for Atlas Intelligence pipeline plugins."""

    name: str
    order: int

    def execute(self, profile: AtlasProfile, context: PipelineContext) -> AtlasProfile:
        """Execute plugin and return updated AtlasProfile."""


@dataclass(frozen=True)
class IdentityPlugin:
    """Attach basic identity metadata."""

    name: str = "identity"
    order: int = 10

    def execute(self, profile: AtlasProfile, context: PipelineContext) -> AtlasProfile:
        """Attach identity section."""
        return (
            profile.with_section(
                "identity",
                {
                    "profile_key": profile.profile_key,
                    "display_name": profile.display_name,
                    "profile_dir": profile.profile_dir,
                },
            )
            .with_provenance(
                [
                    {
                        "section": "identity",
                        "source": "atlas.intelligence.plugins.IdentityPlugin",
                        "role": "Adds canonical profile identity metadata.",
                    }
                ]
            )
        )


@dataclass(frozen=True)
class IntelligenceEnginePlugin:
    """Attach current Intelligence Engine payload."""

    name: str = "intelligence"
    order: int = 50

    def execute(self, profile: AtlasProfile, context: PipelineContext) -> AtlasProfile:
        """Run existing Intelligence Engine and attach its payload."""
        payload = build_intelligence_payload(
            profile.profile_dir,
            config=context.config,
        )

        evidence = payload.get("evidence", [])
        provenance = payload.get("provenance", [])

        return (
            profile.with_section("intelligence", payload)
            .with_evidence(evidence)
            .with_provenance(provenance)
        )


def default_plugins() -> list[IntelligencePlugin]:
    """Return default deterministic plugin registry."""
    return [
        IdentityPlugin(),
        IntelligenceEnginePlugin(),
    ]