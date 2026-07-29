"""Compare two Atlas V3 Canonical Structural Signature artifacts.

This first-stage comparator is intentionally interpretation-free.

It:
- loads two output/css/*.css.json artifacts
- recursively discovers comparable values
- compares every shared numeric field
- reports missing fields and categorical differences
- calculates subsystem similarity
- calculates whole-profile cosine similarity
- writes JSON and Markdown reports

Example:
    python scripts/compare_css_profiles.py nikola_tesla thomas_edison
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable


DEFAULT_CSS_DIR = Path("output") / "css"
DEFAULT_REPORT_DIR = Path("output") / "comparisons"

NON_ANALYTIC_PATH_PARTS = {
    "elapsed_ms",
    "generated_at",
    "compiled_at",
    "timestamp",
    "compiler_version",
    "schema_version",
}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"CSS artifact not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    if not isinstance(payload, dict):
        raise TypeError(f"Expected JSON object in {path}")

    return payload


def extract_css(payload: dict[str, Any]) -> dict[str, Any]:
    """Accept both exported CSS artifacts and direct compiler payloads."""

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

    # Final fallback for a raw CSS object.
    expected_sections = {
        "identity",
        "astronomy",
        "cipher",
        "kamea",
        "structural_measurement",
        "temporal",
    }
    if expected_sections.intersection(payload):
        return payload

    raise KeyError(
        "Could not locate CSS data. Expected 'css', "
        "'data.canonical_structural_signature', or a raw CSS object."
    )


def flatten(
    value: Any,
    prefix: str = "",
) -> dict[str, Any]:
    """Flatten nested dictionaries and lists into stable dotted paths."""

    output: dict[str, Any] = {}

    if isinstance(value, dict):
        for key in sorted(value):
            child_path = f"{prefix}.{key}" if prefix else str(key)
            output.update(flatten(value[key], child_path))
        return output

    if isinstance(value, list):
        for index, item in enumerate(value):
            child_path = f"{prefix}[{index}]"
            output.update(flatten(item, child_path))
        if not value:
            output[prefix] = []
        return output

    output[prefix] = value
    return output


def is_number(value: Any) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
    )


def is_analytic_path(path: str) -> bool:
    lowered = path.lower()
    return not any(part in lowered for part in NON_ANALYTIC_PATH_PARTS)


def subsystem_for_path(path: str) -> str:
    root = path.split(".", 1)[0]
    root = root.split("[", 1)[0]
    return root or "root"


def safe_ratio_difference(left: float, right: float) -> float | None:
    denominator = max(abs(left), abs(right))

    if denominator == 0:
        return 0.0

    return abs(left - right) / denominator


def cosine_similarity(
    left_values: Iterable[float],
    right_values: Iterable[float],
) -> float | None:
    left = list(left_values)
    right = list(right_values)

    if not left or len(left) != len(right):
        return None

    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))

    if left_norm == 0 or right_norm == 0:
        return None

    return dot / (left_norm * right_norm)


def normalized_similarity(left: float, right: float) -> float:
    """Return a bounded 0–1 equality score for two numbers."""

    relative_difference = safe_ratio_difference(left, right)

    if relative_difference is None:
        return 0.0

    return max(0.0, min(1.0, 1.0 - relative_difference))


def compare_numeric_fields(
    left_flat: dict[str, Any],
    right_flat: dict[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    shared_paths = sorted(set(left_flat) & set(right_flat))

    for path in shared_paths:
        left_value = left_flat[path]
        right_value = right_flat[path]

        if not is_number(left_value) or not is_number(right_value):
            continue

        if not is_analytic_path(path):
            continue

        left_number = float(left_value)
        right_number = float(right_value)
        delta = left_number - right_number
        absolute_delta = abs(delta)
        relative_difference = safe_ratio_difference(
            left_number,
            right_number,
        )

        rows.append(
            {
                "path": path,
                "subsystem": subsystem_for_path(path),
                "left": left_number,
                "right": right_number,
                "delta_left_minus_right": delta,
                "absolute_delta": absolute_delta,
                "relative_difference": relative_difference,
                "similarity": normalized_similarity(
                    left_number,
                    right_number,
                ),
            }
        )

    rows.sort(
        key=lambda row: (
            row["relative_difference"]
            if row["relative_difference"] is not None
            else -1.0,
            row["absolute_delta"],
        ),
        reverse=True,
    )

    return rows


def compare_categorical_fields(
    left_flat: dict[str, Any],
    right_flat: dict[str, Any],
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []

    for path in sorted(set(left_flat) & set(right_flat)):
        left_value = left_flat[path]
        right_value = right_flat[path]

        if is_number(left_value) and is_number(right_value):
            continue

        if isinstance(left_value, (dict, list)):
            continue

        if isinstance(right_value, (dict, list)):
            continue

        if left_value != right_value:
            differences.append(
                {
                    "path": path,
                    "subsystem": subsystem_for_path(path),
                    "left": left_value,
                    "right": right_value,
                }
            )

    return differences


def summarize_numeric_rows(
    rows: list[dict[str, Any]],
) -> dict[str, Any]:
    if not rows:
        return {
            "field_count": 0,
            "mean_similarity": None,
            "median_similarity": None,
            "mean_relative_difference": None,
            "cosine_similarity": None,
        }

    similarities = [row["similarity"] for row in rows]
    relative_differences = [
        row["relative_difference"]
        for row in rows
        if row["relative_difference"] is not None
    ]

    left_vector = [row["left"] for row in rows]
    right_vector = [row["right"] for row in rows]

    return {
        "field_count": len(rows),
        "mean_similarity": statistics.fmean(similarities),
        "median_similarity": statistics.median(similarities),
        "mean_relative_difference": (
            statistics.fmean(relative_differences)
            if relative_differences
            else None
        ),
        "cosine_similarity": cosine_similarity(
            left_vector,
            right_vector,
        ),
    }


def build_subsystem_summaries(
    numeric_rows: list[dict[str, Any]],
    categorical_rows: list[dict[str, Any]],
) -> dict[str, Any]:
    numeric_by_subsystem: dict[str, list[dict[str, Any]]] = defaultdict(list)
    categorical_by_subsystem: dict[str, list[dict[str, Any]]] = defaultdict(list)

    for row in numeric_rows:
        numeric_by_subsystem[row["subsystem"]].append(row)

    for row in categorical_rows:
        categorical_by_subsystem[row["subsystem"]].append(row)

    subsystem_names = sorted(
        set(numeric_by_subsystem) | set(categorical_by_subsystem)
    )

    summaries: dict[str, Any] = {}

    for subsystem in subsystem_names:
        summary = summarize_numeric_rows(numeric_by_subsystem[subsystem])
        summary["categorical_difference_count"] = len(
            categorical_by_subsystem[subsystem]
        )
        summaries[subsystem] = summary

    return summaries


def make_markdown(
    result: dict[str, Any],
    top_n: int,
) -> str:
    left_name = result["left_profile"]
    right_name = result["right_profile"]
    overall = result["overall_numeric_summary"]

    lines = [
        f"# Atlas CSS Comparison: {left_name} vs. {right_name}",
        "",
        "## Scope",
        "",
        "This report compares discovered fields from the two compiled Atlas V3 "
        "Canonical Structural Signatures. It does not assign psychological or "
        "historical meaning to the measurements.",
        "",
        "## Coverage",
        "",
        f"- Shared flattened fields: {result['coverage']['shared_field_count']}",
        f"- Shared numeric fields: {overall['field_count']}",
        (
            f"- Fields only in {left_name}: "
            f"{result['coverage']['left_only_field_count']}"
        ),
        (
            f"- Fields only in {right_name}: "
            f"{result['coverage']['right_only_field_count']}"
        ),
        (
            "- Shared categorical differences: "
            f"{len(result['categorical_differences'])}"
        ),
        "",
        "## Whole-profile numeric comparison",
        "",
        "| Measurement | Value |",
        "|---|---:|",
        f"| Mean field similarity | {format_number(overall['mean_similarity'])} |",
        f"| Median field similarity | {format_number(overall['median_similarity'])} |",
        f"| Cosine similarity | {format_number(overall['cosine_similarity'])} |",
        (
            "| Mean relative difference | "
            f"{format_number(overall['mean_relative_difference'])} |"
        ),
        "",
        "## Subsystem summary",
        "",
        "| Subsystem | Numeric fields | Mean similarity | Median similarity | "
        "Cosine similarity | Categorical differences |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    for subsystem, summary in result["subsystem_summaries"].items():
        lines.append(
            f"| {subsystem} "
            f"| {summary['field_count']} "
            f"| {format_number(summary['mean_similarity'])} "
            f"| {format_number(summary['median_similarity'])} "
            f"| {format_number(summary['cosine_similarity'])} "
            f"| {summary['categorical_difference_count']} |"
        )

    lines.extend(
        [
            "",
            f"## Largest {top_n} numeric differences",
            "",
            f"| Rank | Subsystem | Field | {left_name} | {right_name} | "
            "Delta | Relative difference |",
            "|---:|---|---|---:|---:|---:|---:|",
        ]
    )

    for rank, row in enumerate(result["largest_numeric_differences"][:top_n], 1):
        lines.append(
            f"| {rank} "
            f"| {row['subsystem']} "
            f"| `{row['path']}` "
            f"| {format_number(row['left'])} "
            f"| {format_number(row['right'])} "
            f"| {format_number(row['delta_left_minus_right'])} "
            f"| {format_percent(row['relative_difference'])} |"
        )

    lines.extend(
        [
            "",
            "## Categorical differences",
            "",
        ]
    )

    if result["categorical_differences"]:
        lines.extend(
            [
                f"| Field | {left_name} | {right_name} |",
                "|---|---|---|",
            ]
        )

        for row in result["categorical_differences"][:top_n]:
            lines.append(
                f"| `{row['path']}` "
                f"| `{row['left']}` "
                f"| `{row['right']}` |"
            )
    else:
        lines.append("No shared categorical fields differed.")

    lines.extend(
        [
            "",
            "## Fields present in only one artifact",
            "",
            f"### Only in {left_name}",
            "",
        ]
    )

    left_only = result["coverage"]["left_only_paths"]
    if left_only:
        lines.extend(f"- `{path}`" for path in left_only[:top_n])
    else:
        lines.append("None.")

    lines.extend(
        [
            "",
            f"### Only in {right_name}",
            "",
        ]
    )

    right_only = result["coverage"]["right_only_paths"]
    if right_only:
        lines.extend(f"- `{path}`" for path in right_only[:top_n])
    else:
        lines.append("None.")

    lines.append("")
    return "\n".join(lines)


def format_number(value: Any) -> str:
    if value is None:
        return "n/a"

    if isinstance(value, float):
        if abs(value) >= 1000:
            return f"{value:,.4f}"
        return f"{value:.6f}"

    return str(value)


def format_percent(value: float | None) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100:.2f}%"


def compare_profiles(
    left_profile: str,
    right_profile: str,
    css_dir: Path,
    report_dir: Path,
    top_n: int,
) -> tuple[Path, Path, dict[str, Any]]:
    left_path = css_dir / f"{left_profile}.css.json"
    right_path = css_dir / f"{right_profile}.css.json"

    left_payload = load_json(left_path)
    right_payload = load_json(right_path)

    left_css = extract_css(left_payload)
    right_css = extract_css(right_payload)

    left_flat = flatten(left_css)
    right_flat = flatten(right_css)

    numeric_rows = compare_numeric_fields(left_flat, right_flat)
    categorical_rows = compare_categorical_fields(left_flat, right_flat)

    left_paths = set(left_flat)
    right_paths = set(right_flat)
    shared_paths = left_paths & right_paths

    result: dict[str, Any] = {
        "schema_version": "atlas.css-comparison.v1",
        "left_profile": left_profile,
        "right_profile": right_profile,
        "source_files": {
            "left": str(left_path),
            "right": str(right_path),
        },
        "coverage": {
            "left_flattened_field_count": len(left_flat),
            "right_flattened_field_count": len(right_flat),
            "shared_field_count": len(shared_paths),
            "left_only_field_count": len(left_paths - right_paths),
            "right_only_field_count": len(right_paths - left_paths),
            "left_only_paths": sorted(left_paths - right_paths),
            "right_only_paths": sorted(right_paths - left_paths),
        },
        "overall_numeric_summary": summarize_numeric_rows(numeric_rows),
        "subsystem_summaries": build_subsystem_summaries(
            numeric_rows,
            categorical_rows,
        ),
        "largest_numeric_differences": numeric_rows,
        "categorical_differences": categorical_rows,
    }

    report_dir.mkdir(parents=True, exist_ok=True)

    stem = f"{left_profile}__vs__{right_profile}"
    json_path = report_dir / f"{stem}.comparison.json"
    markdown_path = report_dir / f"{stem}.comparison.md"

    with json_path.open("w", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, ensure_ascii=False)

    markdown = make_markdown(result, top_n=top_n)
    markdown_path.write_text(markdown, encoding="utf-8")

    return json_path, markdown_path, result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compare two Atlas V3 CSS artifacts."
    )
    parser.add_argument("left_profile")
    parser.add_argument("right_profile")
    parser.add_argument(
        "--css-dir",
        type=Path,
        default=DEFAULT_CSS_DIR,
    )
    parser.add_argument(
        "--report-dir",
        type=Path,
        default=DEFAULT_REPORT_DIR,
    )
    parser.add_argument(
        "--top",
        type=int,
        default=50,
        help="Maximum rows shown per Markdown section.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        json_path, markdown_path, result = compare_profiles(
            left_profile=args.left_profile,
            right_profile=args.right_profile,
            css_dir=args.css_dir,
            report_dir=args.report_dir,
            top_n=args.top,
        )
    except (FileNotFoundError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}")
        return 1

    overall = result["overall_numeric_summary"]

    print("ATLAS CSS COMPARISON COMPLETE")
    print("=" * 72)
    print(f"Left profile:      {args.left_profile}")
    print(f"Right profile:     {args.right_profile}")
    print(f"Numeric fields:    {overall['field_count']}")
    print(
        "Mean similarity:  "
        f"{format_number(overall['mean_similarity'])}"
    )
    print(
        "Median similarity:"
        f" {format_number(overall['median_similarity'])}"
    )
    print(
        "Cosine similarity:"
        f" {format_number(overall['cosine_similarity'])}"
    )
    print(f"JSON report:       {json_path}")
    print(f"Markdown report:   {markdown_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())