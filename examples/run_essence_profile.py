"""Generate one Atlas essence profile."""

from pathlib import Path

from atlas.essence.profile import build_essence_profile


OUTPUT_DIR = Path("output/examples/essence")


def run_essence_profile(name: str) -> None:
    """Build one essence profile."""
    output_dir = OUTPUT_DIR / _safe_name(name)

    paths = build_essence_profile(name, output_dir)

    print(f"Essence graph written to: {paths['json']}")
    print(f"Essence 3D SVG written to: {paths['svg']}")


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
    run_essence_profile("Michael Elvis Brockway")