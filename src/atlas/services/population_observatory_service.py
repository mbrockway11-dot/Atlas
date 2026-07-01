"""Population Observatory service layer."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.calibration.nearest_neighbor import (
    find_nearest_neighbors,
    neighbor_result_to_dict,
)
from atlas.calibration.population_graph import (
    build_population_graph,
    population_graph_to_dict,
)
from atlas.calibration.similarity_matrix import (
    build_similarity_matrix_from_library,
    similarity_matrix_to_dict,
)


DEFAULT_PROFILE_DIR = Path("output/library/profiles")


def load_population_records(profile_dir: str | Path = DEFAULT_PROFILE_DIR) -> list[dict[str, Any]]:
    """Load profile intake and ACF availability records."""
    root = Path(profile_dir)

    if not root.exists():
        return []

    records: list[dict[str, Any]] = []

    for profile_path in sorted(root.iterdir()):
        if not profile_path.is_dir():
            continue

        intake_path = profile_path / "profile.intake.json"
        acf_path = profile_path / "profile.acf.json"

        intake: dict[str, Any] = {}
        if intake_path.exists():
            try:
                intake = json.loads(intake_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                intake = {}

        records.append(
            {
                "slug": profile_path.name,
                "name": intake.get("name", profile_path.name),
                "birth_date": intake.get("birth_date", ""),
                "birth_time": intake.get("birth_time", "Unknown"),
                "birth_place": intake.get("birth_place", ""),
                "has_intake": intake_path.exists(),
                "has_acf": acf_path.exists(),
                "profile_dir": str(profile_path),
            }
        )

    return records


def build_population_observatory_payload(
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
    *,
    threshold: float = 0.85,
) -> dict[str, Any]:
    """Build population observatory payload."""
    root = Path(profile_dir)

    if not root.exists():
        return {
            "success": False,
            "profile_dir": str(root),
            "records": [],
            "errors": [f"Profile directory not found: {root}"],
            "warnings": [],
            "data": {},
            "metrics": {},
        }

    records = load_population_records(root)

    if not records:
        return {
            "success": False,
            "profile_dir": str(root),
            "records": [],
            "errors": ["No profiles found."],
            "warnings": [],
            "data": {},
            "metrics": {},
        }

    matrix = build_similarity_matrix_from_library(root)
    graph = build_population_graph(matrix, threshold=threshold)

    known_birth_times = sum(
        1
        for record in records
        if str(record.get("birth_time", "")).strip().lower()
        not in {"", "unknown", "none", "null"}
    )

    with_intake = sum(1 for record in records if record.get("has_intake"))
    with_acf = sum(1 for record in records if record.get("has_acf"))

    return {
        "success": True,
        "profile_dir": str(root),
        "threshold": threshold,
        "records": records,
        "errors": [],
        "warnings": [],
        "data": {
            "matrix": matrix,
            "graph": graph,
            "matrix_dict": similarity_matrix_to_dict(matrix),
            "graph_dict": population_graph_to_dict(graph),
        },
        "metrics": {
            "profiles": len(records),
            "with_intake": with_intake,
            "with_acf": with_acf,
            "known_birth_times": known_birth_times,
            "unknown_birth_times": len(records) - known_birth_times,
            "similarity_pairs": matrix.pair_count,
            "mean_similarity": matrix.summary.get("mean_similarity", 0.0),
            "graph_edges": graph.edge_count,
            "graph_density": graph.summary.get("density", 0.0),
        },
    }


def load_profile_detail(
    profile_key: str,
    profile_dir: str | Path = DEFAULT_PROFILE_DIR,
) -> dict[str, Any]:
    """Load selected profile detail without crashing on missing files."""
    profile_path = Path(profile_dir) / profile_key

    files = {
        "intake": profile_path / "profile.intake.json",
        "acf": profile_path / "profile.acf.json",
    }

    payload: dict[str, Any] = {
        "profile_key": profile_key,
        "profile_dir": str(profile_path),
        "exists": profile_path.exists(),
        "missing": [],
        "available": [],
        "intake": None,
        "acf": None,
    }

    for key, path in files.items():
        if path.exists():
            payload[key] = json.loads(path.read_text(encoding="utf-8"))
            payload["available"].append(path.name)
        else:
            payload["missing"].append(path.name)

    return payload


def collect_population_identities(matrix: Any) -> list[str]:
    """Collect identities represented in a similarity matrix."""
    identities: set[str] = set()

    for result in getattr(matrix, "results", []):
        identities.add(result.identity_a)
        identities.add(result.identity_b)

    return sorted(identities)


def build_neighbor_payload(matrix: Any, identity: str, *, limit: int = 10) -> dict[str, Any]:
    """Build nearest-neighbor payload."""
    neighbors = find_nearest_neighbors(matrix, identity, limit=limit)

    return {
        "success": True,
        "identity": identity,
        "limit": limit,
        "neighbors": neighbors.neighbors,
        "report": neighbor_result_to_dict(neighbors),
    }


def json_export(data: Any) -> str:
    """Serialize JSON exports."""
    return json.dumps(data, indent=2, sort_keys=True)


def slugify(value: str) -> str:
    """Build safe filename slug."""
    return value.casefold().replace(" ", "_").replace("/", "_").replace("\\", "_")