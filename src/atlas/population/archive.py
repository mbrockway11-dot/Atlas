"""Population index archive persistence."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.population.index import (
    POPULATION_INDEX_VERSION,
    PopulationIndex,
    PopulationRecord,
)


POPULATION_ARCHIVE_VERSION = "0.1"


def save_population_index(
    *,
    index: PopulationIndex,
    path: str | Path,
) -> None:
    """Save population index to JSON file."""
    output_path = Path(path)
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    payload = {
        "archive_version": POPULATION_ARCHIVE_VERSION,
        "index": index.to_dict(),
    }

    output_path.write_text(
        json.dumps(
            payload,
            indent=2,
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def load_population_index(
    path: str | Path,
) -> PopulationIndex:
    """Load population index from JSON file."""
    input_path = Path(path)

    payload = json.loads(
        input_path.read_text(
            encoding="utf-8",
        )
    )

    index_payload = payload.get("index", payload)

    records = tuple(
        PopulationRecord(
            profile_key=record["profile_key"],
            structural_hash=record["structural_hash"],
            vector={
                key: float(value)
                for key, value in record.get("vector", {}).items()
            },
            labels=dict(record.get("labels", {})),
            metadata=dict(record.get("metadata", {})),
        )
        for record in index_payload.get("records", [])
    )

    return PopulationIndex(
        records=records,
        metadata={
            **dict(index_payload.get("metadata", {})),
            "loaded_from_archive": True,
            "archive_version": payload.get(
                "archive_version",
                POPULATION_ARCHIVE_VERSION,
            ),
            "index_version": index_payload.get(
                "version",
                POPULATION_INDEX_VERSION,
            ),
        },
    )


def population_index_to_json(
    index: PopulationIndex,
) -> str:
    """Serialize population index to JSON string."""
    return json.dumps(
        {
            "archive_version": POPULATION_ARCHIVE_VERSION,
            "index": index.to_dict(),
        },
        indent=2,
        sort_keys=True,
    )


def population_index_from_json(
    text: str,
) -> PopulationIndex:
    """Deserialize population index from JSON string."""
    payload: dict[str, Any] = json.loads(text)
    index_payload = payload.get("index", payload)

    records = tuple(
        PopulationRecord(
            profile_key=record["profile_key"],
            structural_hash=record["structural_hash"],
            vector={
                key: float(value)
                for key, value in record.get("vector", {}).items()
            },
            labels=dict(record.get("labels", {})),
            metadata=dict(record.get("metadata", {})),
        )
        for record in index_payload.get("records", [])
    )

    return PopulationIndex(
        records=records,
        metadata={
            **dict(index_payload.get("metadata", {})),
            "loaded_from_archive": True,
            "archive_version": payload.get(
                "archive_version",
                POPULATION_ARCHIVE_VERSION,
            ),
            "index_version": index_payload.get(
                "version",
                POPULATION_INDEX_VERSION,
            ),
        },
    )
