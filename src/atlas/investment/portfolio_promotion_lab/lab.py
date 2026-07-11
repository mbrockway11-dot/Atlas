"""Portfolio Promotion Lab v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.portfolio_promotion_lab.evaluator import (
    build_asset_return_matrix,
    evaluate_portfolio_windows,
    normalize_portfolio,
)
from atlas.investment.portfolio_promotion_lab.loader import (
    load_promotion_inputs,
)
from atlas.investment.portfolio_promotion_lab.promotion import (
    compare_portfolios,
)
from atlas.investment.portfolio_promotion_lab.thresholds import (
    EVALUATION_WINDOWS,
    MIN_HISTORY_DAYS,
)


OUT_DIR = Path(
    "output/investment_portfolio_promotion_lab"
)

METRICS_CSV = (
    OUT_DIR
    / "portfolio_evaluation_metrics.csv"
)

COMPARISON_CSV = (
    OUT_DIR
    / "portfolio_window_comparison.csv"
)

DECISION_CSV = (
    OUT_DIR
    / "portfolio_promotion_decision.csv"
)

REPORT_JSON = (
    OUT_DIR
    / "portfolio_promotion_report.json"
)

REPORT_MD = (
    OUT_DIR
    / "portfolio_promotion_report.md"
)


def build_portfolio_promotion_report() -> dict[str, Any]:
    """Evaluate and govern candidate portfolio promotion."""
    inputs = load_promotion_inputs()

    baseline_weights = normalize_portfolio(
        inputs["baseline_portfolio"]
    )

    candidate_weights = normalize_portfolio(
        inputs["candidate_portfolio"]
    )

    returns = build_asset_return_matrix(
        inputs["market_history"]
    )

    sufficient_history = (
        len(returns) >= MIN_HISTORY_DAYS
    )

    baseline_metrics = (
        evaluate_portfolio_windows(
            portfolio_name=(
                "alpha_portfolio_v3_1"
            ),
            weights=baseline_weights,
            returns=returns,
            windows=EVALUATION_WINDOWS,
            reference_weights=None,
        )
    )

    candidate_metrics = (
        evaluate_portfolio_windows(
            portfolio_name=(
                "portfolio_optimizer_v2"
            ),
            weights=candidate_weights,
            returns=returns,
            windows=EVALUATION_WINDOWS,
            reference_weights=baseline_weights,
        )
    )

    comparison, decision = compare_portfolios(
        baseline_metrics,
        candidate_metrics,
    )

    if not sufficient_history:
        decision = {
            **decision,
            "decision": "INSUFFICIENT_DATA",
            "reason": (
                "Market history does not meet the "
                f"{MIN_HISTORY_DAYS}-day minimum."
            ),
            "hard_failures": [
                "INSUFFICIENT_HISTORY"
            ],
        }

    metrics = pd.concat(
        [
            baseline_metrics,
            candidate_metrics,
        ],
        ignore_index=True,
    )

    report = {
        "success": bool(
            not metrics.empty
        ),
        "version": (
            "portfolio_promotion_lab_v1"
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Portfolio Promotion Lab v1 compared "
            "Alpha Portfolio v3.1 against Portfolio "
            f"Optimizer v2 and returned "
            f"{decision.get('decision')}."
        ),
        "decision": decision,
        "counts": {
            "market_observations": int(
                len(returns)
            ),
            "evaluation_windows": int(
                len(EVALUATION_WINDOWS)
            ),
            "metric_rows": int(
                len(metrics)
            ),
            "comparison_rows": int(
                len(comparison)
            ),
        },
        "methodology": {
            "evaluation_type": (
                "current_allocation_trailing_window"
            ),
            "walk_forward": False,
            "lookahead_free_weights": False,
            "important_limitation": (
                "Current portfolio weights are applied "
                "to trailing historical returns. This "
                "measures allocation characteristics, "
                "not full historical signal-generation "
                "or walk-forward performance."
            ),
            "transaction_cost_bps": 10.0,
            "windows": EVALUATION_WINDOWS,
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_execution_target": False,
            "baseline_remains_authoritative": True,
            "candidate_can_self_promote": False,
            "requires_explicit_downstream_approval": True,
            "deterministic": True,
        },
        "outputs": {
            "metrics_csv": str(
                METRICS_CSV
            ),
            "comparison_csv": str(
                COMPARISON_CSV
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
        metrics,
        comparison,
    )

    return report


def write_outputs(
    report: dict,
    metrics: pd.DataFrame,
    comparison: pd.DataFrame,
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    metrics.to_csv(
        METRICS_CSV,
        index=False,
    )

    comparison.to_csv(
        COMPARISON_CSV,
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
        build_markdown(
            report,
            metrics,
            comparison,
        ),
        encoding="utf-8",
    )


def flatten_decision(
    decision: dict,
) -> dict:
    return {
        **{
            key: value
            for key, value in decision.items()
            if key not in {
                "promotion_conditions",
                "hard_failures",
            }
        },
        "promotion_conditions": "|".join(
            key
            for key, passed in (
                decision.get(
                    "promotion_conditions",
                    {}
                )
            ).items()
            if passed
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
    metrics: pd.DataFrame,
    comparison: pd.DataFrame,
) -> str:
    decision = report["decision"]

    lines = [
        "# Portfolio Promotion Lab v1",
        "",
        report["summary"],
        "",
        "## Promotion Decision",
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
            "- Window win rate: "
            f"`{decision.get('window_win_rate')}`"
        ),
        (
            "- Reason: "
            f"{decision.get('reason')}"
        ),
        (
            "- Hard failures: "
            f"`{decision.get('hard_failures')}`"
        ),
        "",
        "## Window Comparison",
        "",
    ]

    for _, row in comparison.iterrows():
        lines.append(
            "- "
            f"`{int(row.get('window_days'))}d` "
            f"return_advantage="
            f"`{row.get('net_return_advantage')}` "
            f"sharpe_advantage="
            f"`{row.get('sharpe_advantage')}` "
            f"drawdown_improvement="
            f"`{row.get('drawdown_improvement')}` "
            f"candidate_wins="
            f"`{row.get('candidate_wins')}`"
        )

    lines.extend([
        "",
        "## Methodology Limitation",
        "",
        report[
            "methodology"
        ][
            "important_limitation"
        ],
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
    ])

    return "\n".join(lines)
