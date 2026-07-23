"""Compile one Atlas profile into a reusable identity-vector artifact."""

from __future__ import annotations

import argparse
import json
import sys

from atlas.compiled import compile_identity_vector_artifact


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Compile one saved Atlas ACF profile into a compact "
            "identity-vector artifact."
        )
    )
    parser.add_argument(
        "profile_key",
        help="Saved profile key, such as nikola_tesla.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Rebuild regardless of source hash.",
    )
    return parser


def main() -> int:
    """Run the single-profile compiler."""
    args = build_parser().parse_args()

    try:
        artifact, output_path, rebuilt = (
            compile_identity_vector_artifact(
                args.profile_key,
                force=args.force,
            )
        )
    except Exception as exc:  # noqa: BLE001
        print(
            json.dumps(
                {
                    "success": False,
                    "profile_key": args.profile_key,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                },
                indent=2,
            )
        )
        return 1

    print(
        json.dumps(
            {
                "success": True,
                "profile_key": artifact.profile_key,
                "profile_name": artifact.profile_name,
                "schema_version": artifact.schema_version,
                "compiler_version": artifact.compiler_version,
                "compiler_git_commit": artifact.compiler_git_commit,
                "source_acf_sha256": artifact.source_acf_sha256,
                "vector_count": artifact.vector_count,
                "output_path": str(output_path),
                "rebuilt": rebuilt,
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
