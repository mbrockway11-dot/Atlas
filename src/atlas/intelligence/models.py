"""Stable data contracts for the Atlas Intelligence Engine."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class IntelligenceEngineConfig:
    """Configuration for the Atlas Intelligence Engine."""

    transit_date: str = "2026-06-29"
    neighbor_limit: int = 10
    cluster_count: int = 5
    principal_components: int = 3
    topology_threshold: float = 0.75
    topology_top_k: int = 5
    similarity_metric: str = "cosine"


@dataclass(frozen=True)
class ProfileReference:
    """Profile identity reference."""

    name: str
    profile_dir: str


@dataclass(frozen=True)
class PopulationPosition:
    """Profile position within the population feature space."""

    nearest_neighbors: list[dict[str, Any]] = field(default_factory=list)
    outlier_rank: int | None = None
    centroid_distance: float | None = None


@dataclass(frozen=True)
class StatisticalPosition:
    """Profile position within statistical population models."""

    cluster: dict[str, Any] | None = None
    silhouette: dict[str, Any] | None = None
    principal_components: dict[str, Any] | None = None
    explained_variance_ratio: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class TopologyPosition:
    """Profile role within the population topology graph."""

    available: bool
    degree: int = 0
    weighted_degree: float = 0.0
    component: int | None = None
    community: int | None = None
    degree_centrality: float = 0.0
    weighted_degree_centrality: float = 0.0
    closeness_centrality: float = 0.0
    reason: str | None = None


@dataclass(frozen=True)
class EvidenceRecord:
    """Evidence record produced by an existing Atlas subsystem."""

    claim: str
    source: str
    value: dict[str, Any] | list[Any] | str | int | float | None
    weight: float


@dataclass(frozen=True)
class ConfidenceSummary:
    """Confidence summary based on evidence coverage."""

    score: float
    label: str
    evidence_count: int


@dataclass(frozen=True)
class IntelligenceSummary:
    """Human-readable Intelligence Engine summary."""

    headline: str
    population: str
    statistics: str
    topology: str
    confidence: str


@dataclass(frozen=True)
class ProvenanceRecord:
    """Traceability record for an Intelligence Engine section."""

    section: str
    source: str
    role: str


@dataclass(frozen=True)
class AtlasIntelligencePayload:
    """Canonical Intelligence Engine payload."""

    profile: ProfileReference
    research_session: Any
    population_position: PopulationPosition | None
    statistical_position: StatisticalPosition | None
    topology_position: TopologyPosition | None
    evidence: list[EvidenceRecord]
    confidence: ConfidenceSummary
    summary: IntelligenceSummary
    provenance: list[ProvenanceRecord]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Return JSON-safe dictionary payload."""
        return asdict(self)