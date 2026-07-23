"""Atlas Canonical Structural Signature.

The Canonical Structural Signature is the immutable structural representation of
a profile inside Atlas.

Every subsystem should eventually consume this object rather than rebuilding
structure independently.

Version: 1.0
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any


CSS_VERSION = "1.0"


@dataclass(slots=True)
class IdentityLayer:
    """Immutable identity metadata."""

    profile_key: str
    canonical_name: str
    aliases: list[str] = field(default_factory=list)
    birth_date: str | None = None
    birth_time: str | None = None
    birth_location: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CipherLayer:
    """Deterministic symbolic transformation layer."""

    ordinal: dict[str, Any] = field(default_factory=dict)
    hebrew_phonetic: dict[str, Any] = field(default_factory=dict)
    hebrew_transliteration: dict[str, Any] = field(default_factory=dict)
    gematria: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class KameaLayer:
    """Foundational Kamea and topology layer."""

    topology: dict[str, Any] = field(default_factory=dict)
    planetary_graphs: dict[str, Any] = field(default_factory=dict)
    resonance: dict[str, Any] = field(default_factory=dict)
    graph_metrics: dict[str, Any] = field(default_factory=dict)
    fingerprint: dict[str, Any] = field(default_factory=dict)
    normalized_graphs: dict[str, Any] = field(default_factory=dict)
    structural_metrics: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AstronomyLayer:
    """Canonical physical measurements; interpretation is forbidden here."""

    measurements: dict[str, Any] = field(default_factory=dict)
    planet_graph: dict[str, Any] = field(default_factory=dict)
    stellar_context: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class StructuralMeasurementLayer:
    """Graph-of-graphs and population-ready deterministic feature contract."""

    master_graph: dict[str, Any] = field(default_factory=dict)
    topology_classification: dict[str, Any] = field(default_factory=dict)
    feature_vector: dict[str, float] = field(default_factory=dict)
    similarity: dict[str, Any] = field(default_factory=dict)
    cluster_membership: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class TemporalLayer:
    """Temporal and ephemeris-derived layer."""

    natal: dict[str, Any] = field(default_factory=dict)
    transits: dict[str, Any] = field(default_factory=dict)
    dasha: dict[str, Any] = field(default_factory=dict)
    calibration: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ValidationLayer:
    """Independent validation and confidence layer."""

    domains: dict[str, Any] = field(default_factory=dict)
    scientific_confidence: dict[str, Any] = field(default_factory=dict)
    consensus: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ResearchLayer:
    """Research reasoning layer."""

    reasoning: dict[str, Any] = field(default_factory=dict)
    hypothesis: dict[str, Any] = field(default_factory=dict)
    falsification: dict[str, Any] = field(default_factory=dict)
    experiment: dict[str, Any] = field(default_factory=dict)
    discovery: dict[str, Any] = field(default_factory=dict)
    memory: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class PopulationLayer:
    """Population and corpus-level analysis layer."""

    feature_vector: list[float] = field(default_factory=list)
    nearest_neighbors: list[str] = field(default_factory=list)
    clusters: list[str] = field(default_factory=list)
    correspondence: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class CanonicalStructuralSignature:
    """Canonical structural signature for one Atlas profile."""

    version: str = CSS_VERSION
    identity: IdentityLayer | None = None
    astronomy: AstronomyLayer = field(default_factory=AstronomyLayer)
    cipher: CipherLayer = field(default_factory=CipherLayer)
    kamea: KameaLayer = field(default_factory=KameaLayer)
    temporal: TemporalLayer = field(default_factory=TemporalLayer)
    structural_measurement: StructuralMeasurementLayer = field(
        default_factory=StructuralMeasurementLayer
    )
    validation: ValidationLayer = field(default_factory=ValidationLayer)
    research: ResearchLayer = field(default_factory=ResearchLayer)
    population: PopulationLayer = field(default_factory=PopulationLayer)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert signature to a serializable dictionary."""
        return {
            "version": self.version,
            "identity": dataclass_to_dict(self.identity),
            "astronomy": dataclass_to_dict(self.astronomy),
            "cipher": dataclass_to_dict(self.cipher),
            "kamea": dataclass_to_dict(self.kamea),
            "temporal": dataclass_to_dict(self.temporal),
            "structural_measurement": dataclass_to_dict(
                self.structural_measurement
            ),
            "validation": dataclass_to_dict(self.validation),
            "research": dataclass_to_dict(self.research),
            "population": dataclass_to_dict(self.population),
            "metadata": self.metadata,
        }


def dataclass_to_dict(value: Any) -> Any:
    """Convert slotted dataclasses recursively into dictionaries."""
    if value is None:
        return None

    if is_dataclass(value):
        return {
            item.name: dataclass_to_dict(getattr(value, item.name))
            for item in fields(value)
        }

    if isinstance(value, dict):
        return {
            key: dataclass_to_dict(item)
            for key, item in value.items()
        }

    if isinstance(value, list):
        return [
            dataclass_to_dict(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return tuple(dataclass_to_dict(item) for item in value)

    return value


__all__ = [
    "CSS_VERSION",
    "IdentityLayer",
    "AstronomyLayer",
    "CipherLayer",
    "KameaLayer",
    "TemporalLayer",
    "StructuralMeasurementLayer",
    "ValidationLayer",
    "ResearchLayer",
    "PopulationLayer",
    "CanonicalStructuralSignature",
    "dataclass_to_dict",
]
