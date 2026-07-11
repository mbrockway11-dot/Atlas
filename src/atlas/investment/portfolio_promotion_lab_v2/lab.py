"""Portfolio Promotion Lab v2 walk-forward orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.portfolio_promotion_lab_v2.candidate import (
    build_governance_map,
)
from atlas.investment.portfolio_promotion_lab_v2.config import (
    MINIMUM_HISTORY_DAYS,
)
from atlas.investment.portfolio_promotion_lab_v2.data import (
    build_price_matrix,
    build_return_matrix,
    normalize_engine_signals,
    normalize_market_history,
)
from atlas.investment.portfolio_promotion_lab_v2.loader import (
    load_walk_forward_inputs,
)
from atlas.investment.portfolio_promotion_lab_v2.promotion import (
    build_promotion_decision,
)
from atlas.investment.portfolio_promotion_lab_v2.simulator import (
    run_walk_forward,
)


OUT_DIR = Path(
    "output/investment_portfolio_promotion_lab_v2"
)

CURVES_CSV = (
    OUT_DIR
    / "walk_forward_equity_curves.csv"
)

REBALANCES_CSV = (
    OUT_DIR
    / "walk_forward_rebalances.csv"
)

METRICS_CSV = (
    OUT_DIR
    / "walk_forward_portfolio_metrics.csv"
)

DECISION_CSV = (
    OUT_DIR
    / "walk_forward_promotion_decision.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "portfolio_promotion_v2_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "portfolio_promotion_v2_report.md"
)


def build_portfolio_promotion_v2_report() -> dict[str, Any]:
    """Run true allocation-reconstruction walk-forward research."""
    inputs = load_walk_forward_inputs()

    market = normalize_market_history(
        inputs["market_history"]
    )

    signals = normalize_engine_signals(
        inputs[
            "historical_engine_signals"
        ]
    )

    prices = build_price_matrix(
        market
    )

    returns = build_return_matrix(
        prices
    )

    governance_map = build_governance_map(
        inputs["engine_governance"]
    )

    simulation = run_walk_forward(
        market=market,
        signals=signals,
        returns=returns,
        governance_map=governance_map,
    )

    baseline = simulation[
        "baseline"
    ]

    candidate = simulation[
        "candidate"
    ]

    rolling_win_rate = calculate_rolling_win_rate(
        baseline["curve"],
        candidate["curve"],
    )

    historical_governance_available = False

    decision = build_promotion_decision(
        baseline=baseline[
            "metrics"
        ],
        candidate=candidate[
            "metrics"
        ],
        rolling_win_rate=(
            rolling_win_rate
        ),
        historical_governance_available=(
            historical_governance_available
        ),
    )

    history_sufficient = (
        len(returns)
        >= MINIMUM_HISTORY_DAYS
    )

    if not history_sufficient:
        decision = {
            **decision,
            "decision": (
                "INSUFFICIENT_DATA"
            ),
            "reason": (
                "Historical market coverage does not "
                f"meet the {MINIMUM_HISTORY_DAYS}-day minimum."
            ),
            "production_eligible": False,
            "execution_target_changed": False,
        }

    curves = pd.concat(
        [
            baseline["curve"],
            candidate["curve"],
        ],
        ignore_index=True,
    )

    rebalances = pd.concat(
        [
            baseline[
                "rebalances"
            ],
            candidate[
                "rebalances"
            ],
        ],
        ignore_index=True,
    )

    metrics = pd.DataFrame([
        {
            "portfolio": (
                "alpha_portfolio_v3_1"
            ),
            **baseline["metrics"],
        },
        {
            "portfolio": (
                "portfolio_optimizer_v2"
            ),
            **candidate["metrics"],
        },
    ])

    report = {
        "success": bool(
            not curves.empty
        ),
        "version": (
            "portfolio_promotion_lab_v2"
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Portfolio Promotion Lab v2 reconstructed "
            f"{len(simulation['rebalance_dates'])} rebalance "
            f"dates and returned {decision['decision']}."
        ),
        "decision": decision,
        "baseline_metrics": (
            baseline["metrics"]
        ),
        "candidate_metrics": (
            candidate["metrics"]
        ),
        "counts": {
            "market_rows": int(
                len(market)
            ),
            "return_dates": int(
                len(returns)
            ),
            "signal_rows": int(
                len(signals)
            ),
            "eligible_engine_count": int(
                len(governance_map)
            ),
            "rebalance_dates": int(
                len(
                    simulation[
                        "rebalance_dates"
                    ]
                )
            ),
            "curve_rows": int(
                len(curves)
            ),
            "rebalance_rows": int(
                len(rebalances)
            ),
        },
        "methodology": {
            "allocation_reconstruction": True,
            "walk_forward": True,
            "future_market_data_used": False,
            "current_weights_applied_backward": False,
            "historical_engine_signals": True,
            "historical_covariance": True,
            "historical_governance_snapshots": False,
            "fixed_current_governance_policy": True,
            "important_limitation": (
                "Historical asset signals and covariance are "
                "reconstructed without future market data, but "
                "engine admission weights use the current approved "
                "governance policy because dated governance snapshots "
                "do not yet exist."
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_execution_target": False,
            "baseline_remains_authoritative": True,
            "candidate_can_self_promote": False,
            "requires_explicit_downstream_approval": True,
            "production_promotion_requires_historical_governance": True,
            "deterministic": True,
        },
        "outputs": {
            "curves_csv": str(
                CURVES_CSV
            ),
            "rebalances_csv": str(
                REBALANCES_CSV
            ),
            "metrics_csv": str(
                METRICS_CSV
            ),
            "decision_csv": str(
                DECISION_CSV
            ),
            "report_json": str(
                REPORT_JSON
            ),
            "report_markdown": str(
                REPORT_MD
            ),
        },
    }

    write_outputs(
        report,
        curves,
        rebalances,
        metrics,
    )

    return report


def calculate_rolling_win_rate(
    baseline_curve: pd.DataFrame,
    candidate_curve: pd.DataFrame,
) -> float:
    if (
        baseline_curve.empty
        or candidate_curve.empty
    ):
        return 0.0

    baseline = baseline_curve[
        [
            "date",
            "daily_return",
        ]
    ].rename(
        columns={
            "daily_return": (
                "baseline_return"
            )
        }
    )

    candidate = candidate_curve[
        [
            "date",
            "daily_return",
        ]
    ].rename(
        columns={
            "daily_return": (
                "candidate_return"
            )
        }
    )

    merged = baseline.merge(
        candidate,
        on="date",
        how="inner",
    ).sort_values(
        "date"
    )

    if len(merged) < 30:
        return 0.0

    baseline_rolling = (
        1.0
        + merged[
            "baseline_return"
        ]
    ).rolling(
        30
    ).apply(
        lambda values: values.prod() - 1.0,
        raw=True,
    )

    candidate_rolling = (
        1.0
        + merged[
            "candidate_return"
        ]
    ).rolling(
        30
    ).apply(
        lambda values: values.prod() - 1.0,
        raw=True,
    )

    valid = (
        baseline_rolling.notna()
        & candidate_rolling.notna()
    )

    if not valid.any():
        return 0.0

    return float(
        (
            candidate_rolling[valid]
            > baseline_rolling[valid]
        ).mean()
    )


def write_outputs(
    report: dict,
    curves: pd.DataFrame,
    rebalances: pd.DataFrame,
    metrics: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    curves.to_csv(
        CURVES_CSV,
        index=False,
    )

    rebalances.to_csv(
        REBALANCES_CSV,
        index=False,
    )

    metrics.to_csv(
        METRICS_CSV,
        index=False,
    )

    pd.DataFrame([
        flatten_decision(
            report["decision"]
        )
    ]).to_csv(
        DECISION_CSV,
        index=False,
    )

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        build_markdown(report),
        encoding="utf-8",
    )


def flatten_decision(
    decision: dict,
) -> dict:
    return {
        **{
            key: value
            for key, value in (
                decision.items()
            )
            if key not in {
                "conditions",
                "hard_failures",
            }
        },
        "conditions_passed": "|".join(
            key
            for key, value in (
                decision.get(
                    "conditions",
                    {}
                ).items()
            )
            if value
        ),
        "hard_failures": "|".join(
            decision.get(
                "hard_failures",
                []
            )
        ),
    }


def build_markdown(
    report: dict,
) -> str:
    decision = report[
        "decision"
    ]

    lines = [
        "# Portfolio Promotion Lab v2",
        "",
        report["summary"],
        "",
        "## Walk-Forward Decision",
        "",
        (
            "- Decision: "
            f"`{decision.get('decision')}`"
        ),
        (
            "- Promotion score: "
            f"`{decision.get('promotion_score')}`"
        ),
        (
            "- Return advantage: "
            f"`{decision.get('return_advantage')}`"
        ),
        (
            "- Sharpe advantage: "
            f"`{decision.get('sharpe_advantage')}`"
        ),
        (
            "- Drawdown improvement: "
            f"`{decision.get('drawdown_improvement')}`"
        ),
        (
            "- Rolling win rate: "
            f"`{decision.get('rolling_win_rate')}`"
        ),
        (
            "- Hard failures: "
            f"`{decision.get('hard_failures')}`"
        ),
        (
            "- Production eligible: "
            f"`{decision.get('production_eligible')}`"
        ),
        "",
        "## Baseline Metrics",
        "",
        "```json",
        json.dumps(
            report[
                "baseline_metrics"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Candidate Metrics",
        "",
        "```json",
        json.dumps(
            report[
                "candidate_metrics"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Methodology",
        "",
        "```json",
        json.dumps(
            report[
                "methodology"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Contract",
        "",
        "```json",
        json.dumps(
            report["contract"],
            indent=2,
        ),
        "```",
        "",
    ]

    return "\n".join(lines)
