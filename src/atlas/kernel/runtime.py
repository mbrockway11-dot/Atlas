"""Atlas kernel runtime.

The kernel is the orchestration boundary for dashboards, services, CLI tools,
and future APIs.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.core.context import ResearchContext
from atlas.core.manifest import load_enabled_plugins
from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.intelligence.profile import AtlasProfile
from atlas.kernel.metrics import KernelMetrics, PluginTiming, Timer
from atlas.plugins.registry import build_default_registry, default_enabled_plugins
from atlas.services.atlas_profile_service import (
    build_atlas_profile,
    build_base_atlas_profile,
)
from atlas.services.profile_service import (
    profile_dir,
    profile_exists,
    resolve_profile_display_name,
)


@dataclass(frozen=True)
class AtlasKernel:
    """Atlas orchestration kernel."""

    manifest_path: str = "plugins.yaml"

    def enabled_plugins(self) -> set[str]:
        """Return enabled plugins from manifest or defaults."""
        enabled = load_enabled_plugins(self.manifest_path)
        return enabled if enabled is not None else default_enabled_plugins()

    def build_context(
        self,
        profile_key: str,
        config: IntelligenceEngineConfig | None = None,
    ) -> ResearchContext:
        """Build a ResearchContext for a profile."""
        if not profile_exists(profile_key):
            raise FileNotFoundError(f"Profile not found: {profile_key}")

        runtime_config = config or IntelligenceEngineConfig()

        return ResearchContext(
            profile_key=profile_key,
            display_name=resolve_profile_display_name(profile_key),
            profile_dir=str(profile_dir(profile_key)),
            config=runtime_config.__dict__,
        )

    def run_context(
        self,
        context: ResearchContext,
        *,
        enabled: set[str] | None = None,
    ) -> tuple[ResearchContext, KernelMetrics]:
        """Run the core plugin pipeline and collect metrics."""
        registry = build_default_registry()
        active = enabled if enabled is not None else self.enabled_plugins()

        current = context
        total_timer = Timer()
        timings: list[PluginTiming] = []

        for plugin in registry.ordered(enabled=active):
            timer = Timer()
            before_warning_count = len(current.warnings)

            try:
                current = plugin.execute(current)
                status = "ok"
                warning = None
            except Exception as exc:
                status = "failed"
                warning = f"Plugin {plugin.name} failed: {type(exc).__name__}: {exc}"
                current = current.with_warning(warning)

            if len(current.warnings) > before_warning_count and warning is None:
                warning = current.warnings[-1]

            timings.append(
                PluginTiming(
                    plugin=plugin.name,
                    elapsed_ms=timer.elapsed_ms(),
                    status=status,
                    warning=warning,
                )
            )

        metrics = KernelMetrics(
            total_ms=total_timer.elapsed_ms(),
            plugin_timings=timings,
            cache_status="pipeline",
            warning_count=len(current.warnings),
        )

        return current, metrics

    def load_profile(
        self,
        profile_key: str,
        config: IntelligenceEngineConfig | None = None,
        *,
        use_cache: bool = True,
        refresh: bool = False,
    ) -> dict[str, Any]:
        """Load canonical AtlasProfile payload through the service layer."""
        timer = Timer()

        payload = build_atlas_profile(
            profile_key,
            config=config,
            use_cache=use_cache,
            refresh=refresh,
        )

        cache_status = "hit" if "_cache" in payload and not refresh else "miss"

        metrics = KernelMetrics(
            total_ms=timer.elapsed_ms(),
            plugin_timings=[],
            cache_status=cache_status,
            warning_count=len(payload.get("warnings", [])),
        )

        payload["kernel"] = {
            "runtime": "atlas.kernel.runtime.AtlasKernel",
            "mode": "atlas_profile_service",
            "enabled_plugins": sorted(self.enabled_plugins()),
            "metrics": metrics.to_dict(),
        }

        return payload

    def run_profile_pipeline(
        self,
        profile_key: str,
        config: IntelligenceEngineConfig | None = None,
        *,
        enabled: set[str] | None = None,
    ) -> dict[str, Any]:
        """Run core plugin pipeline and return context payload."""
        context = self.build_context(profile_key, config=config)
        result, metrics = self.run_context(context, enabled=enabled)

        active = enabled if enabled is not None else self.enabled_plugins()

        payload = result.to_dict()
        payload["kernel"] = {
            "runtime": "atlas.kernel.runtime.AtlasKernel",
            "mode": "core_pipeline",
            "enabled_plugins": sorted(active),
            "metrics": metrics.to_dict(),
        }
        return payload

    def load_base_profile(self, profile_key: str) -> AtlasProfile:
        """Load base AtlasProfile model without executing plugins."""
        return build_base_atlas_profile(profile_key)