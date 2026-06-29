"""Build one interpretation-ready Atlas profile summary JSON."""

from pathlib import Path

from atlas.export.json import write_json
from atlas.profiles.summary import build_individual_profile_summary


OUTPUT_DIR = Path("output/examples/profile_summary")


def run_profile_summary(name: str) -> None:
    """Build and export one complete Atlas profile summary."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = build_individual_profile_summary(name)

    output_path = OUTPUT_DIR / f"{_safe_name(name)}_profile_summary.json"
    write_json(summary, output_path)

    print(f"Profile summary written to: {output_path}")


def _safe_name(name: str) -> str:
    """Create a safe lowercase filename stem."""
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )


if __name__ == "__main__":
    run_profile_summary("Michael Elvis Brockway")