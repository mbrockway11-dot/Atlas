"""Atlas data provenance utilities."""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any


PROVENANCE_MODULES = {
    "active_cipher_engine": "atlas.ciphers",
    "data_cipher_ordinal": "data.ciphers.ordinal",
    "data_cipher_hebrew_literal": "data.ciphers.hebrew_literal",
    "data_cipher_hebrew_phonetic": "data.ciphers.hebrew_phonetic",
    "data_kamea_saturn": "data.historical.kamea.saturn",
    "data_kamea_jupiter": "data.historical.kamea.jupiter",
    "data_kamea_mars": "data.historical.kamea.mars",
    "data_kamea_sun": "data.historical.kamea.sun",
    "data_kamea_venus": "data.historical.kamea.venus",
    "data_kamea_mercury": "data.historical.kamea.mercury",
    "data_kamea_moon": "data.historical.kamea.moon",
}


def build_provenance_report() -> dict[str, Any]:
    """Build a report showing which Atlas data modules are importable."""
    modules = {}

    for label, module_name in PROVENANCE_MODULES.items():
        modules[label] = inspect_module(module_name)

    return {
        "module_count": len(modules),
        "modules": modules,
        "all_available": all(item["available"] for item in modules.values()),
    }


def inspect_module(module_name: str) -> dict[str, Any]:
    """Inspect whether a module is importable and where it is loaded from."""
    try:
        module = importlib.import_module(module_name)
    except Exception as error:
        return {
            "module": module_name,
            "available": False,
            "path": None,
            "error": str(error),
        }

    module_file = getattr(module, "__file__", None)

    return {
        "module": module_name,
        "available": True,
        "path": str(Path(module_file).resolve()) if module_file else None,
        "error": None,
    }