"""Execution of validation experiments.

The all-pairs baseline is computed as blocked matrix multiplication rather
than pair-by-pair comparison: 2,250,381 pairs at even a millisecond each
would be forty minutes, while the same work as linear algebra is seconds.

Execution is blocked and checkpointed so a long run can resume, and so that
memory stays bounded regardless of corpus size. Block boundaries are derived
from the corpus size alone, never from timing, so a resumed run produces
byte-identical output to an uninterrupted one.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from time import perf_counter
from typing import Any, Callable

import numpy as np

from atlas.validation.datasets import (
    ORDERED_CIPHERS,
    ORDERED_PLANETS,
    CorpusMatrix,
)


DEFAULT_BLOCK_SIZE = 256


@dataclass(frozen=True, slots=True)
class PairBlock:
    """One block of computed pair scores."""

    start_row: int
    end_row: int
    pair_indices: np.ndarray
    scores: np.ndarray


def unit_normalize(matrix: np.ndarray) -> np.ndarray:
    """Return rows scaled to unit length, leaving zero rows untouched.

    Cosine similarity is then a dot product, which is what makes the
    all-pairs computation a single matrix multiply per block.
    """
    norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    safe = np.where(norms == 0.0, 1.0, norms)

    return matrix / safe


def iter_pair_blocks(
    matrix: np.ndarray,
    *,
    block_size: int = DEFAULT_BLOCK_SIZE,
    start_block: int = 0,
) -> Any:
    """Yield upper-triangle pair blocks in a deterministic order.

    Only ``j > i`` is emitted, so each unordered pair appears exactly once,
    in ascending ``(i, j)`` order regardless of block size or resume point.
    """
    normalized = unit_normalize(matrix)
    row_count = normalized.shape[0]

    block_index = 0

    for start in range(0, row_count, block_size):
        if block_index < start_block:
            block_index += 1
            continue

        end = min(start + block_size, row_count)

        # Similarities from this row block to every row at or after `start`.
        similarities = normalized[start:end] @ normalized[start:].T

        local_rows, local_cols = np.triu_indices(
            n=end - start,
            m=row_count - start,
            k=1,
        )

        global_rows = local_rows + start
        global_cols = local_cols + start

        yield block_index, PairBlock(
            start_row=start,
            end_row=end,
            pair_indices=np.column_stack((global_rows, global_cols)),
            scores=similarities[local_rows, local_cols],
        )

        block_index += 1


def expected_block_count(row_count: int, block_size: int) -> int:
    """Return how many blocks a corpus of this size produces."""
    if row_count <= 0:
        return 0

    return (row_count + block_size - 1) // block_size


@dataclass(frozen=True, slots=True)
class GroupScores:
    """Aggregate score distributions for one decomposition group."""

    label: str
    scores: np.ndarray


def compute_group_scores(
    corpus: CorpusMatrix,
    *,
    sample_pairs: np.ndarray,
) -> dict[str, np.ndarray]:
    """Return per-cipher and per-planet scores for a sample of pairs.

    Computed on a sample rather than all pairs because the decomposition is
    ten extra score columns; storing them for every pair would multiply the
    artifact size for a diagnostic that only needs a distribution.
    """
    results: dict[str, np.ndarray] = {}

    left = sample_pairs[:, 0]
    right = sample_pairs[:, 1]

    for cipher in ORDERED_CIPHERS:
        block = unit_normalize(corpus.block(cipher, None))
        results[f"cipher:{cipher}"] = np.einsum(
            "ij,ij->i", block[left], block[right]
        )

    for planet in ORDERED_PLANETS:
        block = unit_normalize(corpus.block(None, planet))
        results[f"planet:{planet}"] = np.einsum(
            "ij,ij->i", block[left], block[right]
        )

    return results


@dataclass(slots=True)
class Checkpoint:
    """Resume state for a blocked run."""

    experiment_id: str
    corpus_fingerprint: str
    block_size: int
    completed_blocks: int
    total_blocks: int
    pairs_written: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "experiment_id": self.experiment_id,
            "corpus_fingerprint": self.corpus_fingerprint,
            "block_size": self.block_size,
            "completed_blocks": self.completed_blocks,
            "total_blocks": self.total_blocks,
            "pairs_written": self.pairs_written,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "Checkpoint":
        """Rebuild from decoded JSON."""
        return cls(
            experiment_id=str(payload["experiment_id"]),
            corpus_fingerprint=str(payload["corpus_fingerprint"]),
            block_size=int(payload["block_size"]),
            completed_blocks=int(payload["completed_blocks"]),
            total_blocks=int(payload["total_blocks"]),
            pairs_written=int(payload["pairs_written"]),
        )


def load_checkpoint(path: Path) -> Checkpoint | None:
    """Load a checkpoint, or None when absent or unreadable."""
    if not path.is_file():
        return None

    try:
        return Checkpoint.from_dict(
            json.loads(path.read_text(encoding="utf-8"))
        )
    except (OSError, ValueError, KeyError, json.JSONDecodeError):
        return None


def save_checkpoint(checkpoint: Checkpoint, path: Path) -> Path:
    """Write a checkpoint atomically."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(checkpoint.to_dict(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

    return path


def run_all_pairs(
    corpus: CorpusMatrix,
    *,
    block_size: int = DEFAULT_BLOCK_SIZE,
    start_block: int = 0,
    on_block: Callable[[int, PairBlock], None] | None = None,
) -> tuple[np.ndarray, np.ndarray, float]:
    """Compute every unordered pair score.

    Returns ``(pair_indices, scores, elapsed_seconds)``.
    """
    started = perf_counter()

    index_chunks: list[np.ndarray] = []
    score_chunks: list[np.ndarray] = []

    for block_index, block in iter_pair_blocks(
        corpus.matrix,
        block_size=block_size,
        start_block=start_block,
    ):
        index_chunks.append(block.pair_indices)
        score_chunks.append(block.scores)

        if on_block is not None:
            on_block(block_index, block)

    if not index_chunks:
        empty_pairs = np.empty((0, 2), dtype=np.int64)
        return empty_pairs, np.empty(0, dtype=np.float64), 0.0

    return (
        np.vstack(index_chunks),
        np.concatenate(score_chunks),
        perf_counter() - started,
    )
