"""
Name normalization utilities for Atlas.

Codex rule:
- uppercase
- strip punctuation
- preserve letter order
- preserve spaces only for readability
- create compact version for computation
"""

import re


def normalize_name(name: str) -> str:
    """
    Normalize a name or phrase for Atlas processing.

    Example:
        "Gaius Julius Caesar!" -> "GAIUS JULIUS CAESAR"
    """
    if not isinstance(name, str):
        raise TypeError("name must be a string")

    name = name.upper()
    name = re.sub(r"[^A-Z ]+", "", name)
    name = re.sub(r"\s+", " ", name).strip()

    return name


def compact_name(name: str) -> str:
    """
    Remove spaces after normalization.

    Example:
        "Gaius Julius Caesar" -> "GAIUSJULIUSCAESAR"
    """
    return normalize_name(name).replace(" ", "")