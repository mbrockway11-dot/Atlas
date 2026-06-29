"""Canonical AtlasProfile payload."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class AtlasProfile:
    """One canonical profile payload for dashboards, services, and future APIs."""

    profile_key: str
    display_name: str
    profile_dir: str
    sections: dict[str, Any] = field(default_factory=dict)
    evidence: list[dict[str, Any]] = field(default_factory=list)
    provenance: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def with_section(self, name: str, value: Any) -> "AtlasProfile":
        """Return a copy with one section added or replaced."""
        sections = dict(self.sections)
        sections[name] = value

        return AtlasProfile(
            profile_key=self.profile_key,
            display_name=self.display_name,
            profile_dir=self.profile_dir,
            sections=sections,
            evidence=list(self.evidence),
            provenance=list(self.provenance),
            warnings=list(self.warnings),
        )

    def with_evidence(self, records: list[dict[str, Any]]) -> "AtlasProfile":
        """Return a copy with evidence records appended."""
        return AtlasProfile(
            profile_key=self.profile_key,
            display_name=self.display_name,
            profile_dir=self.profile_dir,
            sections=dict(self.sections),
            evidence=[*self.evidence, *records],
            provenance=list(self.provenance),
            warnings=list(self.warnings),
        )

    def with_provenance(self, records: list[dict[str, Any]]) -> "AtlasProfile":
        """Return a copy with provenance records appended."""
        return AtlasProfile(
            profile_key=self.profile_key,
            display_name=self.display_name,
            profile_dir=self.profile_dir,
            sections=dict(self.sections),
            evidence=list(self.evidence),
            provenance=[*self.provenance, *records],
            warnings=list(self.warnings),
        )

    def with_warning(self, warning: str) -> "AtlasProfile":
        """Return a copy with a warning appended."""
        return AtlasProfile(
            profile_key=self.profile_key,
            display_name=self.display_name,
            profile_dir=self.profile_dir,
            sections=dict(self.sections),
            evidence=list(self.evidence),
            provenance=list(self.provenance),
            warnings=[*self.warnings, warning],
        )

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary."""
        return asdict(self)