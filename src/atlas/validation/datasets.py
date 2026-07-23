"""Corpus loading for validation experiments.

Builds a dense feature matrix from the compiled runtime, once, so that an
all-pairs run is linear algebra rather than 2.25 million service calls. The
matrix is derived only from compiled artifacts -- never the ACF corpus --
which is what makes a full-corpus experiment finish in seconds.

Feature order is fixed and explicit: it is part of what the result means, so
it is recorded in provenance rather than left to dictionary iteration.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import numpy as np

from atlas.compiled.calibration import group_key
from atlas.compiled.identity_vector_store import DEFAULT_COMPILED_VECTOR_DIR
from atlas.compiled.calibration import compiled_profile_keys
from atlas.compiled.identity_vector_store import load_compiled_identity_vector
from atlas.compiled.runtime import (
    load_runtime_statistics,
    normalize_vectors_with_statistics,
)
from atlas.ive.composite import PLANET_ORDER
from atlas.ive.schema import VECTOR_FEATURES
from atlas.kamea.identity_graph import CIPHER_ORDER


# Fixed, explicit ordering. Sorting the features keeps the layout stable
# against incidental reordering of VECTOR_FEATURES.
ORDERED_FEATURES: tuple[str, ...] = tuple(sorted(VECTOR_FEATURES))
ORDERED_PLANETS: tuple[str, ...] = tuple(PLANET_ORDER)
ORDERED_CIPHERS: tuple[str, ...] = tuple(CIPHER_ORDER)


@dataclass(frozen=True, slots=True)
class CorpusMatrix:
    """Compiled corpus as a dense matrix, plus the labels to read it."""

    profile_keys: tuple[str, ...]
    profile_names: tuple[str, ...]
    entity_types: tuple[str, ...]
    # (n_profiles, n_ciphers * n_planets * n_features)
    matrix: np.ndarray
    feature_layout: tuple[str, ...]
    normalization_mode: str
    skipped: tuple[str, ...]

    @property
    def profile_count(self) -> int:
        """Return how many profiles are represented."""
        return len(self.profile_keys)

    @property
    def pair_count(self) -> int:
        """Return the number of unique unordered pairs."""
        n = self.profile_count
        return n * (n - 1) // 2

    def index_of(self, profile_key: str) -> int:
        """Return the row index for a profile key."""
        return self.profile_keys.index(profile_key)

    def block(self, cipher: str | None, planet: str | None) -> np.ndarray:
        """Return the column slice for one cipher and/or planet.

        Used for per-cipher and per-planet decomposition: the same rows,
        restricted to the columns that belong to that group.
        """
        columns = [
            index
            for index, label in enumerate(self.feature_layout)
            if (cipher is None or label.startswith(f"{cipher}|"))
            and (planet is None or f"|{planet}|" in label)
        ]

        return self.matrix[:, columns]

    def provenance(self) -> dict[str, Any]:
        """Return a description of exactly what this matrix contains."""
        return {
            "profile_count": self.profile_count,
            "pair_count": self.pair_count,
            "normalization_mode": self.normalization_mode,
            "dimensions": int(self.matrix.shape[1]),
            "ciphers": list(ORDERED_CIPHERS),
            "planets": list(ORDERED_PLANETS),
            "features": list(ORDERED_FEATURES),
            "skipped_profiles": list(self.skipped),
        }


def build_feature_layout() -> tuple[str, ...]:
    """Return the fixed column labels, ``cipher|planet|feature``."""
    return tuple(
        f"{cipher}|{planet}|{feature}"
        for cipher in ORDERED_CIPHERS
        for planet in ORDERED_PLANETS
        for feature in ORDERED_FEATURES
    )


def load_corpus_matrix(
    *,
    normalization_mode: str = "raw",
    artifact_dir: Path = DEFAULT_COMPILED_VECTOR_DIR,
    profile_keys: Iterable[str] | None = None,
) -> CorpusMatrix:
    """Load every compiled profile into one dense matrix.

    Profiles missing a cipher/planet group are skipped rather than
    zero-filled: a zero is a real coordinate and would silently drag
    similarity scores toward an artefact of missingness.
    """
    keys = (
        tuple(compiled_profile_keys(artifact_dir=artifact_dir))
        if profile_keys is None
        else tuple(profile_keys)
    )

    layout = build_feature_layout()
    position = {label: index for index, label in enumerate(layout)}

    statistics = (
        load_runtime_statistics() if normalization_mode != "raw" else None
    )

    rows: list[np.ndarray] = []
    kept_keys: list[str] = []
    kept_names: list[str] = []
    kept_types: list[str] = []
    skipped: list[str] = []

    for profile_key in keys:
        try:
            artifact = load_compiled_identity_vector(
                input_path=artifact_dir
                / f"{profile_key}.identity-vector.json"
            )
        except Exception:  # noqa: BLE001 - one bad artifact must not abort
            skipped.append(profile_key)
            continue

        vectors = normalize_vectors_with_statistics(
            list(artifact.vectors),
            statistics if normalization_mode != "raw" else None,
            normalization_mode,
        )

        row = np.full(len(layout), np.nan, dtype=np.float64)

        for vector in vectors:
            for feature, value in vector.features.items():
                index = position.get(
                    f"{vector.cipher}|{vector.planet}|{feature}"
                )

                if index is not None:
                    row[index] = value

        if np.isnan(row).any():
            skipped.append(profile_key)
            continue

        rows.append(row)
        kept_keys.append(artifact.profile_key)
        kept_names.append(artifact.profile_name)
        kept_types.append(artifact.entity_type)

    matrix = (
        np.vstack(rows)
        if rows
        else np.empty((0, len(layout)), dtype=np.float64)
    )

    return CorpusMatrix(
        profile_keys=tuple(kept_keys),
        profile_names=tuple(kept_names),
        entity_types=tuple(kept_types),
        matrix=matrix,
        feature_layout=layout,
        normalization_mode=normalization_mode,
        skipped=tuple(skipped),
    )


def name_strata(profile_names: Iterable[str]) -> dict[str, np.ndarray]:
    """Return per-profile name descriptors used for stratified reporting.

    These exist to expose confounders before any cohort study: if similarity
    tracks name length or token count, that must be visible up front rather
    than discovered inside a substantive result.
    """
    names = list(profile_names)

    token_counts = np.array(
        [len(name.split()) for name in names], dtype=np.int32
    )
    char_lengths = np.array(
        [len(name.replace(" ", "")) for name in names], dtype=np.int32
    )
    is_ascii = np.array(
        [name.isascii() for name in names], dtype=bool
    )

    return {
        "token_count": token_counts,
        "character_length": char_lengths,
        "is_ascii": is_ascii,
    }


def group_label(cipher: str, planet: str) -> str:
    """Return the canonical comparable-group label."""
    return group_key(cipher, planet)
