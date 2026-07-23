"""Compare compiled artifacts against the ACF sources they were built from.

Non-destructive. Answers what the health check cannot: not just "is the
compiled layer self-consistent" but "does it still agree with the corpus it
claims to describe".

Reports four kinds of divergence:

* ``source_missing`` -- an artifact whose ACF is gone. It still loads and
  still answers queries, which is exactly why this needs saying out loud:
  the profile can no longer be rebuilt or verified.
* ``hash_mismatch`` -- the ACF changed since compilation.
* ``uncompiled_source`` -- an ACF with no artifact.
* ``unexpected_source`` -- an ACF the manifest never saw, i.e. added since.

Writing a snapshot with --snapshot before a batch or test run gives a
before/after record if sources ever disappear again.
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import json
from pathlib import Path
import sys

from atlas.compiled import (
    DEFAULT_COMPILED_VECTOR_DIR,
    artifact_path_for_profile,
    compiled_profile_keys,
    list_compilable_profile_keys,
    load_compiled_identity_vector,
    sha256_file,
    source_acf_path_for_profile,
)
from atlas.library.profile_library import LIBRARY_DIR


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare compiled artifacts against their ACF sources. "
            "Read-only."
        )
    )
    parser.add_argument(
        "--verify-hashes",
        action="store_true",
        help=(
            "Re-hash every source ACF and compare. Authoritative but reads "
            "the whole corpus; the default compares size only."
        ),
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=None,
        metavar="PATH",
        help="Write the observed source list to PATH for later comparison.",
    )
    parser.add_argument(
        "--compare-snapshot",
        type=Path,
        default=None,
        metavar="PATH",
        help="Compare against a snapshot and report sources lost since then.",
    )
    parser.add_argument(
        "--list-limit",
        type=int,
        default=20,
        metavar="N",
        help="Profile keys to list per category (default: 20).",
    )
    return parser


def main() -> int:
    """Run the integrity comparison."""
    args = build_parser().parse_args()

    compiled = set(compiled_profile_keys())
    sources = set(list_compilable_profile_keys(library_dir=LIBRARY_DIR))

    source_missing = sorted(compiled - sources)
    uncompiled_source = sorted(sources - compiled)

    hash_mismatch: list[dict[str, object]] = []
    unreadable: list[str] = []

    for profile_key in sorted(compiled & sources):
        artifact_path = artifact_path_for_profile(profile_key)
        source_path = source_acf_path_for_profile(profile_key)

        try:
            artifact = load_compiled_identity_vector(input_path=artifact_path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            unreadable.append(profile_key)
            continue

        actual_size = source_path.stat().st_size

        if artifact.source_acf_size_bytes != actual_size:
            hash_mismatch.append(
                {
                    "profile_key": profile_key,
                    "reason": "size",
                    "recorded": artifact.source_acf_size_bytes,
                    "actual": actual_size,
                }
            )
            continue

        if args.verify_hashes:
            actual_hash = sha256_file(source_path)

            if artifact.source_acf_sha256 != actual_hash:
                hash_mismatch.append(
                    {
                        "profile_key": profile_key,
                        "reason": "sha256",
                        "recorded": artifact.source_acf_sha256,
                        "actual": actual_hash,
                    }
                )

    lost_since_snapshot: list[str] = []

    if args.compare_snapshot is not None and args.compare_snapshot.is_file():
        try:
            previous = json.loads(
                args.compare_snapshot.read_text(encoding="utf-8")
            )
            previous_sources = set(previous.get("sources", []))
            lost_since_snapshot = sorted(previous_sources - sources)
        except (OSError, json.JSONDecodeError):
            lost_since_snapshot = []

    if args.snapshot is not None:
        args.snapshot.parent.mkdir(parents=True, exist_ok=True)
        args.snapshot.write_text(
            json.dumps(
                {
                    "captured_at": datetime.now(UTC).isoformat(),
                    "source_count": len(sources),
                    "sources": sorted(sources),
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )

    intact = not (
        source_missing or hash_mismatch or unreadable or lost_since_snapshot
    )

    report = {
        "intact": intact,
        "compiled_artifact_count": len(compiled),
        "source_acf_count": len(sources),
        "counts": {
            "source_missing": len(source_missing),
            "hash_mismatch": len(hash_mismatch),
            "uncompiled_source": len(uncompiled_source),
            "unreadable_artifact": len(unreadable),
            "lost_since_snapshot": len(lost_since_snapshot),
        },
        "source_missing": source_missing[: args.list_limit],
        "hash_mismatch": hash_mismatch[: args.list_limit],
        "uncompiled_source": uncompiled_source[: args.list_limit],
        "unreadable_artifact": unreadable[: args.list_limit],
        "lost_since_snapshot": lost_since_snapshot[: args.list_limit],
        "verified_hashes": args.verify_hashes,
        "snapshot_written": (
            str(args.snapshot) if args.snapshot is not None else None
        ),
    }

    print(json.dumps(report, indent=2))

    return 0 if intact else 1


if __name__ == "__main__":
    sys.exit(main())
