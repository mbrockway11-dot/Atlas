"""Regenerate missing profile.acf.json files from their saved intake records.

An ACF is derived data: it is built from the profile's name and birth data,
both of which are preserved in profile.intake.json. A profile directory that
has an intake record but no ACF can therefore be rebuilt exactly, without
guessing.

Reports what it would do by default. Pass --apply to write.

    python scripts/repair_missing_acf_profiles.py
    python scripts/repair_missing_acf_profiles.py --apply
    python scripts/repair_missing_acf_profiles.py --apply --profile-key nikola_tesla
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys
from time import perf_counter

from atlas.acf.builder import export_acf_profile
from atlas.birth import BirthData
from atlas.library.profile_library import LIBRARY_DIR


def normalize_intake(intake: dict) -> dict | None:
    """Return ``{name, birth_date, birth_time, birth_place, entity_type}``.

    Two intake schemas exist in the library and both must be readable, since
    an ACF can only be rebuilt from whatever its profile actually recorded:

    * flat -- ``{"name", "birth_date", "birth_time", "birth_place"}``
    * nested v1.0 -- ``{"identity": {"full_name"}, "birth": {"date", "time",
      "place"}}``

    Returns ``None`` when no usable name is present.
    """
    identity = intake.get("identity")
    birth = intake.get("birth")

    if isinstance(identity, dict) or isinstance(birth, dict):
        identity = identity if isinstance(identity, dict) else {}
        birth = birth if isinstance(birth, dict) else {}

        name = identity.get("full_name") or identity.get("display_name")
        date = birth.get("date")
        time = birth.get("time")
        place = birth.get("place")
        entity_type = identity.get("entity_type") or intake.get("entity_type")
    else:
        name = intake.get("name")
        date = intake.get("birth_date")
        time = intake.get("birth_time")
        place = intake.get("birth_place")
        entity_type = intake.get("entity_type")

    if not name:
        return None

    # Placeholders carry no information; an absent value is more honest than
    # a literal "Unknown" propagated into the rebuilt profile.
    def clean(value: object) -> str | None:
        text = str(value).strip() if value is not None else ""

        if not text or text.lower() in {"unknown", "n/a", "none"}:
            return None

        return text

    return {
        "name": str(name).strip(),
        "birth_date": clean(date),
        "birth_time": clean(time),
        "birth_place": clean(place),
        "entity_type": clean(entity_type) or "person",
    }


def find_repairable(
    library_dir: Path,
    profile_keys: list[str] | None = None,
) -> list[tuple[str, dict]]:
    """Return (profile_key, intake) for profiles missing an ACF."""
    if not library_dir.is_dir():
        return []

    candidates = (
        sorted(entry for entry in library_dir.iterdir() if entry.is_dir())
        if profile_keys is None
        else [library_dir / key for key in profile_keys]
    )

    repairable: list[tuple[str, dict]] = []

    for profile_dir in candidates:
        if not profile_dir.is_dir():
            continue

        if (profile_dir / "profile.acf.json").is_file():
            continue

        intake_path = profile_dir / "profile.intake.json"

        if not intake_path.is_file():
            continue

        try:
            intake = json.loads(intake_path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(intake, dict):
            continue

        normalized = normalize_intake(intake)

        if normalized is not None:
            repairable.append((profile_dir.name, normalized))

    return repairable


def rebuild_one(
    profile_dir: Path,
    intake: dict,
    *,
    force: bool = False,
) -> tuple[int, str]:
    """Rebuild one ACF from its intake record.

    Returns ``(bytes_written, action)``. Refuses to overwrite an existing ACF
    unless ``force`` is set: a regenerated profile is not always
    byte-identical to the original, so silently replacing real data with a
    rebuild would be a quiet downgrade.
    """
    birth_data = BirthData(
        date=intake["birth_date"],
        time=intake["birth_time"],
        location=intake["birth_place"],
    )

    output_path = profile_dir / "profile.acf.json"
    existed = output_path.is_file()

    if existed and not force:
        raise FileExistsError(
            f"{output_path} already exists; refusing to overwrite. "
            "Pass --force to replace it."
        )

    export_acf_profile(
        name=intake["name"],
        output_path=output_path,
        entity_type=intake["entity_type"],
        birth_data=birth_data,
    )

    return output_path.stat().st_size, ("overwrote" if existed else "created")


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Regenerate missing profile.acf.json files from saved intake "
            "records."
        )
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the files. Without this, only reports what is missing.",
    )
    parser.add_argument(
        "--profile-key",
        action="append",
        default=None,
        dest="profile_keys",
        metavar="KEY",
        help="Repair only this profile. May be repeated.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite an ACF that already exists. Off by default: a rebuilt "
            "profile is not guaranteed byte-identical to the original."
        ),
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        metavar="N",
        help="Repair at most N profiles.",
    )
    return parser


def main() -> int:
    """Report or repair missing ACF profiles."""
    args = build_parser().parse_args()

    repairable = find_repairable(LIBRARY_DIR, args.profile_keys)

    if args.limit is not None:
        repairable = repairable[: args.limit]

    if not args.apply:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "missing_acf_count": len(repairable),
                    "profile_keys": [key for key, _ in repairable],
                },
                indent=2,
            )
        )
        return 0

    started = perf_counter()
    repaired: list[dict] = []
    failures: list[dict] = []

    for profile_key, intake in repairable:
        try:
            written, action = rebuild_one(
                LIBRARY_DIR / profile_key,
                intake,
                force=args.force,
            )
        except Exception as exc:  # noqa: BLE001 - one failure must not abort
            failures.append(
                {
                    "profile_key": profile_key,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
            continue

        # Every write is logged, so a repair run leaves a record of exactly
        # which files it created or replaced.
        repaired.append(
            {
                "profile_key": profile_key,
                "bytes": written,
                "action": action,
                "path": str(LIBRARY_DIR / profile_key / "profile.acf.json"),
            }
        )

    print(
        json.dumps(
            {
                "dry_run": False,
                "requested": len(repairable),
                "repaired_count": len(repaired),
                "failed_count": len(failures),
                "elapsed_seconds": round(perf_counter() - started, 2),
                "repaired": repaired,
                "failures": failures,
            },
            indent=2,
        )
    )

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
