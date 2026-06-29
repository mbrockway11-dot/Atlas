from __future__ import annotations

import ast
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(".").resolve()
SRC = ROOT / "src" / "atlas"
DASH = ROOT / "dashboard"
TESTS = ROOT / "tests"
OUT = ROOT / "architecture_audit"
OUT.mkdir(exist_ok=True)

KEYWORDS = {
    "similarity": ["similarity", "cosine", "distance", "neighbor", "nearest"],
    "clustering": ["cluster", "kmeans", "silhouette", "community"],
    "graph_topology": ["graph", "topology", "node", "edge", "centrality", "component"],
    "statistics": ["zscore", "z_score", "variance", "correlation", "baseline", "population_statistics"],
    "confidence": ["confidence", "certainty", "evidence"],
    "reports": ["report", "summary", "interpret"],
    "features": ["feature", "metric", "matrix", "vector"],
    "temporal": ["temporal", "birth", "dasha", "transit", "sidereal", "nakshatra", "varga"],
}

PURPOSE_HINTS = [
    ("dashboard", ["dashboard/"]),
    ("tests", ["tests/"]),
    ("identity/profile construction", ["identity", "acf", "fingerprint", "essence", "birth"]),
    ("temporal calculations", ["temporal", "birth"]),
    ("research matrix/session/validation", ["research"]),
    ("calibration/statistical validation", ["calibration"]),
    ("graph/topology algorithms", ["graph"]),
    ("classification/roles", ["classification"]),
    ("explanation/report language", ["explanation", "intelligence"]),
    ("corpus/library/storage", ["corpus", "library", "database", "datasets"]),
    ("export/rendering", ["export", "visualization"]),
]


def modname(path: Path) -> str:
    rel = path.relative_to(ROOT).with_suffix("")
    parts = rel.parts
    if parts[0] == "src":
        parts = parts[1:]
    return ".".join(parts)


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="ignore")

    try:
        tree = ast.parse(text)
    except SyntaxError as exc:
        return {
            "syntax_error": str(exc),
            "docstring": "",
            "functions": [],
            "classes": [],
            "imports": [],
            "from_imports": [],
            "line_count": len(text.splitlines()),
            "text": text,
        }

    functions = []
    classes = []
    imports = []
    from_imports = []

    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith("_"):
                functions.append(node.name)

        elif isinstance(node, ast.ClassDef):
            if not node.name.startswith("_"):
                classes.append(node.name)

        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)

        elif isinstance(node, ast.ImportFrom):
            if node.module:
                from_imports.append(node.module)

    return {
        "syntax_error": None,
        "docstring": ast.get_docstring(tree) or "",
        "functions": functions,
        "classes": classes,
        "imports": imports,
        "from_imports": from_imports,
        "line_count": len(text.splitlines()),
        "text": text,
    }


def purpose(path: Path) -> str:
    normalized = str(path).replace("\\", "/")

    for label, parts in PURPOSE_HINTS:
        if any(part in normalized for part in parts):
            return label

    return "general support"


def categories(path: Path, meta: dict) -> list[str]:
    haystack = " ".join(
        [
            str(path),
            meta["docstring"],
            " ".join(meta["functions"]),
            " ".join(meta["classes"]),
        ]
    ).lower()

    return [
        category
        for category, keywords in KEYWORDS.items()
        if any(keyword in haystack for keyword in keywords)
    ]


def atlas_imports(meta: dict) -> list[str]:
    modules = []

    for module in meta["imports"] + meta["from_imports"]:
        if module == "atlas" or module.startswith("atlas."):
            modules.append(module)

    return sorted(set(modules))


def build_inventory() -> dict:
    files = sorted(
        list(SRC.rglob("*.py"))
        + list(DASH.rglob("*.py"))
        + list(TESTS.rglob("*.py"))
    )

    items = []
    function_index = defaultdict(list)
    category_index = defaultdict(list)
    import_edges = []

    for path in files:
        meta = parse(path)
        item = {
            "path": str(path.relative_to(ROOT)),
            "module": modname(path),
            "purpose": purpose(path),
            "line_count": meta["line_count"],
            "docstring": meta["docstring"].splitlines()[0] if meta["docstring"] else "",
            "public_functions": meta["functions"],
            "public_classes": meta["classes"],
            "atlas_imports": atlas_imports(meta),
            "categories": categories(path, meta),
            "syntax_error": meta["syntax_error"],
        }

        items.append(item)

        for function_name in meta["functions"]:
            function_index[function_name].append(item["path"])

        for category in item["categories"]:
            category_index[category].append(item["path"])

        for imported_module in item["atlas_imports"]:
            import_edges.append(
                {
                    "source": item["module"],
                    "target": imported_module,
                }
            )

    imported = {edge["target"] for edge in import_edges}

    for item in items:
        item["imported_by_project"] = (
            item["module"] in imported
            or item["path"].startswith("dashboard/")
            or item["path"].startswith("tests/")
            or item["path"].endswith("__init__.py")
        )

    for item in items:
        recommendation = "keep"
        notes = []

        if item["syntax_error"]:
            recommendation = "repair"
            notes.append("syntax error blocks AST inventory")

        if not item["imported_by_project"] and item["path"].startswith("src/atlas/"):
            recommendation = "review"
            notes.append("not directly imported by other Python modules in static scan")

        if len(item["categories"]) >= 3:
            notes.append("multi-responsibility candidate")

        item["recommendation"] = recommendation
        item["notes"] = notes

    return {
        "summary": {
            "src_py": len(list(SRC.rglob("*.py"))),
            "dashboard_py": len(list(DASH.rglob("*.py"))),
            "test_py": len(list(TESTS.rglob("*.py"))),
            "total_py": len(files),
        },
        "modules": items,
        "duplicate_public_function_names": {
            name: paths
            for name, paths in sorted(function_index.items())
            if len(paths) > 1
        },
        "category_index": {
            category: sorted(paths)
            for category, paths in category_index.items()
        },
        "import_edges": import_edges,
    }


def write_json_report(data: dict) -> None:
    (OUT / "module_inventory.json").write_text(
        json.dumps(data, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def write_module_inventory(data: dict) -> None:
    lines = []
    lines.append("# Atlas Module Inventory\n")
    lines.append(
        "Generated static inventory for integration/refactor planning. "
        "This is an architectural aid, not a runtime truth source.\n"
    )

    lines.append("## Summary\n")
    for key, value in data["summary"].items():
        lines.append(f"- **{key}**: {value}")

    lines.append("\n## Modules by package\n")

    packages = defaultdict(list)
    for item in data["modules"]:
        if item["path"].startswith("src/atlas/"):
            package = "/".join(item["path"].split("/")[:3])
        elif item["path"].startswith("dashboard/"):
            package = "dashboard"
        else:
            package = "tests"

        packages[package].append(item)

    for package in sorted(packages):
        lines.append(f"\n### `{package}`\n")
        lines.append("| File | Purpose | Public API | Categories | Recommendation |")
        lines.append("|---|---|---|---|---|")

        for item in sorted(packages[package], key=lambda current: current["path"]):
            api_items = item["public_classes"] + item["public_functions"][:8]
            public_api = ", ".join(api_items)

            if len(item["public_functions"]) > 8:
                public_api += ", ..."

            categories_text = ", ".join(item["categories"])
            recommendation = item["recommendation"]

            if item["notes"]:
                recommendation += ": " + "; ".join(item["notes"])

            lines.append(
                f"| `{item['path']}` | "
                f"{item['purpose']} | "
                f"{public_api or '—'} | "
                f"{categories_text or '—'} | "
                f"{recommendation} |"
            )

    (OUT / "MODULE_INVENTORY.md").write_text("\n".join(lines), encoding="utf-8")


def write_architecture_map(data: dict) -> None:
    lines = [
        "# Atlas Architecture Map\n",
        "This map records observed package responsibilities after the Phase 6A inventory.\n",
    ]

    for package_path in sorted(path for path in SRC.iterdir() if path.is_dir()):
        python_files = list(package_path.rglob("*.py"))
        category_counts = defaultdict(int)
        function_count = 0
        class_count = 0

        for python_file in python_files:
            relative_path = str(python_file.relative_to(ROOT))
            matching = next(
                item for item in data["modules"] if item["path"] == relative_path
            )

            for category in matching["categories"]:
                category_counts[category] += 1

            function_count += len(matching["public_functions"])
            class_count += len(matching["public_classes"])

        top_categories = ", ".join(
            f"{category}({count})"
            for category, count in sorted(
                category_counts.items(),
                key=lambda entry: -entry[1],
            )[:5]
        ) or "general"

        lines.extend(
            [
                f"## `{package_path.name}`",
                f"- Python files: {len(python_files)}",
                f"- Public functions/classes: {function_count}/{class_count}",
                f"- Detected themes: {top_categories}",
                "",
            ]
        )

    (OUT / "ARCHITECTURE_MAP.md").write_text("\n".join(lines), encoding="utf-8")


def write_duplicate_scan(data: dict) -> None:
    lines = [
        "# Atlas Duplicate and Overlap Scan\n",
        "Static scan of duplicate function names and concept overlap categories. "
        "Review before adding new engines.\n",
    ]

    lines.append("## High-risk overlap categories\n")

    for category in [
        "similarity",
        "clustering",
        "graph_topology",
        "statistics",
        "confidence",
        "reports",
        "features",
    ]:
        paths = sorted(data["category_index"].get(category, []))
        lines.append(f"\n### {category}\n")

        for path in paths[:80]:
            lines.append(f"- `{path}`")

        if len(paths) > 80:
            lines.append(f"- ... {len(paths) - 80} more")

    lines.append("\n## Duplicate public function names\n")

    for name, paths in sorted(data["duplicate_public_function_names"].items()):
        if len(paths) >= 2:
            lines.append(f"\n### `{name}`\n")
            for path in paths:
                lines.append(f"- `{path}`")

    (OUT / "DUPLICATE_SCAN.md").write_text("\n".join(lines), encoding="utf-8")


def write_dependency_graph(data: dict) -> None:
    lines = [
        "# Atlas Dependency Graph\n",
        "Static import graph for `atlas.*` imports. "
        "Edges are approximate and do not include dynamic imports.\n",
        "```mermaid",
        "graph TD",
    ]

    package_edges = defaultdict(int)

    for edge in data["import_edges"]:
        source_parts = edge["source"].split(".")[:3]

        if len(source_parts) >= 2 and source_parts[0] == "atlas":
            source = ".".join(source_parts[:2])
        elif edge["source"].startswith("dashboard"):
            source = "dashboard"
        else:
            source = edge["source"].split(".")[0]

        target_parts = edge["target"].split(".")[:2]
        target = ".".join(target_parts) if len(target_parts) >= 2 else edge["target"]

        if source != target:
            package_edges[(source, target)] += 1

    for (source, target), count in sorted(package_edges.items()):
        source_id = source.replace(".", "_")
        target_id = target.replace(".", "_")
        lines.append(f"  {source_id}[{source}] -->|{count}| {target_id}[{target}]")

    lines.append("```\n")
    lines.append("## Raw import edges\n")

    for edge in sorted(data["import_edges"], key=lambda current: (current["source"], current["target"])):
        lines.append(f"- `{edge['source']}` → `{edge['target']}`")

    (OUT / "DEPENDENCY_GRAPH.md").write_text("\n".join(lines), encoding="utf-8")


def write_refactor_plan() -> None:
    lines = [
        "# Atlas Refactor Plan\n",
        "## Prime directive\n",
        "No new analysis module should be added until the existing codebase has been searched for equivalent functionality.\n",
        "## Canonical ownership proposal\n",
        "- `atlas.identity`: profile and identity construction only.",
        "- `atlas.temporal`: birth, chart, transit, dasha, and time-dependent calculations.",
        "- `atlas.research`: matrix/session construction, research exports, and validation reports.",
        "- `atlas.calibration`: canonical home for similarity, nearest-neighbor, z-score, clustering, and population statistics.",
        "- `atlas.graph`: canonical home for graph algorithms and single/population topology primitives.",
        "- `atlas.explanation`: canonical home for user-facing interpretation language.",
        "- `atlas.intelligence`: orchestration only; no duplicate algorithms.",
        "## Immediate actions\n",
        "1. Treat `src/atlas/intelligence/engine.py` as an orchestration layer only.",
        "2. Compare `src/atlas/research/population_topology.py` against `src/atlas/calibration/population_graph.py` and migrate shared graph logic into `atlas.graph` or `atlas.calibration`.",
        "3. Compare `src/atlas/research/statistical.py` against `src/atlas/calibration/population_statistics.py`, `structural_clustering.py`, and `similarity_matrix.py`.",
        "4. Keep dashboard pages thin; dashboard should render, not own calculations.",
        "5. Add deprecation notes before deleting anything.",
        "## Review queues\n",
        "See `DUPLICATE_SCAN.md` for overlap candidates and `MODULE_INVENTORY.md` for per-file recommendations.",
    ]

    (OUT / "REFACTOR_PLAN.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    data = build_inventory()

    write_json_report(data)
    write_module_inventory(data)
    write_architecture_map(data)
    write_duplicate_scan(data)
    write_dependency_graph(data)
    write_refactor_plan()

    print(json.dumps(data["summary"]))


if __name__ == "__main__":
    main()