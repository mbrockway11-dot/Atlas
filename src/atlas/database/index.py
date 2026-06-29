"""Atlas database index."""

from pathlib import Path
from typing import Any
import json

from atlas.library.profile_library import LIBRARY_DIR, safe_name


DATABASE_INDEX_PATH = LIBRARY_DIR / "index.json"


def load_database_index() -> dict[str, Any]:
    """Load Atlas database index."""
    if not DATABASE_INDEX_PATH.exists():
        return {
            "version": "1.0",
            "entities": [],
        }

    return json.loads(DATABASE_INDEX_PATH.read_text(encoding="utf-8"))


def save_database_index(index: dict[str, Any]) -> Path:
    """Save Atlas database index."""
    DATABASE_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATABASE_INDEX_PATH.write_text(
        json.dumps(index, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return DATABASE_INDEX_PATH


def upsert_entity(
    name: str,
    entity_type: str = "person",
    tags: list[str] | None = None,
    birth_confidence: str = "unknown",
    notes: str | None = None,
) -> dict[str, Any]:
    """Add or update one entity in the Atlas database index."""
    index = load_database_index()
    entity_id = safe_name(name)

    entity = {
        "id": entity_id,
        "name": name,
        "entity_type": entity_type,
        "tags": tags or [],
        "birth_confidence": birth_confidence,
        "notes": notes,
        "acf_path": str(Path(entity_id) / "profile.acf.json"),
        "summary_path": str(Path(entity_id) / "profile_summary.json"),
        "interpretation_path": str(Path(entity_id) / "profile_interpretation.json"),
        "codex_report_path": str(Path(entity_id) / "codex_report.md"),
    }

    existing = [
        item for item in index["entities"]
        if item["id"] != entity_id
    ]

    existing.append(entity)
    index["entities"] = sorted(existing, key=lambda item: item["id"])

    save_database_index(index)

    return entity


def list_entities() -> list[dict[str, Any]]:
    """List indexed entities."""
    return load_database_index()["entities"]


def find_entity(entity_id: str) -> dict[str, Any] | None:
    """Find one entity by ID."""
    for entity in list_entities():
        if entity["id"] == entity_id:
            return entity

    return None