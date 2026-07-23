"""Nearest-neighbour and false-neighbour analysis.

"Zero exact collisions" is a weak reassurance. What matters for anyone
reading a nearest-neighbour list as meaningful is the near-collision: two
unrelated names sitting at the very top of the distribution, and *why*.

Every reported neighbour therefore carries the numbers needed to discount it:
global percentile, matched percentile within its structural stratum, the
length and token differences that the baseline showed drive scores, and the
per-cipher and per-planet decomposition that says which part of the encoding
produced the agreement.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

import numpy as np

from atlas.validation.datasets import (
    ORDERED_CIPHERS,
    ORDERED_PLANETS,
    CorpusMatrix,
)
from atlas.validation.runner import unit_normalize


@dataclass(frozen=True, slots=True)
class NeighborRecord:
    """One neighbour pair with everything needed to interpret it."""

    profile_a: str
    profile_b: str
    name_a: str
    name_b: str
    score: float
    global_percentile: float
    matched_percentile: float
    stratum: str
    length_difference: int
    token_difference: int
    cipher_scores: dict[str, float]
    planet_scores: dict[str, float]

    def dominant_cipher(self) -> str:
        """Return the cipher contributing the highest agreement."""
        return max(self.cipher_scores, key=self.cipher_scores.get)

    def dominant_planet(self) -> str:
        """Return the planet contributing the highest agreement."""
        return max(self.planet_scores, key=self.planet_scores.get)

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "profile_a": self.profile_a,
            "profile_b": self.profile_b,
            "name_a": self.name_a,
            "name_b": self.name_b,
            "score": self.score,
            "global_percentile": self.global_percentile,
            "matched_percentile": self.matched_percentile,
            "stratum": self.stratum,
            "length_difference": self.length_difference,
            "token_difference": self.token_difference,
            "dominant_cipher": self.dominant_cipher(),
            "dominant_planet": self.dominant_planet(),
            "cipher_scores": dict(self.cipher_scores),
            "planet_scores": dict(self.planet_scores),
        }


def decompose_pair(
    corpus: CorpusMatrix,
    left: int,
    right: int,
) -> tuple[dict[str, float], dict[str, float]]:
    """Return per-cipher and per-planet similarity for one pair."""
    cipher_scores: dict[str, float] = {}
    planet_scores: dict[str, float] = {}

    for cipher in ORDERED_CIPHERS:
        block = unit_normalize(corpus.block(cipher, None))
        cipher_scores[cipher] = float(block[left] @ block[right])

    for planet in ORDERED_PLANETS:
        block = unit_normalize(corpus.block(None, planet))
        planet_scores[planet] = float(block[left] @ block[right])

    return cipher_scores, planet_scores


def nearest_neighbors(
    corpus: CorpusMatrix,
    profile_key: str,
    *,
    limit: int = 25,
) -> list[tuple[str, float]]:
    """Return the closest profiles to one profile, excluding itself.

    Exact brute-force search. At corpus scale this is a single matrix-vector
    product, and being exact means a neighbour list never needs a caveat
    about approximation.
    """
    index = corpus.index_of(profile_key)
    normalized = unit_normalize(corpus.matrix)

    scores = normalized @ normalized[index]
    scores[index] = -np.inf

    take = min(limit, scores.size - 1)
    order = np.argpartition(scores, -take)[-take:]
    order = order[np.argsort(scores[order])[::-1]]

    return [
        (corpus.profile_keys[int(row)], float(scores[int(row)]))
        for row in order
    ]


def extreme_pairs(
    *,
    scores: np.ndarray,
    pair_indices: np.ndarray,
    fraction: float,
    limit: int,
) -> np.ndarray:
    """Return row positions of the top `fraction` of pairs by score."""
    if not 0.0 < fraction <= 1.0:
        raise ValueError("fraction must be in (0, 1].")

    threshold = float(np.quantile(scores, 1.0 - fraction))
    candidates = np.flatnonzero(scores >= threshold)

    ordered = candidates[np.argsort(scores[candidates])[::-1]]

    return ordered[:limit]


def build_neighbor_records(
    *,
    corpus: CorpusMatrix,
    rows: Sequence[int],
    scores: np.ndarray,
    pair_indices: np.ndarray,
    strata: np.ndarray,
    char_lengths: np.ndarray,
    token_counts: np.ndarray,
    global_percentile_of,
    matched_percentile_of,
) -> list[NeighborRecord]:
    """Build fully annotated neighbour records for selected pair rows."""
    records: list[NeighborRecord] = []

    for row in rows:
        left = int(pair_indices[row, 0])
        right = int(pair_indices[row, 1])
        score = float(scores[row])

        cipher_scores, planet_scores = decompose_pair(corpus, left, right)

        records.append(
            NeighborRecord(
                profile_a=corpus.profile_keys[left],
                profile_b=corpus.profile_keys[right],
                name_a=corpus.profile_names[left],
                name_b=corpus.profile_names[right],
                score=score,
                global_percentile=float(global_percentile_of(score)),
                matched_percentile=float(
                    matched_percentile_of(score, str(strata[row]))
                ),
                stratum=str(strata[row]),
                length_difference=int(
                    abs(
                        int(char_lengths[left]) - int(char_lengths[right])
                    )
                ),
                token_difference=int(
                    abs(int(token_counts[left]) - int(token_counts[right]))
                ),
                cipher_scores=cipher_scores,
                planet_scores=planet_scores,
            )
        )

    return records


def summarize_false_neighbors(
    records: Sequence[NeighborRecord],
) -> dict[str, Any]:
    """Summarize what the extreme neighbours have in common.

    The headline number is how many top-scoring pairs remain extreme once
    structure is controlled: a near-neighbour that is ordinary within its own
    stratum is explained by name shape, not by identity.
    """
    if not records:
        return {"count": 0}

    matched = np.array([r.matched_percentile for r in records])
    length_differences = np.array([r.length_difference for r in records])

    cipher_counts: dict[str, int] = {}
    planet_counts: dict[str, int] = {}

    for record in records:
        cipher = record.dominant_cipher()
        planet = record.dominant_planet()
        cipher_counts[cipher] = cipher_counts.get(cipher, 0) + 1
        planet_counts[planet] = planet_counts.get(planet, 0) + 1

    explained = int(np.count_nonzero(matched < 95.0))

    return {
        "count": len(records),
        "mean_length_difference": float(length_differences.mean()),
        "median_length_difference": float(np.median(length_differences)),
        "mean_matched_percentile": float(matched.mean()),
        "explained_by_structure": explained,
        "explained_fraction": explained / len(records),
        "still_extreme_when_matched": len(records) - explained,
        "dominant_cipher_counts": dict(sorted(cipher_counts.items())),
        "dominant_planet_counts": dict(sorted(planet_counts.items())),
    }
