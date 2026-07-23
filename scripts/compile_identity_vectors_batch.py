"""Compile the entire Atlas profile library into vector artifacts.

Discovers saved profiles, compiles each into a schema-v2 identity-vector
artifact (reusing artifacts whose source ACF is unchanged), writes a
compilation manifest, and prints a concise report. One broken profile
does not abort the batch unless ``--fail-fast`` is given.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas.compiled import (
    DEFAULT_MANIFEST_PATH,
    EXPECTED_VECTOR_COUNT,
    compile_identity_vector_library,
)
from atlas.library.profile_library import LIBRARY_DIR


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Compile saved Atlas ACF profiles into compact identity-vector "
            "artifacts and write a compilation manifest."
        )
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild every artifact regardless of source hash.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Compile at most N profiles.",
    )
    parser.add_argument(
        "--profile-key",
        action="append",
        default=None,
        dest="profile_keys",
        metavar="KEY",
        help=(
            "Compile only this profile key. May be given multiple times. "
            "When omitted, the whole saved-profile library is compiled."
        ),
    )
    parser.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop after the first profile that fails to compile.",
    )
    parser.add_argument(
        "--include-sourceless",
        action="store_true",
        help=(
            "Also request saved profile keys that have no ACF source. "
            "By default the library is scanned for profiles that actually "
            "have a profile.acf.json, so registry entries without an export "
            "are skipped instead of recorded as failures."
        ),
    )
    parser.add_argument(
        "--manifest-path",
        "--report-path",
        type=Path,
        default=DEFAULT_MANIFEST_PATH,
        dest="manifest_path",
        metavar="PATH",
        help=(
            "Where to write the compilation manifest "
            f"(default: {DEFAULT_MANIFEST_PATH})."
        ),
    )
    return parser


def main() -> int:
    """Run the batch library compiler."""
    args = build_parser().parse_args()

    # Explicit keys win; otherwise scan the library so that registry
    # entries without an exported ACF are skipped rather than failed.
    library_dir = (
        None
        if args.profile_keys or args.include_sourceless
        else LIBRARY_DIR
    )

    result = compile_identity_vector_library(
        profile_keys=args.profile_keys,
        force=args.force,
        limit=args.limit,
        fail_fast=args.fail_fast,
        write_manifest=True,
        manifest_path=args.manifest_path,
        library_dir=library_dir,
    )

    manifest = result.manifest
    irregular = result.irregular_outcomes()

    report = {
        "success": manifest.failed_count == 0,
        "compiler_version": manifest.compiler_version,
        "compiler_git_commit": manifest.compiler_git_commit,
        "artifact_schema_version": manifest.artifact_schema_version,
        "requested_count": manifest.requested_count,
        "successful_count": manifest.successful_count,
        "rebuilt_count": manifest.rebuilt_count,
        "reused_count": manifest.reused_count,
        "failed_count": manifest.failed_count,
        "total_vector_count": manifest.total_vector_count,
        "total_source_bytes": manifest.total_source_bytes,
        "total_artifact_bytes": manifest.total_artifact_bytes,
        "storage_reduction_percent": round(
            manifest.storage_reduction_percent, 2
        ),
        "elapsed_seconds": round(manifest.elapsed_seconds, 2),
        "profiles_per_second": round(manifest.profiles_per_second, 2),
        "expected_vector_count": EXPECTED_VECTOR_COUNT,
        "irregular_vector_profiles": [
            {
                "profile_key": outcome.profile_key,
                "vector_count": outcome.vector_count,
            }
            for outcome in irregular
        ],
        "failures": list(manifest.failures),
        "manifest_path": str(args.manifest_path),
    }

    print(json.dumps(report, indent=2))

    return 1 if manifest.failed_count else 0


if __name__ == "__main__":
    sys.exit(main())
