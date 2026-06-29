"""Atlas Intelligence pipeline manager."""

from __future__ import annotations

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.intelligence.plugins import (
    IntelligencePlugin,
    PipelineContext,
    default_plugins,
)
from atlas.intelligence.profile import AtlasProfile


def run_intelligence_pipeline(
    profile: AtlasProfile,
    *,
    config: IntelligenceEngineConfig | None = None,
    plugins: list[IntelligencePlugin] | None = None,
) -> AtlasProfile:
    """Run a deterministic plugin pipeline over an AtlasProfile."""
    context = PipelineContext(config=config or IntelligenceEngineConfig())
    registry = plugins if plugins is not None else default_plugins()

    current = profile

    for plugin in sorted(registry, key=lambda item: (item.order, item.name)):
        try:
            current = plugin.execute(current, context)
        except Exception as exc:
            current = current.with_warning(
                f"Plugin {plugin.name} failed: {type(exc).__name__}: {exc}"
            )

    return current