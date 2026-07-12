"""Atlas Compiler source loading."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.atlas_compiler.registry import (
    SOURCE_SPECS,
    SourceSpec,
)


def load_compiler_sources() -> list[dict[str, Any]]:
    """Load every registered compiler component."""
    return [
        load_source(spec)
        for spec in SOURCE_SPECS
    ]


def load_source(
    spec: SourceSpec,
) -> dict[str, Any]:
    """Load one registered artifact."""
    path = spec.path

    base = {
        "component_id": spec.component_id,
        "section": spec.section,
        "path": str(path),
        "source_type": spec.source_type,
        "required": spec.required,
        "exists": path.exists(),
        "valid": False,
        "error": "",
        "sha256": "",
        "row_count": None,
        "payload": None,
    }

    if (
        not path.exists()
        or not path.is_file()
    ):
        base["error"] = "SOURCE_NOT_FOUND"
        return base

    try:
        raw_bytes = path.read_bytes()

        base["sha256"] = hashlib.sha256(
            raw_bytes
        ).hexdigest()

        if spec.source_type == "json":
            payload = json.loads(
                raw_bytes.decode("utf-8")
            )

            base["payload"] = payload
            base["valid"] = isinstance(
                payload,
                dict,
            )

            if not base["valid"]:
                base["error"] = (
                    "JSON_ROOT_NOT_OBJECT"
                )

            return base

        if spec.source_type == "csv":
            frame = pd.read_csv(path)

            base["row_count"] = int(
                len(frame)
            )

            base["payload"] = dataframe_records(
                frame
            )

            base["valid"] = True
            return base

        base["error"] = (
            "UNSUPPORTED_SOURCE_TYPE"
        )

    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        OSError,
        ValueError,
    ) as error:
        base["error"] = (
            f"{type(error).__name__}: {error}"
        )

    return base


def dataframe_records(
    frame: pd.DataFrame,
) -> list[dict]:
    """Convert a DataFrame into JSON-safe records."""
    if frame.empty:
        return []

    normalized = frame.astype(
        object
    ).where(
        pd.notna(frame),
        None,
    )

    return normalized.to_dict(
        orient="records"
    )
