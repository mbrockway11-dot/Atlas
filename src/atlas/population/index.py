"""Population index for structural fingerprints."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.fingerprint import StructuralFingerprint


POPULATION_INDEX_VERSION = "0.1"


@dataclass(frozen=True)
class PopulationRecord:
    """One profile entry in a population index."""

    profile_key: str
    structural_hash: str
    vector: dict[str, float]
    labels: dict[str, Any]
    metadata: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe population record."""
        return {
            "profile_key": self.profile_key,
            "structural_hash": self.structural_hash,
            "vector": self.vector,
            "labels": self.labels,
            "metadata": self.metadata,
        }


@dataclass(frozen=True)
class PopulationIndex:
    """Immutable population index of structural fingerprints."""

    records: tuple[PopulationRecord, ...]
    metadata: dict[str, Any]

    @property
    def count(self) -> int:
        """Return record count."""
        return len(self.records)

    def profile_keys(self) -> tuple[str, ...]:
        """Return indexed profile keys."""
        return tuple(record.profile_key for record in self.records)

    def find_profile(self, profile_key: str) -> PopulationRecord | None:
        """Find one profile record by key."""
        for record in self.records:
            if record.profile_key == profile_key:
                return record

        return None

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe population index."""
        return {
            "version": POPULATION_INDEX_VERSION,
            "count": self.count,
            "records": [
                record.to_dict()
                for record in self.records
            ],
            "metadata": self.metadata,
        }


def build_population_record(
    fingerprint: StructuralFingerprint,
) -> PopulationRecord:
    """Build population record from structural fingerprint."""
    return PopulationRecord(
        profile_key=fingerprint.profile_key,
        structural_hash=fingerprint.structural_hash,
        vector=fingerprint.vector,
        labels=fingerprint.labels,
        metadata=fingerprint.metadata,
    )


def build_population_index(
    fingerprints: list[StructuralFingerprint] | tuple[StructuralFingerprint, ...],
) -> PopulationIndex:
    """Build immutable population index from structural fingerprints."""
    records = tuple(
        build_population_record(fingerprint)
        for fingerprint in fingerprints
    )

    return PopulationIndex(
        records=records,
        metadata={
            "index_version": POPULATION_INDEX_VERSION,
            "fingerprint_count": len(records),
        },
    )