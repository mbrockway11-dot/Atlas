
"""Run Atlas Core v2 investment pipeline."""

from __future__ import annotations

from atlas.core import AtlasContext, AtlasEngine, NodeRegistry
from atlas.core.investment_nodes import build_investment_core_nodes
from atlas.core.report import write_core_report


def build_registry() -> NodeRegistry:
    registry = NodeRegistry()

    for node in build_investment_core_nodes():
        registry.register(node)

    return registry


def main() -> None:
    context = AtlasContext(mode="paper", live_trading_enabled=False)
    engine = AtlasEngine(build_registry(), context=context)
    report = engine.run()
    write_core_report(report)

    print(report["success"])
    print("Run ID:", report["run_id"])
    print("Nodes:", report["node_count"])
    print("State keys:", report["state_keys"])

    for row in report.get("results", []):
        print(row)

    print("JSON: output/atlas_core/atlas_core_report.json")
    print("Markdown: output/atlas_core/atlas_core_report.md")


if __name__ == "__main__":
    main()
