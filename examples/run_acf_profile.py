"""Generate one Atlas Codex Format profile."""

from pathlib import Path

from atlas.acf.builder import export_acf_profile


OUTPUT_DIR = Path("output/examples/acf")


def run_acf_profile(name: str) -> None:
    """Build and export one ACF profile."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_path = OUTPUT_DIR / f"{_safe_name(name)}.acf.json"

    export_acf_profile(
        name=name,
        output_path=output_path,
        entity_type="person",
    )

    print(f"Atlas Codex Format profile written to: {output_path}")


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
    run_acf_profile("Michael Elvis Brockway")