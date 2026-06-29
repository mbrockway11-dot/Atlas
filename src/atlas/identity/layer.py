"""Identity graph layer objects."""

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class IdentityLayer:
    """One of the 21 identity topology layers."""

    layer_id: str
    cipher: str
    planet: str
    kamea: str
    grid_size: int
    sequence: dict[str, Any]
    features: dict[str, Any]
    subtype: dict[str, Any]
    kamea_score: float
    planetary_function: str


def identity_layer_to_dict(layer: IdentityLayer) -> dict[str, Any]:
    """Convert identity layer to JSON-safe dictionary."""
    return {
        "layer_id": layer.layer_id,
        "cipher": layer.cipher,
        "planet": layer.planet,
        "kamea": layer.kamea,
        "grid_size": layer.grid_size,
        "sequence": layer.sequence,
        "features": layer.features,
        "subtype": layer.subtype,
        "kamea_score": layer.kamea_score,
        "planetary_function": layer.planetary_function,
    }