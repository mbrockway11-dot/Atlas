"""Atlas kernel job helpers.

This is lightweight scaffolding for future CLI commands such as corpus rebuilds,
cache refreshes, and batch profile execution.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from atlas.intelligence.models import IntelligenceEngineConfig
from atlas.kernel.runtime import AtlasKernel
from atlas.services.profile_service import list_profile_keys


@dataclass(frozen=True)
class KernelJobResult:
    """Result of a kernel job."""

    job: str
    profile_count: int
    succeeded: int
    failed: int
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe job result."""
        return asdict(self)


def rebuild_intelligence_cache(
    *,
    config: IntelligenceEngineConfig | None = None,
    limit: int | None = None,
) -> KernelJobResult:
    """Refresh AtlasProfile cache for saved profiles."""
    kernel = AtlasKernel()
    profile_keys = list_profile_keys()

    if limit is not None:
        profile_keys = profile_keys[:limit]

    succeeded = 0
    failed = 0
    warnings: list[str] = []

    for profile_key in profile_keys:
        try:
            payload = kernel.load_profile(
                profile_key,
                config=config,
                use_cache=True,
                refresh=True,
            )
            succeeded += 1
            for warning in payload.get("warnings", []):
                warnings.append(f"{profile_key}: {warning}")
        except Exception as exc:
            failed += 1
            warnings.append(f"{profile_key}: {type(exc).__name__}: {exc}")

    return KernelJobResult(
        job="rebuild_intelligence_cache",
        profile_count=len(profile_keys),
        succeeded=succeeded,
        failed=failed,
        warnings=warnings,
    )