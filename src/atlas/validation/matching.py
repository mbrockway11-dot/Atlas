"""Structural matching and matched percentiles.

The all-pairs baseline showed that absolute name-length difference predicts
similarity at r = -0.55, explaining 30% of score variance. A global
percentile therefore says less than it appears to: a pair can sit at the 97th
percentile of the whole population purely because both names are of similar
length, and be entirely ordinary among names of comparable structure.

This module supplies the second number. A *matched* percentile locates a
score within the subpopulation of pairs that share its structural stratum, so
that "high" means high relative to like-shaped names rather than to the
corpus at large.

Strata are stored as quantile grids rather than full sorted arrays: a grid of
a few hundred points per stratum reconstructs percentiles to well within
reporting precision, and keeps the index small enough to load on every
request.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np


MATCHED_INDEX_SCHEMA = "atlas.validation.matched-percentile-index.v1"

# Buckets for absolute name-length difference. Boundaries follow the strata
# that showed the steepest score gradient in the baseline.
LENGTH_DIFFERENCE_EDGES: tuple[int, ...] = (0, 3, 6, 11, 21)

# Quantile grid resolution per stratum. 401 points gives ~0.25 percentile
# resolution, finer than anything a report quotes.
QUANTILE_GRID_SIZE = 401

# Strata with fewer pairs than this are pooled into a shared fallback: a
# percentile computed from a handful of pairs is noise wearing a number.
MIN_STRATUM_SIZE = 200


def length_difference_bucket(difference: int | np.ndarray) -> Any:
    """Return the bucket label for an absolute length difference."""
    edges = np.asarray(LENGTH_DIFFERENCE_EDGES)
    index = np.searchsorted(edges, np.asarray(difference), side="right") - 1
    index = np.clip(index, 0, len(edges) - 1)

    labels = np.array(
        [
            f"{edges[i]}-{edges[i + 1] - 1}" if i + 1 < len(edges)
            else f"{edges[i]}+"
            for i in range(len(edges))
        ]
    )

    return labels[index]


def stratum_keys(
    *,
    token_counts: np.ndarray,
    char_lengths: np.ndarray,
    pair_indices: np.ndarray,
) -> np.ndarray:
    """Return a structural stratum label for every pair.

    The label combines the (order-independent) token-count pair with the
    length-difference bucket -- the two structural variables the baseline
    identified as confounders.
    """
    left = pair_indices[:, 0]
    right = pair_indices[:, 1]

    low_tokens = np.minimum(token_counts[left], token_counts[right])
    high_tokens = np.maximum(token_counts[left], token_counts[right])

    length_difference = np.abs(
        char_lengths[left].astype(np.int64)
        - char_lengths[right].astype(np.int64)
    )

    buckets = length_difference_bucket(length_difference)

    return np.char.add(
        np.char.add(
            np.char.add(low_tokens.astype(str), "+"),
            np.char.add(high_tokens.astype(str), "|len:"),
        ),
        buckets,
    )


@dataclass(frozen=True, slots=True)
class Stratum:
    """The score distribution of one structural stratum."""

    label: str
    count: int
    quantiles: tuple[float, ...]

    def percentile_of(self, score: float) -> float:
        """Return the percentile of a score within this stratum."""
        grid = np.asarray(self.quantiles, dtype=np.float64)

        # Position of `score` among the grid points, interpolated.
        position = float(np.searchsorted(grid, score, side="right"))

        if position <= 0:
            return 0.0

        if position >= grid.size:
            return 100.0

        lower = grid[int(position) - 1]
        upper = grid[int(position)]
        span = upper - lower
        fraction = (score - lower) / span if span > 0 else 0.0

        return float(100.0 * (position - 1 + fraction) / (grid.size - 1))

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "label": self.label,
            "count": self.count,
            "quantiles": list(self.quantiles),
        }


@dataclass(frozen=True, slots=True)
class MatchedPercentileIndex:
    """Per-stratum score distributions, plus a pooled fallback."""

    schema_version: str
    strata: dict[str, Stratum]
    pooled: Stratum
    total_pairs: int
    min_stratum_size: int

    def stratum_for(self, label: str) -> Stratum:
        """Return the stratum for a label, or the pooled fallback."""
        return self.strata.get(label, self.pooled)

    def matched_percentile(self, score: float, label: str) -> float:
        """Return the percentile of a score within its own stratum."""
        return self.stratum_for(label).percentile_of(score)

    def coverage(self) -> dict[str, Any]:
        """Return how much of the population sits in named strata."""
        named = sum(stratum.count for stratum in self.strata.values())

        return {
            "strata": len(self.strata),
            "pairs_in_named_strata": named,
            "pairs_pooled": self.total_pairs - named,
            "named_fraction": (
                named / self.total_pairs if self.total_pairs else 0.0
            ),
        }

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "total_pairs": self.total_pairs,
            "min_stratum_size": self.min_stratum_size,
            "coverage": self.coverage(),
            "pooled": self.pooled.to_dict(),
            "strata": {
                label: stratum.to_dict()
                for label, stratum in sorted(self.strata.items())
            },
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "MatchedPercentileIndex":
        """Reconstruct and validate from decoded JSON."""
        schema_version = str(payload["schema_version"])

        if schema_version != MATCHED_INDEX_SCHEMA:
            raise ValueError(
                f"Unsupported matched-percentile index: {schema_version!r}"
            )

        def stratum(body: dict[str, Any]) -> Stratum:
            return Stratum(
                label=str(body["label"]),
                count=int(body["count"]),
                quantiles=tuple(float(v) for v in body["quantiles"]),
            )

        return cls(
            schema_version=schema_version,
            strata={
                str(label): stratum(body)
                for label, body in payload["strata"].items()
            },
            pooled=stratum(payload["pooled"]),
            total_pairs=int(payload["total_pairs"]),
            min_stratum_size=int(payload["min_stratum_size"]),
        )


def _quantile_grid(values: np.ndarray) -> tuple[float, ...]:
    """Return an evenly spaced quantile grid over a score array."""
    probabilities = np.linspace(0.0, 100.0, QUANTILE_GRID_SIZE)

    return tuple(
        float(v) for v in np.percentile(np.sort(values), probabilities)
    )


def build_matched_index(
    *,
    scores: np.ndarray,
    labels: np.ndarray,
    min_stratum_size: int = MIN_STRATUM_SIZE,
) -> MatchedPercentileIndex:
    """Build a matched-percentile index from an all-pairs run."""
    values = np.asarray(scores, dtype=np.float64)
    unique, inverse = np.unique(labels, return_inverse=True)

    strata: dict[str, Stratum] = {}

    for index, label in enumerate(unique):
        selected = values[inverse == index]

        if selected.size < min_stratum_size:
            continue

        strata[str(label)] = Stratum(
            label=str(label),
            count=int(selected.size),
            quantiles=_quantile_grid(selected),
        )

    return MatchedPercentileIndex(
        schema_version=MATCHED_INDEX_SCHEMA,
        strata=strata,
        pooled=Stratum(
            label="__pooled__",
            count=int(values.size),
            quantiles=_quantile_grid(values),
        ),
        total_pairs=int(values.size),
        min_stratum_size=min_stratum_size,
    )


def save_matched_index(
    index: MatchedPercentileIndex,
    path: Path,
) -> Path:
    """Write the index atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(index.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

    return path


def load_matched_index(path: Path) -> MatchedPercentileIndex:
    """Load and validate a matched-percentile index."""
    payload = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(payload, dict):
        raise ValueError("Matched-percentile index root must be an object.")

    return MatchedPercentileIndex.from_dict(payload)


def sample_matched_controls(
    *,
    positive_pairs: Sequence[tuple[int, int]],
    labels_by_pair: dict[tuple[int, int], str],
    candidate_pairs: np.ndarray,
    candidate_labels: np.ndarray,
    controls_per_positive: int = 5,
    seed: int = 0,
) -> dict[tuple[int, int], list[tuple[int, int]]]:
    """Draw structurally matched controls for each positive pair.

    Controls are drawn from candidates sharing the positive pair's stratum,
    so a cohort effect cannot be an artefact of name shape. Positives are
    never returned as their own controls.
    """
    rng = np.random.default_rng(seed)

    by_label: dict[str, list[int]] = {}

    for row, label in enumerate(candidate_labels):
        by_label.setdefault(str(label), []).append(row)

    positive_set = {tuple(pair) for pair in positive_pairs}
    matched: dict[tuple[int, int], list[tuple[int, int]]] = {}

    for pair in positive_pairs:
        key = tuple(pair)
        label = labels_by_pair.get(key)
        pool = by_label.get(str(label), [])

        eligible = [
            row
            for row in pool
            if tuple(candidate_pairs[row]) not in positive_set
        ]

        if not eligible:
            matched[key] = []
            continue

        take = min(controls_per_positive, len(eligible))
        chosen = rng.choice(len(eligible), size=take, replace=False)

        matched[key] = [
            tuple(candidate_pairs[eligible[int(index)]]) for index in chosen
        ]

    return matched
