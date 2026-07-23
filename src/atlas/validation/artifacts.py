"""Persistence and provenance for validation experiments.

Every result is tied to the exact corpus and schema that produced it. A score
without that binding is not reproducible: the same experiment over a
recompiled corpus is a different experiment, and only the hashes make that
visible.

Pair data is written as Parquet because 2.25 million rows in JSON is neither
readable nor cheap; summaries stay JSON because they are meant to be read.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import json
from pathlib import Path
import platform
import sys
from typing import Any

import numpy as np

from atlas.compiled.compiler_identity import (
    COMPILER_VERSION,
    current_git_commit,
    current_git_dirty,
)
from atlas.compiled.feature_schema import current_feature_schema_hash
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)
from atlas.compiled.index import DEFAULT_INDEX_PATH, load_compiled_index
from atlas.validation.models import ExperimentConfig


VALIDATION_RESULT_SCHEMA = "atlas.validation.result.v1"
DEFAULT_VALIDATION_DIR = Path("output") / "validation"


@dataclass(frozen=True, slots=True)
class ExperimentProvenance:
    """Everything needed to say what a result was computed from."""

    schema_version: str
    experiment_id: str
    generated_at: str
    feature_schema_hash: str
    source_manifest_hash: str
    artifact_schema_version: str
    compiler_version: str
    git_commit: str
    git_dirty: bool
    python_version: str
    platform: str
    profile_count: int
    pair_count: int
    normalization_mode: str
    # Part of the reproduction contract: scores are bit-exact for a given
    # block size, and equal only to within a few ULPs across different ones,
    # because BLAS varies its summation order with matrix shape.
    block_size: int

    def to_dict(self) -> dict[str, Any]:
        """Return a JSON-safe representation."""
        return {
            "schema_version": self.schema_version,
            "experiment_id": self.experiment_id,
            "generated_at": self.generated_at,
            "corpus": {
                "feature_schema_hash": self.feature_schema_hash,
                "source_manifest_hash": self.source_manifest_hash,
                "artifact_schema_version": self.artifact_schema_version,
                "profile_count": self.profile_count,
                "pair_count": self.pair_count,
                "normalization_mode": self.normalization_mode,
                "block_size": self.block_size,
            },
            "build": {
                "compiler_version": self.compiler_version,
                "git_commit": self.git_commit,
                "git_dirty": self.git_dirty,
                "python_version": self.python_version,
                "platform": self.platform,
            },
        }


def build_provenance(
    config: ExperimentConfig,
    *,
    profile_count: int,
    pair_count: int,
    block_size: int,
    index_path: Path = DEFAULT_INDEX_PATH,
) -> ExperimentProvenance:
    """Capture the corpus and build identity behind a result."""
    try:
        source_manifest_hash = load_compiled_index(
            input_path=index_path
        ).source_manifest_hash
    except Exception:  # noqa: BLE001 - provenance must not abort a run
        source_manifest_hash = "unknown"

    return ExperimentProvenance(
        schema_version=VALIDATION_RESULT_SCHEMA,
        experiment_id=config.experiment_id,
        generated_at=datetime.now(UTC).isoformat(),
        feature_schema_hash=current_feature_schema_hash(),
        source_manifest_hash=source_manifest_hash,
        artifact_schema_version=COMPILED_IDENTITY_VECTOR_SCHEMA,
        compiler_version=COMPILER_VERSION,
        git_commit=current_git_commit(),
        git_dirty=current_git_dirty(),
        python_version=platform.python_version(),
        platform=platform.platform(),
        profile_count=profile_count,
        pair_count=pair_count,
        normalization_mode=config.normalization_mode,
        block_size=block_size,
    )


def experiment_dir(
    experiment_id: str,
    *,
    root: Path = DEFAULT_VALIDATION_DIR,
) -> Path:
    """Return the output directory for one experiment."""
    safe = experiment_id.strip()

    if not safe or safe in {".", ".."} or "/" in safe or "\\" in safe:
        raise ValueError(f"Unsafe experiment_id: {experiment_id!r}")

    return root / safe


def write_json(payload: dict[str, Any], path: Path) -> Path:
    """Write a JSON document atomically with canonical formatting."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")

    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)

    return path


def write_pairs(
    *,
    profile_keys: tuple[str, ...],
    pair_indices: np.ndarray,
    scores: np.ndarray,
    path: Path,
    metric: str,
    normalization_mode: str,
) -> Path:
    """Write pair scores to Parquet.

    Profile keys are stored as dictionary-encoded columns, which keeps the
    file small despite repeating each key roughly 2,000 times.
    """
    import pandas as pd

    path.parent.mkdir(parents=True, exist_ok=True)

    keys = np.asarray(profile_keys, dtype=object)

    frame = pd.DataFrame(
        {
            "profile_a": pd.Categorical(keys[pair_indices[:, 0]]),
            "profile_b": pd.Categorical(keys[pair_indices[:, 1]]),
            "score": scores.astype(np.float32),
        }
    )

    frame.attrs["metric"] = metric
    frame.attrs["normalization_mode"] = normalization_mode

    frame.to_parquet(path, index=False, compression="snappy")

    return path


def read_pairs(path: Path):
    """Read a pairs artifact back."""
    import pandas as pd

    return pd.read_parquet(path)
