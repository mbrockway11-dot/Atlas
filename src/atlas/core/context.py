"""Shared execution context for Atlas pipelines."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ResearchContext:
    """Immutable context passed through Atlas execution pipelines."""

    profile_key: str
    display_name: str
    profile_dir: str
    config: dict[str, Any] = field(default_factory=dict)
    data: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def with_data(self, key: str, value: Any) -> "ResearchContext":
        data = dict(self.data)
        data[key] = value
        return self._replace(data=data)

    def with_evidence(self, records: list[dict[str, Any]]) -> "ResearchContext":
        return self._replace(evidence=[*self.evidence, *records])

    def with_provenance(self, records: list[dict[str, Any]]) -> "ResearchContext":
        return self._replace(provenance=[*self.provenance, *records])

    def with_warning(self, warning: str) -> "ResearchContext":
        return self._replace(warnings=[*self.warnings, warning])

    def _replace(
        self,
        *,
        data: dict[str, Any] | None = None,
        evidence: list[dict[str, Any]] | None = None,
        provenance: list[dict[str, Any]] | None = None,
        warnings: list[str] | None = None,
    ) -> "ResearchContext":
        return ResearchContext(
            profile_key=self.profile_key,
            display_name=self.display_name,
            profile_dir=self.profile_dir,
            config=dict(self.config),
            data=dict(self.data) if data is None else data,
            evidence=list(self.evidence) if evidence is None else evidence,
            provenance=list(self.provenance) if provenance is None else provenance,
            warnings=list(self.warnings) if warnings is None else warnings,
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)