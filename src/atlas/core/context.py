"""Atlas Core runtime contexts."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from typing import Any, Iterable, Mapping
from uuid import uuid4


@dataclass
class AtlasContext:
    """Mutable runtime context used by newer node-oriented workflows."""

    mode: str = "paper"
    run_id: str = field(default_factory=lambda: str(uuid4()))
    started_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    live_trading_enabled: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ResearchContext:
    """Immutable profile research context used by the plugin kernel.

    The helper methods always return a new context so plugins cannot mutate
    upstream state accidentally. This preserves the public API expected by the
    kernel, plugin registry, dashboards, and historical tests while allowing
    ``AtlasContext`` to remain available for newer runtime workflows.
    """

    profile_key: str
    display_name: str
    profile_dir: str
    config: Mapping[str, Any] = field(default_factory=dict)
    data: Mapping[str, Any] = field(default_factory=dict)
    provenance: tuple[Mapping[str, Any], ...] = ()
    warnings: tuple[str, ...] = ()

    def with_data(self, key: str, value: Any) -> "ResearchContext":
        """Return a copy containing one updated data section."""
        updated = dict(self.data)
        updated[key] = value
        return replace(self, data=updated)

    def with_provenance(
        self,
        records: Iterable[Mapping[str, Any]],
    ) -> "ResearchContext":
        """Return a copy with provenance records appended."""
        additions = tuple(dict(record) for record in records)
        return replace(self, provenance=(*self.provenance, *additions))

    def with_warning(self, warning: str) -> "ResearchContext":
        """Return a copy with one warning appended."""
        return replace(self, warnings=(*self.warnings, str(warning)))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-friendly representation of the context."""
        return {
            "profile_key": self.profile_key,
            "display_name": self.display_name,
            "profile_dir": self.profile_dir,
            "config": dict(self.config),
            "data": dict(self.data),
            "provenance": [dict(record) for record in self.provenance],
            "warnings": list(self.warnings),
        }


__all__ = ["AtlasContext", "ResearchContext"]
