"""Compile Structural Codices and readiness notes for the Atlas library."""

from __future__ import annotations

import argparse
import json

from atlas.library.profile_library import list_saved_profiles
from atlas.services.bulk_profile_codex_service import run_bulk_profile_codex


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--no-resume", action="store_true")
    parser.add_argument("--rebuild-existing", action="store_true")
    parser.add_argument("--checkpoint-every", type=int, default=25)
    args = parser.parse_args()

    keys = list_saved_profiles()
    if args.limit is not None:
        keys = keys[: max(args.limit, 0)]
    report = run_bulk_profile_codex(
        profile_keys=keys,
        resume=not args.no_resume,
        rebuild_existing=args.rebuild_existing,
        checkpoint_every=args.checkpoint_every,
    )
    print(json.dumps({
        "requested_profile_count": report.get("requested_profile_count"),
        "audited_profile_count": report.get("audited_profile_count"),
        "failed_profile_count": report.get("failed_profile_count"),
        "status_counts": report.get("status_counts"),
        "missing_field_counts": report.get("missing_field_counts"),
        "outputs": report.get("outputs"),
    }, indent=2))


if __name__ == "__main__":
    main()
