"""The shared denotational ontology for cross-system comparison.

The most important 1E artifact, frozen and hashed before any real subject is
examined. Every system maps into these four axes *independently*; the axes are
the only vocabulary in which agreement is ever assessed, so fixing them first
is what stops the comparison from drifting to accommodate whatever a subject
happens to show.

The axes are orthogonal by design. A single expression may carry a coordinate
on each -- a domain, a dynamic, a temporal character, a behavioral
manifestation -- and two expressions are compared axis by axis, never as a
whole, because two systems can agree on domain while disagreeing on polarity.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any


ONTOLOGY_SCHEMA = "atlas.validation.denotation.ontology.v1"
ONTOLOGY_VERSION = "1.0.0"

# What the expression is about.
DOMAINS: tuple[str, ...] = (
    "cognition",
    "communication",
    "affiliation",
    "agency",
    "conflict",
    "material_organization",
    "transformation",
    "spirituality",
)

# How it moves.
DYNAMICS: tuple[str, ...] = (
    "expansion",
    "contraction",
    "stabilization",
    "disruption",
    "repetition",
    "reversal",
    "concealment",
    "emergence",
)

# Its temporal character -- the axis that governs referential comparability.
TEMPORAL_CHARACTERS: tuple[str, ...] = (
    "enduring",
    "developmental",
    "periodic",
    "acute",
    "transitional",
)

# How it manifests observably -- the axis 1E-B tests against coded behavior.
BEHAVIORAL_MANIFESTATIONS: tuple[str, ...] = (
    "initiation",
    "persistence",
    "avoidance",
    "cooperation",
    "dominance",
    "adaptation",
    "risk_taking",
)

AXES: dict[str, tuple[str, ...]] = {
    "domain": DOMAINS,
    "dynamic": DYNAMICS,
    "temporal_character": TEMPORAL_CHARACTERS,
    "behavioral_manifestation": BEHAVIORAL_MANIFESTATIONS,
}

# Frozen compatibility: which *different* coordinates on one axis denote
# compatible-but-distinct roles ("different roles in the same configuration").
# Deliberately small and structural. Without an entry here, two different
# values do NOT agree -- they are unrelated. This is the guard against
# vocabulary breadth: if any two coordinates counted as complementary
# agreement, a broad enough ontology would make every pairing confirm every
# other, which is exactly the artifact the null controls must be able to
# destroy. Symmetric pairs; membership is order-independent.
COMPATIBLE_COORDINATES: dict[str, tuple[frozenset[str], ...]] = {
    "dynamic": (
        # Both denote low change.
        frozenset({"repetition", "stabilization"}),
        # Both denote high change.
        frozenset({"disruption", "reversal"}),
        # Both denote outward movement.
        frozenset({"expansion", "emergence"}),
        # Both denote inward movement.
        frozenset({"contraction", "concealment"}),
    ),
    # Other axes start empty. A compatibility claim on domain, temporal
    # character or behavioral manifestation needs its own frozen, defensible
    # entry before it can license agreement -- it may not be assumed.
    "domain": (),
    "temporal_character": (),
    "behavioral_manifestation": (),
}


def are_compatible(axis: str, left: str, right: str) -> bool:
    """Return whether two different coordinates are a frozen compatible pair."""
    pair = frozenset({left, right})

    return any(
        pair == entry for entry in COMPATIBLE_COORDINATES.get(axis, ())
    )


# Polarity is separate from the axis coordinate, because two systems can name
# the same domain with opposite valence -- that is contradiction, not
# agreement, and collapsing them would hide it.
POLARITIES: tuple[str, ...] = ("positive", "negative", "neutral")

# Whether a system's mapping onto an axis is licensed by a direct rule or an
# interpretive one. Interpretive mappings are admissible but must be flagged,
# because the null controls have to be able to weight them down.
MAPPING_KINDS: tuple[str, ...] = ("direct", "interpretive")


class OntologyError(ValueError):
    """A coordinate does not lie in the frozen ontology."""


def is_valid_coordinate(axis: str, value: str) -> bool:
    """Return whether ``value`` is a member of ``axis``."""
    return axis in AXES and value in AXES[axis]


def require_coordinate(axis: str, value: str) -> None:
    """Raise unless ``value`` is a frozen member of ``axis``."""
    if axis not in AXES:
        raise OntologyError(
            f"{axis!r} is not an ontology axis. Choose one of "
            f"{', '.join(sorted(AXES))}."
        )

    if value not in AXES[axis]:
        raise OntologyError(
            f"{value!r} is not a frozen {axis}. The ontology is fixed before "
            "subjects are examined; a new coordinate needs a version bump, "
            "not an ad-hoc addition."
        )


def ontology_hash() -> str:
    """Return a deterministic hash of the frozen ontology.

    Participates in every concordance artifact, so a change to what an axis
    *means* invalidates comparisons made across it -- the same discipline the
    feature-schema and representation hashes enforce elsewhere.
    """
    payload = {
        "schema": ONTOLOGY_SCHEMA,
        "version": ONTOLOGY_VERSION,
        "axes": {axis: list(values) for axis, values in AXES.items()},
        "compatible_coordinates": {
            axis: sorted(sorted(pair) for pair in pairs)
            for axis, pairs in COMPATIBLE_COORDINATES.items()
        },
        "polarities": list(POLARITIES),
        "mapping_kinds": list(MAPPING_KINDS),
    }

    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode(
            "utf-8"
        )
    ).hexdigest()


def ontology_manifest() -> dict[str, Any]:
    """Return the ontology as a JSON-safe manifest, hash included."""
    return {
        "schema": ONTOLOGY_SCHEMA,
        "version": ONTOLOGY_VERSION,
        "hash": ontology_hash(),
        "axes": {axis: list(values) for axis, values in AXES.items()},
        "polarities": list(POLARITIES),
        "mapping_kinds": list(MAPPING_KINDS),
        "note": (
            "Frozen before any subject is examined. Systems map into these "
            "axes independently; agreement is assessed only in this "
            "vocabulary."
        ),
    }
