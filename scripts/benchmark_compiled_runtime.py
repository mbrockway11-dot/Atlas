"""Benchmark each stage of the Atlas compiled runtime.

Measures what a comparison request actually costs now, and -- with
``--include-legacy`` -- what the old full-ACF calibration path costs for the
same population. The point of the compiled layer is that runtime stops
scaling with the size of the source corpus, so the legacy figure is
extrapolated from a sample rather than paid in full by default.
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
    DEFAULT_MANIFEST_PATH,
    compiled_profile_keys,
    load_calibration_statistics,
    load_calibration_vectors_from_artifacts,
    load_compiled_identity_vector,
)
from atlas.compiled.index import DEFAULT_INDEX_PATH, load_compiled_index
from atlas.compiled.runtime import (
    build_runtime_identity_vector,
    clear_runtime_caches,
)
from atlas.ive import build_raw_vectors_from_acf
from atlas.library.profile_library import LIBRARY_DIR


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Benchmark the Atlas compiled runtime stage by stage."
    )
    parser.add_argument(
        "--profile-a",
        default="nikola_tesla",
        metavar="KEY",
        help="First profile for comparison benchmarks.",
    )
    parser.add_argument(
        "--profile-b",
        default="isaac_newton",
        metavar="KEY",
        help="Second profile for comparison benchmarks.",
    )
    parser.add_argument(
        "--mode",
        default="percentile",
        choices=["raw", "percentile", "minmax", "zscore"],
        help="Normalization mode for comparison benchmarks.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=20,
        metavar="N",
        help="Iterations for warm measurements (default: 20).",
    )
    parser.add_argument(
        "--include-legacy",
        action="store_true",
        help=(
            "Also sample the old ACF calibration path and extrapolate it "
            "to the whole corpus. Reads real ACFs, so it is slow."
        ),
    )
    parser.add_argument(
        "--legacy-sample",
        type=int,
        default=25,
        metavar="N",
        help="ACFs to sample for the legacy estimate (default: 25).",
    )
    return parser


def _time(callable_, repeat: int = 1) -> tuple[float, object]:
    """Return the mean seconds per call and the last result."""
    started = perf_counter()
    result = None

    for _ in range(max(1, repeat)):
        result = callable_()

    return (perf_counter() - started) / max(1, repeat), result


def _legacy_estimate(sample_size: int) -> dict[str, object]:
    """Sample real ACFs and extrapolate the old calibration cost."""
    keys = compiled_profile_keys()
    sampled = 0
    total_bytes = 0
    started = perf_counter()

    for profile_key in keys[:sample_size]:
        acf_path = LIBRARY_DIR / profile_key / "profile.acf.json"

        if not acf_path.is_file():
            continue

        payload = acf_path.read_bytes()
        total_bytes += len(payload)

        acf = json.loads(payload.decode("utf-8-sig"))
        build_raw_vectors_from_acf(acf)
        sampled += 1

    elapsed = perf_counter() - started

    if not sampled:
        return {"available": False}

    per_profile = elapsed / sampled

    return {
        "available": True,
        "sampled_profiles": sampled,
        "sampled_bytes": total_bytes,
        "seconds_per_profile": round(per_profile, 6),
        "corpus_profiles": len(keys),
        "estimated_full_corpus_seconds": round(
            per_profile * len(keys), 2
        ),
        "estimated_full_corpus_bytes": int(
            (total_bytes / sampled) * len(keys)
        ),
    }


def main() -> int:
    """Run the benchmark suite."""
    args = build_parser().parse_args()

    keys = compiled_profile_keys()

    if not keys:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        "No compiled artifacts found. Run "
                        "scripts/compile_identity_vectors_batch.py first."
                    ),
                },
                indent=2,
            )
        )
        return 1

    stages: dict[str, object] = {}

    # --- single artifact -------------------------------------------------
    clear_runtime_caches()
    seconds, _ = _time(
        lambda: load_compiled_identity_vector(args.profile_a),
        args.repeat,
    )
    stages["single_artifact_load"] = round(seconds, 6)

    seconds, _ = _time(
        lambda: (
            load_compiled_identity_vector(args.profile_a),
            load_compiled_identity_vector(args.profile_b),
        ),
        args.repeat,
    )
    stages["two_artifact_loads"] = round(seconds, 6)

    # --- calibration surfaces --------------------------------------------
    seconds, statistics = _time(load_calibration_statistics)
    stages["statistics_only_load"] = round(seconds, 6)

    seconds, corpus_vectors = _time(load_calibration_vectors_from_artifacts)
    stages["full_compiled_corpus_load"] = round(seconds, 6)

    if DEFAULT_CALIBRATION_VECTORS_PATH.is_file():
        from atlas.compiled import load_calibration_vectors

        seconds, _ = _time(load_calibration_vectors)
        stages["consolidated_calibration_load"] = round(seconds, 6)
    else:
        stages["consolidated_calibration_load"] = None

    if DEFAULT_INDEX_PATH.is_file():
        seconds, index = _time(load_compiled_index)
        stages["compiled_index_load"] = round(seconds, 6)
    else:
        index = None
        stages["compiled_index_load"] = None

    # --- comparisons ------------------------------------------------------
    def _comparison() -> None:
        build_runtime_identity_vector(
            args.profile_a,
            normalization_mode=args.mode,
        )
        build_runtime_identity_vector(
            args.profile_b,
            normalization_mode=args.mode,
        )

    clear_runtime_caches()
    seconds, _ = _time(_comparison)
    stages["cold_first_comparison"] = round(seconds, 6)

    seconds, _ = _time(_comparison, args.repeat)
    stages["warm_repeated_comparison"] = round(seconds, 6)

    report: dict[str, object] = {
        "success": True,
        "normalization_mode": args.mode,
        "repeat": args.repeat,
        "corpus": {
            "compiled_profiles": len(keys),
            "calibration_vectors": len(corpus_vectors),
            "statistics_groups": len(statistics.groups),
            "artifact_dir": str(DEFAULT_COMPILED_VECTOR_DIR),
            "statistics_bytes": (
                DEFAULT_FEATURE_STATISTICS_PATH.stat().st_size
                if DEFAULT_FEATURE_STATISTICS_PATH.is_file()
                else 0
            ),
            "total_artifact_bytes": (
                index.total_artifact_bytes if index else None
            ),
        },
        "stages_seconds": stages,
    }

    if DEFAULT_MANIFEST_PATH.is_file():
        manifest = json.loads(
            DEFAULT_MANIFEST_PATH.read_text(encoding="utf-8")
        )
        report["corpus"]["total_source_bytes"] = manifest.get(
            "total_source_bytes"
        )
        report["corpus"]["storage_reduction_percent"] = round(
            manifest.get("storage_reduction_percent", 0.0), 2
        )

    if args.include_legacy:
        legacy = _legacy_estimate(args.legacy_sample)
        report["legacy_acf_calibration"] = legacy

        warm = stages["warm_repeated_comparison"]

        if legacy.get("available") and warm:
            report["speedup_vs_legacy_calibration"] = round(
                legacy["estimated_full_corpus_seconds"] / warm, 1
            )

    print(json.dumps(report, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
