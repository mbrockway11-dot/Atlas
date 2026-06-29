"""Build interpretation-ready Atlas profile summary and interpretation JSON."""

from pathlib import Path

from atlas.export.json import write_json
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.profiles.summary import build_individual_profile_summary


OUTPUT_DIR = Path("output/examples/profile_interpretation")


def run_profile_interpretation(name: str) -> None:
    """Build and export profile summary plus deterministic interpretation."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = build_individual_profile_summary(name)
    interpretation = interpret_profile_summary(summary)

    summary_path = OUTPUT_DIR / f"{_safe_name(name)}_profile_summary.json"
    interpretation_path = OUTPUT_DIR / f"{_safe_name(name)}_profile_interpretation.json"

    write_json(summary, summary_path)
    write_json(profile_interpretation_to_dict(interpretation), interpretation_path)

    print(f"Profile summary written to: {summary_path}")
    print(f"Profile interpretation written to: {interpretation_path}")

    print("\nSummary:")
    for line in interpretation.summary_lines:
        print(f"- {line}")


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
    run_profile_interpretation("Michael Elvis Brockway")