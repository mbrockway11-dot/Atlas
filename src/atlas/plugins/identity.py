"""Identity plugin for the Atlas core registry."""

from __future__ import annotations

from dataclasses import dataclass

from atlas.core.context import ResearchContext


@dataclass(frozen=True)
class IdentityCorePlugin:
    """Attach canonical identity metadata to ResearchContext."""

    name: str = "identity"
    order: int = 10
    depends_on: tuple[str, ...] = ()

    def execute(self, context: ResearchContext) -> ResearchContext:
        """Attach identity data to the shared context."""
        return (
            context.with_data(
                "identity",
                {
                    "profile_key": context.profile_key,
                    "display_name": context.display_name,
                    "profile_dir": context.profile_dir,
                },
            )
            .with_provenance(
                [
                    {
                        "section": "identity",
                        "source": "atlas.plugins.identity.IdentityCorePlugin",
                        "role": "Adds canonical profile identity metadata.",
                    }
                ]
            )
        )