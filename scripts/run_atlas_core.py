
"""Run Atlas Core v1 investment pipeline wrapper."""

from __future__ import annotations

from atlas.core import AtlasContext, AtlasEngine, NodeRegistry, ScriptNode
from atlas.core.report import write_core_report


def build_registry() -> NodeRegistry:
    registry = NodeRegistry()

    registry.register(ScriptNode(
        name="daily_investment_runbook",
        command=["scripts/daily_investment_runbook.py"],
        provides=["daily_runbook"],
    ))

    registry.register(ScriptNode(
        name="portfolio_state",
        command=["scripts/update_portfolio_state.py"],
        requires=["daily_runbook"],
        provides=["portfolio_state"],
    ))

    registry.register(ScriptNode(
        name="portfolio_lifecycle",
        command=["scripts/update_portfolio_lifecycle.py"],
        requires=["portfolio_state"],
        provides=["portfolio_lifecycle"],
    ))

    registry.register(ScriptNode(
        name="position_manager",
        command=["scripts/update_position_manager.py"],
        requires=["portfolio_lifecycle"],
        provides=["position_manager"],
    ))

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
    print("JSON: output/atlas_core/atlas_core_report.json")
    print("Markdown: output/atlas_core/atlas_core_report.md")


if __name__ == "__main__":
    main()
