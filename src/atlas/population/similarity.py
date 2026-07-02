"""Population similarity search for structural fingerprints."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Any

from atlas.fingerprint import StructuralFingerprint
from atlas.population.index import PopulationIndex, PopulationRecord


POPULATION_SIMILARITY_VERSION = "0.1"


@dataclass(frozen=True)
class PopulationSimilarity:
    """Similarity result for one population record."""

    profile_key: str
    similarity: float
    distance: float
    shared_features: dict[str, float]
    structural_hash: str

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe similarity result."""
        return {
            "profile_key": self.profile_key,
            "similarity": self.similarity,
            "distance": self.distance,
            "shared_features": self.shared_features,
            "structural_hash": self.structural_hash,
        }


def find_similar_profiles(
    *,
    index: PopulationIndex,
    fingerprint: StructuralFingerprint,
    limit: int = 10,
) -> list[PopulationSimilarity]:
    """Find most similar population records to one fingerprint."""
    if limit <= 0:
        raise ValueError("limit must be greater than zero")

    results = [
        compare_fingerprint_to_record(
            fingerprint=fingerprint,
            record=record,
        )
        for record in index.records
    ]

    results.sort(
        key=lambda result: (
            -result.similarity,
            result.profile_key,
        )
    )

    return results[:limit]


def compare_fingerprint_to_record(
    *,
    fingerprint: StructuralFingerprint,
    record: PopulationRecord,
) -> PopulationSimilarity:
    """Compare one fingerprint against one population record."""
    distance, shared_features = vector_distance(
        fingerprint.vector,
        record.vector,
    )

    similarity = similarity_from_distance(distance)

    return PopulationSimilarity(
        profile_key=record.profile_key,
        similarity=similarity,
        distance=distance,
        shared_features=shared_features,
        structural_hash=record.structural_hash,
    )


def vector_distance(
    left: dict[str, float],
    right: dict[str, float],
) -> tuple[float, dict[str, float]]:
    """Compute normalized Euclidean distance over shared vector keys."""
    shared_keys = sorted(set(left) & set(right))

    if not shared_keys:
        return 1.0, {}

    squared = 0.0
    shared_features: dict[str, float] = {}

    for key in shared_keys:
        left_value = float(left[key])
        right_value = float(right[key])

        scale = max(abs(left_value), abs(right_value), 1.0)
        normalized_delta = (left_value - right_value) / scale

        squared += normalized_delta ** 2
        shared_features[key] = 1.0 - min(1.0, abs(normalized_delta))

    distance = sqrt(squared / len(shared_keys))

    return distance, shared_features


def similarity_from_distance(distance: float) -> float:
    """Convert distance to bounded similarity."""
    return 1.0 / (1.0 + max(0.0, float(distance)))
