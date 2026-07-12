"""Research Hypothesis Validation Lab v1 orchestration."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any

import pandas as pd

from atlas.investment.hypothesis_validation.config import (
    FOLD_RESULTS_CSV,
    OUTPUT_DIR,
    REPORT_JSON,
    REPORT_MD,
    RESULTS_CSV,
    SCHEMA_VERSION,
    SUPPORTED_HYPOTHESIS_TYPES,
    TRADE_LEDGER_CSV,
    VALIDATED_CSV,
    VERSION,
)
from atlas.investment.hypothesis_validation.decision import (
    build_validation_decision,
)
from atlas.investment.hypothesis_validation.loader import (
    load_validation_inputs,
)
from atlas.investment.hypothesis_validation.walk_forward import (
    validate_hypothesis,
)
from atlas.investment.meta_research.evidence import (
    build_research_evidence,
)


def build_hypothesis_validation_report() -> dict[str, Any]:
    """Validate eligible Meta Research hypotheses."""
    inputs = load_validation_inputs()

    evidence = build_research_evidence(
        inputs["trades"],
        inputs["market_history"],
    )

    hypotheses = normalize_hypotheses(
        inputs["hypotheses"]
    )

    result_rows = []
    fold_frames = []
    ledger_frames = []

    for hypothesis in hypotheses.to_dict(
        orient="records"
    ):
        validation = validate_hypothesis(
            hypothesis,
            evidence,
        )

        decision = build_validation_decision(
            hypothesis,
            validation["folds"],
        )

        result_rows.append(
            decision
        )

        if not validation[
            "folds"
        ].empty:
            fold_frames.append(
                validation["folds"]
            )

        if not validation[
            "ledger"
        ].empty:
            ledger_frames.append(
                validation["ledger"]
            )

    results = pd.DataFrame(
        result_rows
    )

    folds = (
        pd.concat(
            fold_frames,
            ignore_index=True,
        )
        if fold_frames
        else pd.DataFrame()
    )

    ledger = (
        pd.concat(
            ledger_frames,
            ignore_index=True,
        )
        if ledger_frames
        else pd.DataFrame()
    )

    validated = (
        results[
            results["decision"]
            .eq("VALIDATE")
        ].copy()
        if not results.empty
        else pd.DataFrame()
    )

    decision_counts = (
        results[
            "decision"
        ].value_counts().to_dict()
        if not results.empty
        else {}
    )

    report = {
        "success": bool(
            not hypotheses.empty
            and not results.empty
        ),
        "version": VERSION,
        "schema_version": (
            SCHEMA_VERSION
        ),
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Research Hypothesis Validation Lab v1 "
            f"evaluated {len(hypotheses)} supported "
            f"hypothesis/hypotheses across "
            f"{len(folds)} walk-forward fold result(s), "
            f"validating {len(validated)}."
        ),
        "counts": {
            "input_hypotheses": int(
                len(
                    inputs["hypotheses"]
                )
            ),
            "supported_hypotheses": int(
                len(hypotheses)
            ),
            "evidence_rows": int(
                len(evidence)
            ),
            "result_rows": int(
                len(results)
            ),
            "fold_rows": int(
                len(folds)
            ),
            "trade_ledger_rows": int(
                len(ledger)
            ),
            "validated_hypotheses": int(
                len(validated)
            ),
        },
        "decision_counts": (
            decision_counts
        ),
        "top_results": (
            results.sort_values(
                [
                    "validation_score",
                    "fold_win_rate",
                    "mean_return_advantage",
                ],
                ascending=[
                    False,
                    False,
                    False,
                ],
                kind="stable",
            ).head(15).to_dict(
                orient="records"
            )
            if not results.empty
            else []
        ),
        "methodology": {
            "supported_types": sorted(
                SUPPORTED_HYPOTHESIS_TYPES
            ),
            "walk_forward": True,
            "expanding_training_window": True,
            "non_overlapping_trades": True,
            "numeric_state_thresholds_fit_on_training_only": True,
            "future_features_used": False,
            "transaction_costs_applied": True,
            "multiple_testing_correction": False,
            "statistical_significance_claimed": False,
            "important_limitation": (
                "Validation establishes deterministic "
                "out-of-sample robustness under the "
                "specified gates, but does not establish "
                "causality. Multiple-hypothesis correction "
                "and portfolio contribution testing remain "
                "separate requirements."
            ),
        },
        "contract": {
            "read_only": True,
            "execution_instruction": False,
            "changes_engine_code": False,
            "changes_engine_registry": False,
            "changes_governance": False,
            "changes_ensemble_weights": False,
            "validated_hypothesis_can_self_promote": False,
            "requires_separate_engine_implementation": True,
            "deterministic_given_inputs": True,
        },
        "outputs": {
            "results_csv": str(
                RESULTS_CSV
            ),
            "fold_results_csv": str(
                FOLD_RESULTS_CSV
            ),
            "trade_ledger_csv": str(
                TRADE_LEDGER_CSV
            ),
            "validated_csv": str(
                VALIDATED_CSV
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
        report=report,
        results=results,
        folds=folds,
        ledger=ledger,
        validated=validated,
    )

    return report


def normalize_hypotheses(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame is None or frame.empty:
        return pd.DataFrame()

    required = {
        "hypothesis_id",
        "hypothesis_type",
        "engine_id",
        "feature",
        "state",
    }

    if not required.issubset(
        frame.columns
    ):
        return pd.DataFrame()

    result = frame.copy()

    result[
        "hypothesis_type"
    ] = (
        result[
            "hypothesis_type"
        ]
        .astype(str)
        .str.upper()
    )

    result = result[
        result[
            "hypothesis_type"
        ].isin(
            SUPPORTED_HYPOTHESIS_TYPES
        )
    ]

    result = result[
        result["engine_id"]
        .fillna("")
        .astype(str)
        .str.len()
        .gt(0)
    ]

    return result.sort_values(
        [
            "priority",
            "confidence",
            "hypothesis_id",
        ],
        ascending=[
            False,
            False,
            True,
        ],
        kind="stable",
    ).reset_index(drop=True)


def write_outputs(
    *,
    report: dict,
    results: pd.DataFrame,
    folds: pd.DataFrame,
    ledger: pd.DataFrame,
    validated: pd.DataFrame,
) -> None:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    results.to_csv(
        RESULTS_CSV,
        index=False,
    )

    folds.to_csv(
        FOLD_RESULTS_CSV,
        index=False,
    )

    ledger.to_csv(
        TRADE_LEDGER_CSV,
        index=False,
    )

    validated.to_csv(
        VALIDATED_CSV,
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
            report
        ),
        encoding="utf-8",
    )


def build_markdown(
    report: dict,
) -> str:
    lines = [
        "# Research Hypothesis Validation Lab v1",
        "",
        report["summary"],
        "",
        "## Decision Counts",
        "",
        "```json",
        json.dumps(
            report[
                "decision_counts"
            ],
            indent=2,
        ),
        "```",
        "",
        "## Leading Results",
        "",
    ]

    for row in report.get(
        "top_results",
        [],
    ):
        lines.extend([
            (
                f"### {row.get('hypothesis_id')}"
            ),
            "",
            (
                f"- Decision: "
                f"`{row.get('decision')}`"
            ),
            (
                f"- Engine: "
                f"`{row.get('engine_id')}`"
            ),
            (
                f"- Gate: "
                f"`{row.get('feature')}="
                f"{row.get('state')}`"
            ),
            (
                f"- Validation score: "
                f"`{row.get('validation_score')}`"
            ),
            (
                f"- Fold win rate: "
                f"`{row.get('fold_win_rate')}`"
            ),
            (
                f"- Mean-return advantage: "
                f"`{row.get('mean_return_advantage')}`"
            ),
            (
                f"- Profit-factor advantage: "
                f"`{row.get('profit_factor_advantage')}`"
            ),
            (
                f"- Sharpe advantage: "
                f"`{row.get('sharpe_advantage')}`"
            ),
            (
                f"- Drawdown improvement: "
                f"`{row.get('drawdown_improvement')}`"
            ),
            (
                f"- Reason: "
                f"{row.get('reason')}"
            ),
            "",
        ])

    lines.extend([
        "## Methodology",
        "",
        "```json",
        json.dumps(
            report["methodology"],
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
    ])

    return "\n".join(lines)
