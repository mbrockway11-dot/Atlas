"""Audit Atlas AI subsystem integration."""

from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SEARCH_DIRS = [
    ROOT / "src",
    ROOT / "dashboard",
    ROOT / "scripts",
    ROOT / "docs",
    ROOT / "tests",
]

COMPONENTS = {
    "Hypothesis Engine": [
        "hypothesis",
        "HypothesisEngine",
        "hypothesis_engine",
    ],
    "Falsification Engine": [
        "falsification",
        "FalsificationEngine",
        "falsification_engine",
    ],
    "Experiment Planner": [
        "experiment_planner",
        "ExperimentPlanner",
        "experiment planner",
    ],
    "Query Planner": [
        "query_planner",
        "QueryPlanner",
        "query planner",
    ],
    "Reasoning Engine": [
        "reasoning_engine",
        "ReasoningEngine",
        "reasoning engine",
    ],
    "Discovery Engine": [
        "discovery_engine",
        "DiscoveryEngine",
        "discovery engine",
    ],
    "Research Memory": [
        "research_memory",
        "ResearchMemory",
        "research memory",
    ],
    "Confidence Model": [
        "confidence_model",
        "ConfidenceModel",
        "confidence model",
    ],
    "Scientific Method": [
        "scientific_method",
        "ScientificMethod",
        "scientific method",
    ],
}


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def files_matching(patterns: list[str], root: Path) -> list[Path]:
    matches: list[Path] = []

    if not root.exists():
        return matches

    for path in root.rglob("*"):
        if not path.is_file():
            continue

        if path.suffix.lower() not in {".py", ".md", ".txt"}:
            continue

        text = read_text(path).lower()

        if any(pattern.lower() in text for pattern in patterns):
            matches.append(path)

    return sorted(matches)


def classify_component(name: str, patterns: list[str]) -> dict[str, object]:
    docs = files_matching(patterns, ROOT / "docs")
    src = files_matching(patterns, ROOT / "src")
    services = files_matching(patterns, ROOT / "src" / "atlas" / "services")
    dashboard = files_matching(patterns, ROOT / "dashboard")
    tests = files_matching(patterns, ROOT / "tests")

    runtime_hits = [
        path
        for path in src
        if "services" not in path.parts
        and path.name != "__init__.py"
    ]

    status = "missing"

    if docs and not src:
        status = "documented_only"
    elif src and not services and not dashboard:
        status = "implemented_not_exposed"
    elif src and services and not dashboard:
        status = "service_integrated_not_dashboard_visible"
    elif src and services and dashboard:
        status = "dashboard_visible"
    elif src:
        status = "partial"

    return {
        "component": name,
        "status": status,
        "docs": docs,
        "src": src,
        "services": services,
        "dashboard": dashboard,
        "tests": tests,
        "runtime_hits": runtime_hits,
    }


def relative(paths: list[Path]) -> list[str]:
    return [str(path.relative_to(ROOT)) for path in paths]


def print_component(result: dict[str, object]) -> None:
    print(f"## {result['component']}")
    print(f"- status: {result['status']}")
    print(f"- docs: {len(result['docs'])}")
    print(f"- src: {len(result['src'])}")
    print(f"- services: {len(result['services'])}")
    print(f"- dashboard: {len(result['dashboard'])}")
    print(f"- tests: {len(result['tests'])}")
    print(f"- runtime_hits: {len(result['runtime_hits'])}")

    for label in ["docs", "src", "services", "dashboard", "tests"]:
        paths = relative(result[label])
        if paths:
            print(f"- {label}_files:")
            for path in paths[:20]:
                print(f"  - {path}")

    print()


def main() -> None:
    print("# Atlas AI Integration Audit")
    print()

    results = [
        classify_component(name, patterns)
        for name, patterns in COMPONENTS.items()
    ]

    for result in results:
        print_component(result)

    print("# Summary")
    print()

    for result in results:
        print(f"- {result['component']}: {result['status']}")


if __name__ == "__main__":
    main()