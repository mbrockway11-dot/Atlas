"""Kamea projection functions."""

from atlas.kamea.path import KameaPath
from atlas.kamea.squares import KAMEAS


def get_kamea(kamea_name: str):
    """Return a planetary Kamea by key."""
    key = kamea_name.lower().strip()

    if key not in KAMEAS:
        available = ", ".join(sorted(KAMEAS))
        raise ValueError(f"Unknown Kamea '{kamea_name}'. Available: {available}")

    return KAMEAS[key]


def project_values_to_kamea(
    values: list[int],
    kamea_name: str,
    use_planetary_transform: bool = False,
) -> KameaPath:
    """Project values into a selected planetary Kamea."""
    kamea = get_kamea(kamea_name)

    return kamea.project_values(
        values,
        use_planetary_transform=use_planetary_transform,
    )


def project_values_to_all_kameas(
    values: list[int],
    use_planetary_transform: bool = False,
) -> dict[str, KameaPath]:
    """Project values into all planetary Kameas."""
    return {
        key: kamea.project_values(
            values,
            use_planetary_transform=use_planetary_transform,
        )
        for key, kamea in KAMEAS.items()
    }