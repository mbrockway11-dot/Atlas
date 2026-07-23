"""Build the consolidated calibration corpus and normalization statistics.

Reads the per-profile compiled identity-vector artifacts -- never the source
ACFs -- and writes:

* ``output/compiled/calibration/raw-vectors.json``
* ``output/compiled/calibration/feature-statistics.json``

Both carry a source-manifest hash so Atlas can tell when the corpus has
moved on and the derived artifacts must be rebuilt.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from time import perf_counter

from atlas.compiled import (
    DEFAULT_CALIBRATION_VECTORS_PATH,
    DEFAULT_COMPILED_VECTOR_DIR,
    DEFAULT_FEATURE_STATISTICS_PATH,
    build_calibration_statistics,
    build_calibration_vector_artifact,
    save_calibration_statistics,
    save_calibration_vectors,
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Consolidate compiled identity-vector artifacts into a single "
            "calibration corpus and precompute normalization statistics."
        )
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_COMPILED_VECTOR_DIR,
        metavar="PATH",
        help=(
            "Directory of compiled identity-vector artifacts "
            f"(default: {DEFAULT_COMPILED_VECTOR_DIR})."
        ),
    )
    parser.add_argument(
        "--vectors-path",
        type=Path,
        default=DEFAULT_CALIBRATION_VECTORS_PATH,
        metavar="PATH",
        help=(
            "Where to write the consolidated calibration corpus "
            f"(default: {DEFAULT_CALIBRATION_VECTORS_PATH})."
        ),
    )
    parser.add_argument(
        "--statistics-path",
        type=Path,
        default=DEFAULT_FEATURE_STATISTICS_PATH,
        metavar="PATH",
        help=(
            "Where to write the normalization statistics "
            f"(default: {DEFAULT_FEATURE_STATISTICS_PATH})."
        ),
    )
    parser.add_argument(
        "--skip-vectors",
        action="store_true",
        help=(
            "Only write the statistics artifact. The consolidated corpus is "
            "much larger and is not needed once statistics exist."
        ),
    )
    return parser


def main() -> int:
    """Build and persist the calibration artifacts."""
    args = build_parser().parse_args()

    started = perf_counter()

    corpus = build_calibration_vector_artifact(
        artifact_dir=args.artifact_dir,
    )

    if corpus.vector_count == 0:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        "No compiled identity-vector artifacts found in "
                        f"{args.artifact_dir}. Run "
                        "scripts/compile_identity_vectors_batch.py first."
                    ),
                },
                indent=2,
            )
        )
        return 1

    statistics = build_calibration_statistics(
        corpus.vectors,
        source_manifest_hash_value=corpus.source_manifest_hash,
        profile_count=corpus.profile_count,
    )

    statistics_path = save_calibration_statistics(
        statistics,
        output_path=args.statistics_path,
    )

    vectors_path = (
        None
        if args.skip_vectors
        else save_calibration_vectors(corpus, output_path=args.vectors_path)
    )

    elapsed = perf_counter() - started

    report = {
        "success": True,
        "source_manifest_hash": corpus.source_manifest_hash,
        "profile_count": corpus.profile_count,
        "vector_count": corpus.vector_count,
        "feature_count": len(corpus.feature_schema),
        "group_count": len(statistics.groups),
        "statistics_path": str(statistics_path),
        "statistics_bytes": statistics_path.stat().st_size,
        "vectors_path": str(vectors_path) if vectors_path else None,
        "vectors_bytes": (
            vectors_path.stat().st_size if vectors_path else 0
        ),
        "elapsed_seconds": round(elapsed, 2),
    }

    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
