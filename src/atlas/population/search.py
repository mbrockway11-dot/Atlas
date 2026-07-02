"""Population search utilities."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from atlas.fingerprint import StructuralFingerprint
from atlas.population.index import PopulationIndex
from atlas.population.similarity import (
    PopulationSimilarity,
    find_similar_profiles,
)


POPULATION_SEARCH_VERSION = "0.1"


@dataclass(frozen=True)
class PopulationSearchResult:
    """Search result wrapper for population similarity matches."""

    query_profile_key: str
    matches: tuple[PopulationSimilarity, ...]
    filters: dict[str, Any]
    metadata: dict[str, Any]

    @property
    def count(self) -> int:
        """Return match count."""
        return len(self.matches)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe search payload."""
        return {
            "version": POPULATION_SEARCH_VERSION,
            "query_profile_key": self.query_profile_key,
            "count": self.count,
            "matches": [
                match.to_dict()
                for match in self.matches
            ],
            "filters": self.filters,
            "metadata": self.metadata,
        }


def search_population(
    *,
    index: PopulationIndex,
    fingerprint: StructuralFingerprint,
    minimum_similarity: float = 0.0,
    top_k: int = 25,
    exclude_self: bool = False,
    fingerprint_type: str | None = None,
    metadata_filters: dict[str, Any] | None = None,
) -> PopulationSearchResult:
    """Search population index using structural fingerprint similarity."""
    if top_k <= 0:
        raise ValueError("top_k must be greater than zero")

    if minimum_similarity < 0.0 or minimum_similarity > 1.0:
        raise ValueError("minimum_similarity must be between 0.0 and 1.0")

    metadata_filters = metadata_filters or {}

    candidates = _filter_index(
        index=index,
        exclude_profile_key=fingerprint.profile_key if exclude_self else None,
        fingerprint_type=fingerprint_type,
        metadata_filters=metadata_filters,
    )

    matches = find_similar_profiles(
        index=candidates,
        fingerprint=fingerprint,
        limit=max(top_k, candidates.count or 1),
    )

    filtered_matches = tuple(
        match
        for match in matches
        if match.similarity >= minimum_similarity
    )[:top_k]

    return PopulationSearchResult(
        query_profile_key=fingerprint.profile_key,
        matches=filtered_matches,
        filters={
            "minimum_similarity": minimum_similarity,
            "top_k": top_k,
            "exclude_self": exclude_self,
            "fingerprint_type": fingerprint_type,
            "metadata_filters": metadata_filters,
        },
        metadata={
            "search_version": POPULATION_SEARCH_VERSION,
            "candidate_count": candidates.count,
            "index_count": index.count,
        },
    )


def _filter_index(
    *,
    index: PopulationIndex,
    exclude_profile_key: str | None,
    fingerprint_type: str | None,
    metadata_filters: dict[str, Any],
) -> PopulationIndex:
    """Filter population index before similarity search."""
    records = []

    for record in index.records:
        if exclude_profile_key and record.profile_key == exclude_profile_key:
            continue

        if fingerprint_type is not None:
            if record.metadata.get("fingerprint_type") != fingerprint_type:
                continue

        if not _metadata_matches(
            record.metadata,
            metadata_filters,
        ):
            continue

        records.append(record)

    return PopulationIndex(
        records=tuple(records),
        metadata={
            **index.metadata,
            "filtered": True,
            "filtered_count": len(records),
        },
    )


def _metadata_matches(
    metadata: dict[str, Any],
    filters: dict[str, Any],
) -> bool:
    """Return whether metadata satisfies all filters."""
    for key, expected in filters.items():
        if metadata.get(key) != expected:
            return False

    return True
