"""Parent-engine path and contract resolution."""

from __future__ import annotations

from pathlib import Path


ENGINE_ROOT = Path(
    "src/atlas/investment/alpha/engines"
)


def resolve_parent_engine_file(
    engine_id: str,
) -> str:
    """Resolve the likely parent-engine implementation file."""
    stem = normalize_engine_stem(
        engine_id
    )

    direct = (
        ENGINE_ROOT
        / f"{stem}.py"
    )

    if direct.exists():
        return str(direct)

    candidates = sorted(
        ENGINE_ROOT.glob("*.py")
    )

    for candidate in candidates:
        if stem in candidate.stem:
            return str(candidate)

    return str(direct)


def resolve_parent_test_file(
    engine_id: str,
) -> str:
    """Resolve the preferred variant test target."""
    stem = normalize_engine_stem(
        engine_id
    )

    return str(
        Path("tests")
        / f"test_{stem}_variant.py"
    )


def normalize_engine_stem(
    engine_id: str,
) -> str:
    value = str(
        engine_id
    ).strip()

    if value.endswith("_v1"):
        value = value[:-3]

    return value
