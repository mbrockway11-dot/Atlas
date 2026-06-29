"""Build Atlas ACF profiles from TXT or CSV intake datasets."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from atlas.acf.builder import export_acf_profile
from atlas.datasets import (
    IdentityRecord,
    dataset_load_result_to_dict,
    load_dataset,
)


DEFAULT_INPUT = "research/profile_intake/names.txt"
DEFAULT_OUTPUT = "output/library/profiles"


def main() -> None:
    """Build profiles from TXT or CSV intake file."""
    parser = argparse.ArgumentParser(
        description="Build Atlas profiles from TXT or CSV intake datasets."
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Input TXT or CSV dataset.",
    )

    parser.add_argument(
        "--output",
        default=DEFAULT_OUTPUT,
        help="Output profile library directory.",
    )

    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing profile.acf.json files.",
    )

    parser.add_argument(
        "--report",
        default="output/dataset_load_report.json",
        help="Dataset load validation report path.",
    )

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)
    report_path = Path(args.report)

    if not input_path.exists():
        raise FileNotFoundError(f"Intake file not found: {input_path}")

    load_result = load_dataset(input_path)
    records = load_result.records

    if not records:
        raise ValueError(f"No valid records found in {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    report_path.write_text(
        json.dumps(
            dataset_load_result_to_dict(load_result),
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )

    built = 0
    skipped = 0
    failed = 0

    print("")
    print("Atlas Batch Profile Builder")
    print("=" * 56)
    print(f"Input:   {input_path}")
    print(f"Output:  {output_dir}")
    print(f"Report:  {report_path}")
    print(f"Records: {len(records)}")
    print(f"Issues:  {len(load_result.issues)}")
    print("")

    for record in records:
        slug = slugify_name(record.name)
        profile_dir = output_dir / slug
        acf_path = profile_dir / "profile.acf.json"
        metadata_path = profile_dir / "profile.intake.json"

        if acf_path.exists() and not args.overwrite:
            skipped += 1
            print(f"SKIP  {record.name} -> {acf_path}")
            continue

        profile_dir.mkdir(parents=True, exist_ok=True)

        try:
            export_acf_profile(
                name=record.name,
                output_path=acf_path,
            )

            metadata_path.write_text(
                json.dumps(
                    identity_record_to_metadata(record),
                    indent=2,
                    sort_keys=True,
                ),
                encoding="utf-8",
            )

            built += 1
            print(f"BUILT {record.name} -> {acf_path}")

        except Exception as error:
            failed += 1
            print(f"FAIL  {record.name}: {error}")

    print("")
    print("Batch complete")
    print("=" * 56)
    print(f"Built:   {built}")
    print(f"Skipped: {skipped}")
    print(f"Failed:  {failed}")


def identity_record_to_metadata(
    record: IdentityRecord,
) -> dict[str, str | int]:
    """Convert IdentityRecord to saved intake metadata."""
    return {
        "name": record.name,
        "birth_date": record.birth_date,
        "birth_time": record.birth_time,
        "birth_place": record.birth_place,
        "source_file": record.source_file,
        "row_number": record.row_number,
    }


def slugify_name(name: str) -> str:
    """Convert a profile name to a safe folder slug."""
    slug = name.casefold().strip()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_")


if __name__ == "__main__":
    main()