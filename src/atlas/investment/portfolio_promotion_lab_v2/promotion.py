"""Portfolio Promotion Lab v2 decision governance."""

from __future__ import annotations

from atlas.investment.portfolio_promotion_lab_v2.config import (
    MAX_CANDIDATE_DRAWDOWN,
    MAX_CANDIDATE_TURNOVER,
    MAX_CANDIDATE_VOLATILITY,
    PROMOTION_MIN_DRAWDOWN_IMPROVEMENT,
    PROMOTION_MIN_NET_RETURN_ADVANTAGE,
    PROMOTION_MIN_REBALANCES,
    PROMOTION_MIN_SHARPE_ADVANTAGE,
    REQUIRE_HISTORICAL_GOVERNANCE_FOR_PRODUCTION,
)


def build_promotion_decision(
    *,
    baseline: dict,
    candidate: dict,
    rolling_win_rate: float,
    historical_governance_available: bool,
) -> dict:
    """Apply deterministic walk-forward promotion criteria."""
    return_advantage = (
        candidate[
            "cumulative_return"
        ]
        - baseline[
            "cumulative_return"
        ]
    )

    sharpe_advantage = (
        candidate["sharpe"]
        - baseline["sharpe"]
    )

    drawdown_improvement = (
        abs(
            baseline[
                "maximum_drawdown"
            ]
        )
        - abs(
            candidate[
                "maximum_drawdown"
            ]
        )
    )

    hard_failures = []

    if (
        candidate["rebalance_count"]
        < PROMOTION_MIN_REBALANCES
    ):
        hard_failures.append(
            "INSUFFICIENT_REBALANCES"
        )

    if (
        abs(
            candidate[
                "maximum_drawdown"
            ]
        )
        > MAX_CANDIDATE_DRAWDOWN
    ):
        hard_failures.append(
            "EXCESSIVE_DRAWDOWN"
        )

    if (
        candidate[
            "annualized_volatility"
        ]
        > MAX_CANDIDATE_VOLATILITY
    ):
        hard_failures.append(
            "EXCESSIVE_VOLATILITY"
        )

    if (
        candidate[
            "average_turnover"
        ]
        > MAX_CANDIDATE_TURNOVER
    ):
        hard_failures.append(
            "EXCESSIVE_TURNOVER"
        )

    conditions = {
        "net_return_advantage": (
            return_advantage
            >= PROMOTION_MIN_NET_RETURN_ADVANTAGE
        ),
        "sharpe_advantage": (
            sharpe_advantage
            >= PROMOTION_MIN_SHARPE_ADVANTAGE
        ),
        "drawdown_improvement": (
            drawdown_improvement
            >= PROMOTION_MIN_DRAWDOWN_IMPROVEMENT
        ),
        "positive_rolling_consistency": (
            rolling_win_rate >= 0.60
        ),
        "no_hard_failures": (
            not hard_failures
        ),
    }

    passed = sum(
        bool(value)
        for value in conditions.values()
    )

    score = (
        passed
        / len(conditions)
    )

    research_winner = all(
        conditions.values()
    )

    production_eligible = (
        research_winner
        and (
            historical_governance_available
            or not (
                REQUIRE_HISTORICAL_GOVERNANCE_FOR_PRODUCTION
            )
        )
    )

    if production_eligible:
        decision = "PROMOTE_CANDIDATE"
        reason = (
            "Candidate passed walk-forward performance, "
            "risk, consistency, and governance-history gates."
        )

    elif research_winner:
        decision = "RESEARCH_PROMOTION_ONLY"
        reason = (
            "Candidate won the reconstructed walk-forward test, "
            "but historical governance snapshots are unavailable."
        )

    elif hard_failures:
        decision = "KEEP_BASELINE"
        reason = (
            "Candidate breached one or more hard "
            "walk-forward portfolio constraints."
        )

    elif passed >= 3:
        decision = "EXTEND_RESEARCH"
        reason = (
            "Candidate showed partial walk-forward improvement "
            "but did not pass all promotion conditions."
        )

    else:
        decision = "KEEP_BASELINE"
        reason = (
            "Candidate did not outperform the baseline "
            "consistently in walk-forward evaluation."
        )

    return {
        "decision": decision,
        "reason": reason,
        "promotion_score": round(
            score,
            8,
        ),
        "return_advantage": round(
            return_advantage,
            8,
        ),
        "sharpe_advantage": round(
            sharpe_advantage,
            8,
        ),
        "drawdown_improvement": round(
            drawdown_improvement,
            8,
        ),
        "rolling_win_rate": round(
            rolling_win_rate,
            8,
        ),
        "conditions": conditions,
        "hard_failures": hard_failures,
        "historical_governance_available": (
            historical_governance_available
        ),
        "research_winner": research_winner,
        "production_eligible": (
            production_eligible
        ),
        "execution_target_changed": False,
    }
