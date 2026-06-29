"""Generate an Atlas Codex markdown report."""

from pathlib import Path

from atlas.export.json import write_json
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report, write_markdown_report


OUTPUT_DIR = Path("output/examples/codex_report")


def run_codex_report(name: str) -> None:
    """Generate summary JSON, interpretation JSON, and markdown Codex report."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    summary = build_individual_profile_summary(name)
    interpretation = interpret_profile_summary(summary)
    report = build_profile_markdown_report(summary, interpretation)

    safe = _safe_name(name)

    summary_path = OUTPUT_DIR / f"{safe}_profile_summary.json"
    interpretation_path = OUTPUT_DIR / f"{safe}_profile_interpretation.json"
    report_path = OUTPUT_DIR / f"{safe}_codex_report.md"

    write_json(summary, summary_path)
    write_json(profile_interpretation_to_dict(interpretation), interpretation_path)
    write_markdown_report(report, report_path)

    print(f"Profile summary written to: {summary_path}")
    print(f"Profile interpretation written to: {interpretation_path}")
    print(f"Codex report written to: {report_path}")


def _safe_name(name: str) -> str:
    """Create safe lowercase filename stem."""
    return (
        name.lower()
        .strip()
        .replace(" ", "_")
        .replace("-", "_")
        .replace("'", "")
    )


if __name__ == "__main__":
    run_codex_report("Michael Elvis Brockway")