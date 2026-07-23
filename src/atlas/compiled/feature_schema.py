"""Deterministic feature-schema identity for the Atlas compiled layer.

The *feature-schema hash* is a fingerprint of the meaning of a compiled
vector: which planets and ciphers exist, which features each carries, how the
vector is built, and how it is normalized. It is deliberately independent of
any single profile's data.

It catches the failure the outer schema version cannot: the dataclass and the
``atlas.compiled.identity-vectors.v2`` string can both stay fixed while the
feature *set*, planet order, cipher order, builder, or normalization algorithm
changes underneath them. When the feature-schema hash of the current code
differs from the one recorded in an artifact, that artifact was built against a
different notion of "feature" and must be treated as stale -- even though its
source ACF is byte-for-byte unchanged.

The hash is computed only from code-declared constants, so it is available
without a corpus and is stable across runs (no timestamps, no iteration-order
dependence).
"""

from __future__ import annotations

from dataclasses import dataclass, fields
import hashlib
import json
from typing import Any

from atlas.ive.normalizer import NORMALIZATION_MODES, NORMALIZATION_VERSION
from atlas.ive.schema import IVE_VERSION, VECTOR_FEATURES, PlanetFeatureVector
from atlas.kamea.identity_graph import CIPHER_ORDER
from atlas.ive.composite import PLANET_ORDER


FEATURE_SCHEMA_VERSION = "atlas.feature-schema.v1"


@dataclass(frozen=True, slots=True)
class FeatureSchema:
    """The code-declared identity of a compiled feature vector."""

    schema_version: str
    vector_dataclass: str
    vector_fields: tuple[str, ...]
    ciphers: tuple[str, ...]
    planets: tuple[str, ...]
    features: tuple[str, ...]
    builder_version: str
    normalization_version: str
    normalization_modes: tuple[str, ...]

    def canonical_payload(self) -> dict[str, Any]:
        """Return the exact structure the hash is computed over.

        Kept separate from ``to_dict`` so the hashed content is explicit and
        auditable: anything not in here does not affect the hash.
        """
        return {
            "schema_version": self.schema_version,
            "vector_dataclass": self.vector_dataclass,
            "vector_fields": list(self.vector_fields),
            "ciphers": list(self.ciphers),
            "planets": list(self.planets),
            "features": list(self.features),
            "builder_version": self.builder_version,
            "normalization_version": self.normalization_version,
            "normalization_modes": list(self.normalization_modes),
        }

    def digest(self) -> str:
        """Return the deterministic SHA-256 over the canonical payload."""
        encoded = json.dumps(
            self.canonical_payload(),
            sort_keys=True,
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")

        return hashlib.sha256(encoded).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Return payload plus the digest, for embedding in artifacts."""
        payload = self.canonical_payload()
        payload["digest"] = self.digest()
        return payload


def current_feature_schema() -> FeatureSchema:
    """Build the feature schema from the currently loaded code.

    Ordering rules make the hash stable and meaningful:

    * cipher and planet order are the canonical declared orders -- reordering
      is a real schema change, so these are *not* sorted.
    * feature names are sorted, matching how the normalizer groups features;
      reordering the ``VECTOR_FEATURES`` tuple must not change the hash.
    """
    return FeatureSchema(
        schema_version=FEATURE_SCHEMA_VERSION,
        vector_dataclass=PlanetFeatureVector.__name__,
        vector_fields=tuple(field.name for field in fields(PlanetFeatureVector)),
        ciphers=tuple(CIPHER_ORDER),
        planets=tuple(PLANET_ORDER),
        features=tuple(sorted(VECTOR_FEATURES)),
        builder_version=str(IVE_VERSION),
        normalization_version=NORMALIZATION_VERSION,
        normalization_modes=tuple(NORMALIZATION_MODES),
    )


def current_feature_schema_hash() -> str:
    """Return the digest of the current code-declared feature schema."""
    return current_feature_schema().digest()


def feature_schema_matches(recorded_hash: str | None) -> bool:
    """Return whether a recorded hash matches the current schema.

    A missing hash (older artifact that predates schema hashing) does not
    match: callers should treat it as stale and rebuild, rather than assume
    compatibility.
    """
    if not recorded_hash:
        return False

    return recorded_hash == current_feature_schema_hash()
