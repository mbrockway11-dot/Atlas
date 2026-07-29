"""Inspect Atlas CSS sections used for structural feature extraction.

This diagnostic does not modify Atlas data. It discovers:

- Kamea analysis structure
- Available graph metrics
- Planet and cipher labels
- Master-graph structure
- Existing feature vectors
- Scalar fields suitable for semantic comparison

Run:
    python scripts/inspect_css_feature_sources.py nikola_tesla thomas_edison
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


DEFAULT_CSS_DIR = Path("output") / "css"
MAX_EXAMPLES = 20


def load_css(profile_key: str, css_dir: Path) -> dict[str, Any]:
    path = css_dir / f"{profile_key}.css.json"

    if not path.exists():
        raise FileNotFoundError(f"CSS artifact not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}")

    css = payload.get("css")

    if isinstance(css, dict):
        return css

    data = payload.get("data")

    if isinstance(data, dict):
        candidate = data.get("canonical_structural_signature")

        if isinstance(candidate, dict):
            return candidate

    candidate = payload.get("canonical_structural_signature")

    if isinstance(candidate, dict):
        return candidate

    return payload


def type_name(value: Any) -> str:
    if value is None:
        return "null"

    if isinstance(value, bool):
        return "bool"

    if isinstance(value, int):
        return "int"

    if isinstance(value, float):
        return "float"

    if isinstance(value, str):
        return "str"

    if isinstance(value, dict):
        return "dict"

    if isinstance(value, list):
        return "list"

    return type(value).__name__


def summarize_value(value: Any) -> str:
    if isinstance(value, dict):
        keys = list(value.keys())
        preview = ", ".join(str(key) for key in keys[:12])

        if len(keys) > 12:
            preview += ", ..."

        return f"dict[{len(value)}] keys=({preview})"

    if isinstance(value, list):
        item_types = Counter(type_name(item) for item in value)
        return f"list[{len(value)}] item_types={dict(item_types)}"

    text = repr(value)

    if len(text) > 160:
        text = text[:157] + "..."

    return text


def print_mapping(
    title: str,
    value: Any,
    *,
    depth: int = 2,
    indent: int = 0,
) -> None:
    prefix = " " * indent
    print(f"{prefix}{title}: {summarize_value(value)}")

    if depth <= 0:
        return

    if isinstance(value, dict):
        for key, child in list(value.items())[:MAX_EXAMPLES]:
            print_mapping(
                str(key),
                child,
                depth=depth - 1,
                indent=indent + 2,
            )

    elif isinstance(value, list):
        for index, child in enumerate(value[:5]):
            print_mapping(
                f"[{index}]",
                child,
                depth=depth - 1,
                indent=indent + 2,
            )


def discover_paths(
    value: Any,
    prefix: str = "",
    *,
    include_containers: bool = False,
) -> list[tuple[str, str, Any]]:
    rows: list[tuple[str, str, Any]] = []

    if isinstance(value, dict):
        if include_containers and prefix:
            rows.append((prefix, "dict", len(value)))

        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            rows.extend(
                discover_paths(
                    child,
                    path,
                    include_containers=include_containers,
                )
            )

        return rows

    if isinstance(value, list):
        if include_containers and prefix:
            rows.append((prefix, "list", len(value)))

        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            rows.extend(
                discover_paths(
                    child,
                    path,
                    include_containers=include_containers,
                )
            )

        return rows

    rows.append((prefix, type_name(value), value))
    return rows


def normalize_indexed_path(path: str) -> str:
    """Replace list positions with [] so repeated schemas group together."""

    output: list[str] = []
    index = 0

    while index < len(path):
        character = path[index]

        if character == "[":
            closing = path.find("]", index)

            if closing != -1:
                output.append("[]")
                index = closing + 1
                continue

        output.append(character)
        index += 1

    return "".join(output)


def schema_frequency(value: Any) -> Counter[str]:
    counter: Counter[str] = Counter()

    for path, field_type, _ in discover_paths(value):
        normalized = normalize_indexed_path(path)
        counter[f"{normalized} :: {field_type}"] += 1

    return counter


def find_named_objects(
    value: Any,
    *,
    candidate_keys: tuple[str, ...],
    prefix: str = "",
) -> list[tuple[str, dict[str, Any]]]:
    matches: list[tuple[str, dict[str, Any]]] = []

    if isinstance(value, dict):
        if any(key in value for key in candidate_keys):
            matches.append((prefix or "<root>", value))

        for key, child in value.items():
            path = f"{prefix}.{key}" if prefix else str(key)
            matches.extend(
                find_named_objects(
                    child,
                    candidate_keys=candidate_keys,
                    prefix=path,
                )
            )

    elif isinstance(value, list):
        for index, child in enumerate(value):
            path = f"{prefix}[{index}]"
            matches.extend(
                find_named_objects(
                    child,
                    candidate_keys=candidate_keys,
                    prefix=path,
                )
            )

    return matches


def print_schema_frequencies(
    title: str,
    value: Any,
    *,
    limit: int = 80,
) -> None:
    print()
    print(title)
    print("-" * len(title))

    frequencies = schema_frequency(value)

    for schema, count in frequencies.most_common(limit):
        print(f"{count:>6}  {schema}")


def print_candidate_analyses(kamea: Any) -> None:
    print()
    print("KAMEA ANALYSIS OBJECTS")
    print("----------------------")

    candidates = find_named_objects(
        kamea,
        candidate_keys=(
            "planet",
            "cipher",
            "features",
            "graph_metrics",
            "node_count",
            "edge_count",
        ),
    )

    print(f"Candidate objects discovered: {len(candidates)}")

    for path, candidate in candidates[:30]:
        useful_identity = {
            key: candidate.get(key)
            for key in (
                "planet",
                "planet_name",
                "cipher",
                "cipher_name",
                "translation",
                "name",
                "label",
                "analysis_id",
            )
            if key in candidate
        }

        print()
        print(f"PATH: {path}")
        print(f"IDENTITY: {useful_identity}")
        print(f"KEYS: {sorted(candidate.keys())}")


def print_scalar_candidates(
    title: str,
    section: Any,
    *,
    allowed_terms: tuple[str, ...],
    excluded_terms: tuple[str, ...],
    limit: int = 120,
) -> None:
    print()
    print(title)
    print("-" * len(title))

    rows: list[tuple[str, str, Any]] = []

    for path, field_type, value in discover_paths(section):
        lowered = path.lower()

        if field_type not in {"int", "float", "bool"}:
            continue

        if not any(term in lowered for term in allowed_terms):
            continue

        if any(term in lowered for term in excluded_terms):
            continue

        rows.append((normalize_indexed_path(path), field_type, value))

    seen: set[str] = set()

    for path, field_type, value in rows:
        key = f"{path}::{field_type}"

        if key in seen:
            continue

        seen.add(key)
        print(f"{field_type:<6} {path:<110} example={value!r}")

        if len(seen) >= limit:
            break

    print(f"Unique candidate schemas shown: {len(seen)}")


def inspect_profile(profile_key: str, css_dir: Path) -> None:
    css = load_css(profile_key, css_dir)

    kamea = css.get("kamea", {})
    structural = css.get("structural_measurement", {})

    print()
    print("=" * 100)
    print(f"PROFILE: {profile_key}")
    print("=" * 100)

    print_mapping("kamea", kamea, depth=3)
    print()
    print_mapping("structural_measurement", structural, depth=4)

    print_candidate_analyses(kamea)

    print_schema_frequencies(
        "MOST COMMON KAMEA FIELD SCHEMAS",
        kamea,
        limit=100,
    )

    print_schema_frequencies(
        "MOST COMMON STRUCTURAL-MEASUREMENT FIELD SCHEMAS",
        structural,
        limit=100,
    )

    graph_terms = (
        "node_count",
        "edge_count",
        "density",
        "degree",
        "component",
        "cycle",
        "clustering",
        "transitivity",
        "assortativity",
        "centrality",
        "betweenness",
        "pagerank",
        "eigenvector",
        "entropy",
        "diameter",
        "radius",
        "modularity",
        "bridge",
        "articulation",
        "hub",
        "leaf",
        "terminal",
        "symmetry",
        "repeat",
        "weight",
        "coverage",
        "loop",
        "branch",
        "path_length",
        "spectral",
        "connectivity",
    )

    implementation_terms = (
        "sequence_index",
        ".edge[",
        ".node[",
        "coordinate",
        "source[",
        "target[",
        "longitude",
        "latitude",
        "declination",
        "timestamp",
        "elapsed",
    )

    print_scalar_candidates(
        "KAMEA SEMANTIC SCALAR CANDIDATES",
        kamea,
        allowed_terms=graph_terms,
        excluded_terms=implementation_terms,
    )

    print_scalar_candidates(
        "STRUCTURAL SEMANTIC SCALAR CANDIDATES",
        structural,
        allowed_terms=graph_terms,
        excluded_terms=implementation_terms,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Inspect Atlas CSS sources for semantic feature extraction."
    )

    parser.add_argument(
        "profiles",
        nargs="+",
        help="Profile keys such as nikola_tesla and thomas_edison.",
    )

    parser.add_argument(
        "--css-dir",
        type=Path,
        default=DEFAULT_CSS_DIR,
    )

    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output")
        / "comparisons"
        / "css_feature_source_inspection.txt",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    args.output.parent.mkdir(parents=True, exist_ok=True)

    import contextlib
    import sys

    try:
        with args.output.open("w", encoding="utf-8") as output_handle:
            with contextlib.redirect_stdout(output_handle):
                for profile_key in args.profiles:
                    inspect_profile(profile_key, args.css_dir)

    except (FileNotFoundError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print("ATLAS CSS FEATURE-SOURCE INSPECTION COMPLETE")
    print(f"Profiles: {', '.join(args.profiles)}")
    print(f"Report:   {args.output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())