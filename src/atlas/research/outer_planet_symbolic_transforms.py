"""Disabled outer-planet symbolic hypotheses for non-canonical research.

These declarations are experiment proposals, not astronomical measurements.
The canonical CSS compiler does not import or execute this module.
"""

from __future__ import annotations

from typing import Any


OUTER_PLANET_SYMBOLIC_HYPOTHESES = {
    "Uranus": {
        "hypothesis": "rewiring",
        "enabled": False,
        "canonical": False,
    },
    "Neptune": {
        "hypothesis": "diffusion",
        "enabled": False,
        "canonical": False,
    },
    "Pluto": {
        "hypothesis": "pruning_or_persistence",
        "enabled": False,
        "canonical": False,
    },
}


def disabled_outer_planet_transform_registry() -> dict[str, Any]:
    """Return inert experiment metadata without transforming any graph."""
    return {
        "status": "disabled",
        "execution_allowed_in_canonical_css": False,
        "transforms": {
            body: dict(specification)
            for body, specification in OUTER_PLANET_SYMBOLIC_HYPOTHESES.items()
        },
    }


__all__ = [
    "OUTER_PLANET_SYMBOLIC_HYPOTHESES",
    "disabled_outer_planet_transform_registry",
]
