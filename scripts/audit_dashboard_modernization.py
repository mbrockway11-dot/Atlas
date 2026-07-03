"""Audit dashboard pages for service-layer modernization."""

from __future__ import annotations

from pathlib import Path


DASHBOARD_DIR = Path("dashboard/pages")

DIRECT_ENGINE_PATTERNS = [
    "from atlas.core",
    "from atlas.graph",
    "from atlas.temporal",
    "from atlas.fingerprint",
    "from atlas.population",
    "from atlas.ive",
    "compile_profile",
    "build_temporal_graph",
    "compute_graph_metrics",
    "build_graph_activation",
    "propagate_activation",
    "build_structural_fingerprint",
]

SERVICE_PATTERN = "from atlas.services"


def main() -> None:
    rows = []

    for path in sorted(DASHBOARD_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")

        direct_hits = [
            pattern
            for pattern in DIRECT_ENGINE_PATTERNS
            if pattern in text
        ]

        service_backed = SERVICE_PATTERN in text

        status = "service_backed"
        if direct_hits and service_backed:
            status = "mixed"
        elif direct_hits:
            status = "direct_engine"
        elif not service_backed:
            status = "unclassified"

        rows.append(
            {
                "page": str(path),
                "status": status,
                "service_backed": service_backed,
                "direct_hits": direct_hits,
            }
        )

    print("# Dashboard Modernization Audit")
    print()

    for row in rows:
        print(f"## {row['page']}")
        print(f"- status: {row['status']}")
        print(f"- service_backed: {row['service_backed']}")
        if row["direct_hits"]:
            print(f"- direct_hits: {', '.join(row['direct_hits'])}")
        else:
            print("- direct_hits: none")
        print()

    needs_work = [
        row
        for row in rows
        if row["status"] in {"mixed", "direct_engine", "unclassified"}
    ]

    print("# Summary")
    print(f"- total_pages: {len(rows)}")
    print(f"- needs_work: {len(needs_work)}")
    print("- pages:")
    for row in needs_work:
        print(f"  - {row['page']} [{row['status']}]")


if __name__ == "__main__":
    main()





