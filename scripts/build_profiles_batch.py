"""Build Atlas ACF profiles from a batch name list."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from atlas.acf.builder import export_acf_profile


DEFAULT_INPUT = "research/profile_intake/names.txt"
DEFAULT_OUTPUT = "output/library/profiles"


def main() -> None:
    """Build profiles from one-name-per-line input file."""
    parser = argparse.ArgumentParser(
        description="Build Atlas profiles from a batch name list."
    )

    parser.add_argument(
        "--input",
        default=DEFAULT_INPUT,
        help="Text file containing one profile name per line.",
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

    args = parser.parse_args()

    input_path = Path(args.input)
    output_dir = Path(args.output)

    if not input_path.exists():
        raise FileNotFoundError(f"Name intake file not found: {input_path}")

    names = load_names(input_path)

    if not names:
        raise ValueError(f"No names found in {input_path}")

    output_dir.mkdir(parents=True, exist_ok=True)

    built = 0
    skipped = 0

    print("")
    print("Atlas Batch Profile Builder")
    print("=" * 56)
    print(f"Input: {input_path}")
    print(f"Output: {output_dir}")
    print(f"Names: {len(names)}")
    print("")

    for name in names:
        slug = slugify_name(name)
        profile_dir = output_dir / slug
        acf_path = profile_dir / "profile.acf.json"

        if acf_path.exists() and not args.overwrite:
            skipped += 1
            print(f"SKIP  {name} -> {acf_path}")
            continue

        profile_dir.mkdir(parents=True, exist_ok=True)

        export_acf_profile(
            name=name,
            output_path=acf_path,
        )

        built += 1
        print(f"BUILT {name} -> {acf_path}")

    print("")
    print("Batch complete")
    print("=" * 56)
    print(f"Built:   {built}")
    print(f"Skipped: {skipped}")


def load_names(path: Path) -> list[str]:
    """Load one name per line, ignoring blanks and comments."""
    names = []

    for line in path.read_text(encoding="utf-8").splitlines():
        cleaned = line.strip()

        if not cleaned:
            continue

        if cleaned.startswith("#"):
            continue

        names.append(cleaned)

    return dedupe_preserve_order(names)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    """Deduplicate values while preserving input order."""
    seen = set()
    deduped = []

    for value in values:
        key = value.casefold()

        if key in seen:
            continue

        seen.add(key)
        deduped.append(value)

    return deduped


def slugify_name(name: str) -> str:
    """Convert a profile name to a safe folder slug."""
    slug = name.casefold().strip()
    slug = re.sub(r"[^\w\s-]", "", slug, flags=re.UNICODE)
    slug = re.sub(r"[\s_-]+", "_", slug)
    return slug.strip("_")


if __name__ == "__main__":
    main()