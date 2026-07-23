"""Deterministic content hashing for compiled artifacts.

An artifact's ``content_hash`` fingerprints only its *semantic* content --
what the artifact means -- and deliberately excludes volatile provenance such
as ``compiled_at``, git state, platform, and the invoking command. Two runs of
the same compiler semantics over the same source therefore produce the same
content hash, even though their provenance blocks differ by timestamp.

That property is what makes the hash useful for reproducibility checks,
cache-equality decisions, audit trails, and future distributed builds: it
answers "is this the same artifact?" without being fooled by when or where it
was built.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from atlas.ive.schema import PlanetFeatureVector


def _canonical_vector(vector: PlanetFeatureVector) -> dict[str, Any]:
    """Return one vector as a canonical, order-stable dict."""
    return {
        "version": vector.version,
        "name": vector.name,
        "cipher": vector.cipher,
        "planet": vector.planet,
        "kamea": vector.kamea,
        "grid_size": vector.grid_size,
        # Features are sorted so a reordering of the source mapping -- which
        # carries no meaning -- never changes the hash.
        "features": dict(sorted(vector.features.items())),
    }


def compute_identity_content_hash(
    *,
    profile_key: str,
    profile_name: str,
    entity_type: str,
    source_acf_sha256: str,
    feature_schema_hash: str,
    vectors: Iterable[PlanetFeatureVector],
) -> str:
    """Return the deterministic content hash of a compiled identity artifact.

    Covers profile metadata, the source hash, the feature-schema hash, and the
    ordered vector data. Excludes every volatile provenance field.
    """
    payload = {
        "profile_key": profile_key,
        "profile_name": profile_name,
        "entity_type": entity_type,
        "source_acf_sha256": source_acf_sha256,
        "feature_schema_hash": feature_schema_hash,
        "vectors": [_canonical_vector(vector) for vector in vectors],
    }

    encoded = json.dumps(
        payload,
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()
