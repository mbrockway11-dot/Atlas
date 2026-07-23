"""Validate compiled identity-vector artifacts and rebuild the index.

Checks every compiled artifact against its source ACF and reports which are
current, stale, damaged, written against an older schema, or orphaned
(source ACF gone). Also reports profiles that have a source but no artifact.

Read-only by default. ``--rebuild-stale`` recompiles anything that is not
current; ``--write-index`` refreshes ``output/compiled/index.json``.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from atlas.compiled import (
    DEFAULT_COMPILED_VECTOR_DIR,
    EXPECTED_VECTOR_COUNT,
    artifact_path_for_profile,
    compile_identity_vector_artifact,
    compiled_artifact_is_current,
    list_compilable_profile_keys,
    load_compiled_identity_vector,
    source_acf_path_for_profile,
)
from atlas.compiled.index import (
    DEFAULT_INDEX_PATH,
    build_compiled_index,
    save_compiled_index,
)
from atlas.compiled.identity_vector_artifact import (
    COMPILED_IDENTITY_VECTOR_SCHEMA,
)
from atlas.library.profile_library import LIBRARY_DIR


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Validate compiled identity-vector artifacts against their "
            "source ACFs."
        )
    )
    parser.add_argument(
        "--artifact-dir",
        type=Path,
        default=DEFAULT_COMPILED_VECTOR_DIR,
        metavar="PATH",
        help=f"Artifact directory (default: {DEFAULT_COMPILED_VECTOR_DIR}).",
    )
    parser.add_argument(
        "--rebuild-stale",
        action="store_true",
        help="Recompile every artifact that is not current.",
    )
    parser.add_argument(
        "--write-index",
        action="store_true",
        help=f"Rebuild {DEFAULT_INDEX_PATH} after validating.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=DEFAULT_INDEX_PATH,
        metavar="PATH",
        help=f"Where to write the index (default: {DEFAULT_INDEX_PATH}).",
    )
    parser.add_argument(
        "--list-limit",
        type=int,
        default=20,
        metavar="N",
        help="How many profile keys to list per category (default: 20).",
    )
    return parser


def classify(profile_key: str, artifact_dir: Path) -> str:
    """Return the validation state of one profile's artifact."""
    artifact_path = artifact_path_for_profile(
        profile_key,
        output_dir=artifact_dir,
    )
    source_path = source_acf_path_for_profile(profile_key)

    if not artifact_path.is_file():
        return "missing"

    try:
        artifact = load_compiled_identity_vector(input_path=artifact_path)
    except ValueError as exc:
        # from_dict rejects both unknown schemas and structural damage.
        if "schema" in str(exc).lower():
            return "old_schema"

        return "damaged"
    except (json.JSONDecodeError, KeyError, TypeError):
        return "damaged"

    if not source_path.is_file():
        return "orphaned"

    if artifact.schema_version != COMPILED_IDENTITY_VECTOR_SCHEMA:
        return "old_schema"

    if not compiled_artifact_is_current(artifact, source_path):
        return "stale"

    return "current"


def main() -> int:
    """Validate the compiled corpus."""
    args = build_parser().parse_args()

    profile_keys = list_compilable_profile_keys(library_dir=LIBRARY_DIR)

    states: dict[str, list[str]] = {
        "current": [],
        "missing": [],
        "stale": [],
        "damaged": [],
        "old_schema": [],
        "orphaned": [],
    }

    for profile_key in profile_keys:
        states[classify(profile_key, args.artifact_dir)].append(profile_key)

    rebuilt: list[str] = []
    rebuild_failures: list[dict[str, str]] = []

    if args.rebuild_stale:
        needs_rebuild = (
            states["missing"]
            + states["stale"]
            + states["damaged"]
            + states["old_schema"]
        )

        for profile_key in needs_rebuild:
            try:
                compile_identity_vector_artifact(profile_key, force=True)
            except Exception as exc:  # noqa: BLE001
                rebuild_failures.append(
                    {
                        "profile_key": profile_key,
                        "error_type": type(exc).__name__,
                        "error": str(exc),
                    }
                )
                continue

            rebuilt.append(profile_key)

    index_summary = None

    if args.write_index:
        index = build_compiled_index(artifact_dir=args.artifact_dir)
        index_path = save_compiled_index(index, output_path=args.index_path)

        index_summary = {
            "index_path": str(index_path),
            "profile_count": index.profile_count,
            "total_vector_count": index.total_vector_count,
            "total_artifact_bytes": index.total_artifact_bytes,
            "source_manifest_hash": index.source_manifest_hash,
            "entity_type_counts": index.entity_type_counts(),
            "irregular_vector_counts": list(
                index.irregular_keys(EXPECTED_VECTOR_COUNT)
            )[: args.list_limit],
        }

    healthy = not any(
        states[name]
        for name in ("missing", "stale", "damaged", "old_schema")
    )

    report = {
        "healthy": healthy and not rebuild_failures,
        "artifact_schema_version": COMPILED_IDENTITY_VECTOR_SCHEMA,
        "profiles_checked": len(profile_keys),
        "counts": {name: len(keys) for name, keys in states.items()},
        "samples": {
            name: keys[: args.list_limit]
            for name, keys in states.items()
            if name != "current" and keys
        },
        "rebuilt_count": len(rebuilt),
        "rebuild_failures": rebuild_failures,
        "index": index_summary,
    }

    print(json.dumps(report, indent=2))

    return 0 if report["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
