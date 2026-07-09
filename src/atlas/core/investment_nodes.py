
"""Atlas Core v2 investment pipeline nodes."""

from __future__ import annotations

from atlas.core import ScriptNode


def build_investment_core_nodes() -> list[ScriptNode]:
    """Return the full investment pipeline as individual Core nodes."""
    return [
        ScriptNode(
            name="market_features",
            command=["scripts/build_market_features.py", "--root", r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"],
            provides=["market_features"],
        ),
        ScriptNode(
            name="alpha_hypotheses",
            command=["scripts/generate_alpha_hypotheses.py"],
            requires=["market_features"],
            provides=["alpha_hypotheses"],
        ),
        ScriptNode(
            name="alpha_backtests",
            command=["scripts/run_alpha_backtests.py", "--min-trades", "5"],
            requires=["alpha_hypotheses"],
            provides=["alpha_backtests"],
        ),
        ScriptNode(
            name="alpha_validation",
            command=["scripts/validate_alpha_strategies.py", "--top-n", "25"],
            requires=["alpha_backtests"],
            provides=["alpha_validation"],
        ),
        ScriptNode(
            name="alpha_ensemble",
            command=["scripts/build_alpha_ensemble.py"],
            requires=["alpha_validation"],
            provides=["alpha_ensemble"],
        ),
        ScriptNode(
            name="cross_sectional_ranker",
            command=["scripts/build_cross_sectional_alpha_ranker.py"],
            requires=["alpha_ensemble"],
            provides=["cross_sectional_ranker"],
        ),
        ScriptNode(
            name="alpha_portfolio",
            command=["scripts/build_alpha_portfolio.py"],
            requires=["cross_sectional_ranker"],
            provides=["alpha_portfolio"],
        ),
        ScriptNode(
            name="sigil_v32_adapter",
            command=["scripts/build_sigil_v32_adapter.py", "--root", r"C:\Projects\sigil-engine-git"],
            provides=["sigil_v32_adapter"],
        ),
        ScriptNode(
            name="strategy_registry",
            command=["scripts/build_strategy_registry.py"],
            requires=["alpha_portfolio", "sigil_v32_adapter"],
            provides=["strategy_registry"],
        ),
        ScriptNode(
            name="adaptive_weighting",
            command=["scripts/build_adaptive_weighting.py"],
            requires=["alpha_validation", "alpha_backtests"],
            provides=["adaptive_weighting"],
        ),
        ScriptNode(
            name="market_direction",
            command=["scripts/build_market_direction.py"],
            requires=["strategy_registry"],
            provides=["market_direction"],
        ),
        ScriptNode(
            name="decision_engine",
            command=["scripts/build_decision_engine.py"],
            requires=["market_direction", "adaptive_weighting", "strategy_registry"],
            provides=["decision_engine"],
        ),
        ScriptNode(
            name="execution_planner",
            command=["scripts/build_execution_planner.py"],
            requires=["decision_engine", "alpha_portfolio", "strategy_registry"],
            provides=["execution_planner"],
        ),
        ScriptNode(
            name="execution_simulator",
            command=["scripts/simulate_execution_plan.py"],
            requires=["execution_planner"],
            provides=["execution_simulator"],
        ),
        ScriptNode(
            name="paper_trading",
            command=["scripts/run_paper_trading.py"],
            requires=["execution_simulator"],
            provides=["paper_trading"],
        ),
        ScriptNode(
            name="performance",
            command=["scripts/update_portfolio_performance.py"],
            requires=["paper_trading"],
            provides=["performance"],
        ),
        ScriptNode(
            name="learning",
            command=["scripts/update_strategy_learning.py"],
            requires=["performance"],
            provides=["learning"],
        ),
        ScriptNode(
            name="trade_safety",
            command=["scripts/build_trade_safety_report.py"],
            requires=["execution_simulator", "performance", "learning", "decision_engine"],
            provides=["trade_safety"],
        ),
        ScriptNode(
            name="broker_interface",
            command=["scripts/build_broker_interface.py"],
            requires=["trade_safety", "execution_planner"],
            provides=["broker_interface"],
        ),
        ScriptNode(
            name="execution_engine",
            command=["scripts/update_execution_engine.py", "--mode", "paper"],
            requires=["broker_interface", "trade_safety", "risk_engine"],
            provides=["execution_engine"],
        ),
        ScriptNode(
            name="portfolio_state",
            command=["scripts/update_portfolio_state.py"],
            requires=["broker_interface", "performance", "decision_engine"],
            provides=["portfolio_state"],
        ),
        ScriptNode(
            name="portfolio_lifecycle",
            command=["scripts/update_portfolio_lifecycle.py"],
            requires=["portfolio_state", "broker_interface"],
            provides=["portfolio_lifecycle"],
        ),
        ScriptNode(
            name="position_manager",
            command=["scripts/update_position_manager.py"],
            requires=["portfolio_lifecycle", "portfolio_state", "decision_engine", "learning"],
            provides=["position_manager"],
        ),
        ScriptNode(
            name="rebalance_engine",
            command=["scripts/update_rebalance_engine.py"],
            requires=["portfolio_state", "position_manager", "decision_engine", "alpha_portfolio"],
            provides=["rebalance_engine"],
        ),
        ScriptNode(
            name="action_engine",
            command=["scripts/update_action_engine.py"],
            requires=["portfolio_lifecycle", "position_manager", "portfolio_state", "decision_engine", "learning", "performance"],
            provides=["action_engine"],
        ),
        ScriptNode(
            name="risk_engine",
            command=["scripts/update_risk_engine.py"],
            requires=["portfolio_state", "performance", "learning", "action_engine", "rebalance_engine"],
            provides=["risk_engine"],
        ),
    ]
