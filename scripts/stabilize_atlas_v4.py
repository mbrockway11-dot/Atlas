"""Atlas v4 stabilization checkpoint."""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]

OUTPUT_DIR = ROOT / "output" / "stabilization"
REPORT_JSON = OUTPUT_DIR / "atlas_v4_stabilization_report.json"
REPORT_MD = OUTPUT_DIR / "atlas_v4_stabilization_report.md"


PIPELINE_COMMANDS = [
    [
        sys.executable,
        "scripts/run_alpha_engines.py",
    ],
    [
        sys.executable,
        "scripts/update_macro_intelligence.py",
    ],
    [
        sys.executable,
        "scripts/update_regime_intelligence.py",
    ],
    [
        sys.executable,
        "scripts/update_macro_regime_fusion.py",
    ],
    [
        sys.executable,
        "scripts/run_historical_alpha_engines.py",
    ],
    [
        sys.executable,
        "scripts/validate_historical_alpha_engines.py",
    ],
    [
        sys.executable,
        "scripts/run_alpha_research_lab.py",
    ],
    [
        sys.executable,
        "scripts/update_alpha_ensemble.py",
    ],
    [
        sys.executable,
        "scripts/update_learning_engine.py",
    ],
    [
        sys.executable,
        "scripts/update_ensemble_intelligence_v7.py",
    ],
    [
        sys.executable,
        "scripts/update_governance_snapshots.py",
    ],
    [
        sys.executable,
        "scripts/run_meta_research_engine.py",
    ],
    [
        sys.executable,
        "scripts/run_hypothesis_validation_lab.py",
    ],
    [
        sys.executable,
        "scripts/update_validated_variant_registry.py",
    ],
    [
        sys.executable,
        "scripts/run_variant_review_board.py",
    ],
    [
        sys.executable,
        "scripts/update_variant_decision_ledger.py",
    ],
    [
        sys.executable,
        "scripts/run_variant_implementation_planner.py",
    ],
    [
        sys.executable,
        "scripts/update_portfolio_optimizer_v2.py",
    ],
    [
        sys.executable,
        "scripts/run_portfolio_promotion_lab.py",
    ],
    [
        sys.executable,
        "scripts/run_portfolio_promotion_lab_v2.py",
    ],
    [
        sys.executable,
        "scripts/update_atlas_compiler.py",
    ],
    [
        sys.executable,
        "scripts/validate_atlas_state_api.py",
    ],
    [
        sys.executable,
        "scripts/update_research_scheduler.py",
    ],
    [
        sys.executable,
        "scripts/run_research_cycle.py",
    ],
    [
        sys.executable,
        "scripts/update_experiment_registry.py",
    ],
]


TEST_COMMAND = [
    sys.executable,
    "-m",
    "pytest",
    "tests/test_alpha_engines.py",
    "tests/test_alpha_engine_expansion.py",
    "tests/test_historical_alpha_engines.py",
    "tests/test_alpha_engine_validation.py",
    "tests/test_alpha_research_lab.py",
    "tests/test_alpha_research_portfolio.py",
    "tests/test_macro_intelligence_v1.py",
    "tests/test_regime_intelligence_v1.py",
    "tests/test_macro_regime_fusion_v1.py",
    "tests/test_alpha_ensemble_v6.py",
    "tests/test_alpha_ensemble_v6_1.py",
    "tests/test_ensemble_intelligence_v7.py",
    "tests/test_governance_snapshots_v1.py",
    "tests/test_meta_research_engine_v1.py",
    "tests/test_hypothesis_validation_lab_v1.py",
    "tests/test_validated_variant_registry_v1.py",
    "tests/test_variant_review_board_v1.py",
    "tests/test_variant_decision_ledger_v1.py",
    "tests/test_variant_implementation_planner_v1.py",
    "tests/test_portfolio_optimizer_v2.py",
    "tests/test_portfolio_promotion_lab_v1.py",
    "tests/test_portfolio_promotion_lab_v2.py",
    "tests/test_learning_engine_v3_1.py",
    "tests/test_atlas_compiler_v1.py",
    "tests/test_atlas_state_api_v1.py",
    "tests/test_research_scheduler_v1.py",
    "tests/test_research_orchestrator_v1.py",
    "tests/test_experiment_registry_v1.py",
    "-q",
]

KNOWN_EXTERNAL_BLOCKERS = [
    {
        "id": "missing_research_context",
        "description": (
            "Legacy kernel/plugin tests import ResearchContext from "
            "atlas.core.context, but that compatibility symbol is absent."
        ),
        "affected_tests": [
            "tests/test_core_registry.py",
            "tests/test_kernel_plugins.py",
            "tests/test_kernel_runtime.py",
            "tests/test_plugins_registry.py",
        ],
        "blocks_alpha_research_loop": False,
    }
]


REQUIRED_ARTIFACTS = [
    "output/investment_alpha_engines/alpha_engine_report.json",
    "output/investment_alpha_engines/alpha_engine_latest.csv",
    "output/investment_macro_intelligence/macro_intelligence_report.json",
    "output/investment_macro_intelligence/macro_indicators.csv",
    "output/investment_macro_intelligence/macro_fetch_status.csv",
    "output/investment_regime_intelligence/regime_intelligence_report.json",
    "output/investment_regime_intelligence/current_market_state.csv",
    "output/investment_regime_intelligence/engine_regime_suitability.csv",
    "output/investment_macro_regime_fusion/macro_regime_fusion_report.json",
    "output/investment_macro_regime_fusion/engine_context_modifiers.csv",
    "output/investment_alpha_engines/historical_alpha_engine_report.json",
    "output/investment_alpha_engines/historical_alpha_engine_validation.json",
    "output/investment_alpha_research_lab/alpha_research_lab_report.json",
    "output/investment_alpha_research_lab/alpha_research_promotion_decisions.csv",
    "output/investment_alpha_ensemble/alpha_ensemble_report.json",
    "output/investment_alpha_ensemble/alpha_ensemble_scores.csv",
    "output/investment_alpha_ensemble/alpha_ensemble_allocations.csv",
    "output/investment_learning/learning_report.json",
    "output/investment_learning/strategy_memory.csv",
    "output/investment_learning/strategy_memory_summary.csv",
    "output/investment_learning/engine_learning_recommendations.csv",
    "output/investment_learning/market_memory.csv",
    "output/investment_alpha_ensemble/ensemble_v7_engine_governance.csv",
    "output/investment_alpha_ensemble/ensemble_v7_contribution_ledger.csv",
    "output/investment_alpha_ensemble/ensemble_v7_audit.json",
    "output/investment_alpha_ensemble/ensemble_v7_audit.md",
    "output/investment_governance_snapshots/engine_governance_snapshots.csv",
    "output/investment_governance_snapshots/market_context_snapshots.csv",
    "output/investment_governance_snapshots/governance_snapshot_manifest.csv",
    "output/investment_governance_snapshots/governance_snapshots_report.json",
    "output/investment_governance_snapshots/governance_snapshots_report.md",
    "output/investment_meta_research/engine_diagnostics.csv",
    "output/investment_meta_research/feature_interactions.csv",
    "output/investment_meta_research/engine_failure_modes.csv",
    "output/investment_meta_research/engine_family_gaps.csv",
    "output/investment_meta_research/research_priorities.csv",
    "output/investment_meta_research/hypothesis_library.csv",
    "output/investment_meta_research/meta_research_report.json",
    "output/investment_meta_research/meta_research_report.md",
    "output/investment_hypothesis_validation/hypothesis_validation_results.csv",
    "output/investment_hypothesis_validation/hypothesis_validation_folds.csv",
    "output/investment_hypothesis_validation/hypothesis_validation_trade_ledger.csv",
    "output/investment_hypothesis_validation/validated_hypotheses.csv",
    "output/investment_hypothesis_validation/hypothesis_validation_report.json",
    "output/investment_hypothesis_validation/hypothesis_validation_report.md",
    "output/investment_validated_variants/validated_variant_registry.csv",
    "output/investment_validated_variants/validated_variant_specifications.jsonl",
    "output/investment_validated_variants/validated_variant_manifest.csv",
    "output/investment_validated_variants/validated_variant_conflicts.csv",
    "output/investment_validated_variants/validated_variant_registry_report.json",
    "output/investment_validated_variants/validated_variant_registry_report.md",
    "output/investment_variant_review/variant_review_board.csv",
    "output/investment_variant_review/approved_variants.csv",
    "output/investment_variant_review/held_variants.csv",
    "output/investment_variant_review/rejected_variants.csv",
    "output/investment_variant_review/variants_requiring_more_research.csv",
    "output/investment_variant_review/variant_review_queue.csv",
    "output/investment_variant_review/implementation_backlog.csv",
    "output/investment_variant_review/variant_review_report.json",
    "output/investment_variant_review/variant_review_report.md",
    "output/investment_variant_decisions/variant_decision_ledger.csv",
    "output/investment_variant_decisions/decision_history.csv",
    "output/investment_variant_decisions/approved_variants.csv",
    "output/investment_variant_decisions/rejected_variants.csv",
    "output/investment_variant_decisions/archived_variants.csv",
    "output/investment_variant_decisions/deferred_variants.csv",
    "output/investment_variant_decisions/revisit_later_variants.csv",
    "output/investment_variant_decisions/implementation_queue.csv",
    "output/investment_variant_decisions/variant_decision_report.json",
    "output/investment_variant_decisions/variant_decision_report.md",
    "output/investment_variant_implementation_planner/variant_implementation_plans.csv",
    "output/investment_variant_implementation_planner/variant_target_files.csv",
    "output/investment_variant_implementation_planner/variant_test_plan.csv",
    "output/investment_variant_implementation_planner/variant_acceptance_criteria.csv",
    "output/investment_variant_implementation_planner/variant_rollback_plan.csv",
    "output/investment_variant_implementation_planner/variant_engineering_backlog.csv",
    "output/investment_variant_implementation_planner/variant_implementation_specifications.jsonl",
    "output/investment_variant_implementation_planner/variant_implementation_conflicts.csv",
    "output/investment_variant_implementation_planner/variant_implementation_planner_report.json",
    "output/investment_variant_implementation_planner/variant_implementation_planner_report.md",
    "output/investment_atlas_compiler/atlas_compiled_state.json",
    "output/investment_atlas_compiler/atlas_compiled_state.md",
    "output/investment_atlas_compiler/atlas_component_inventory.csv",
    "output/investment_atlas_compiler/atlas_component_validation.csv",
    "output/investment_atlas_compiler/atlas_state_manifest.csv",
    "output/investment_atlas_compiler/atlas_compiler_report.json",
    "output/investment_atlas_compiler/atlas_compiler_report.md",
    "output/investment_state_api/state_api_validation.json",
    "output/investment_state_api/state_api_validation.md",
    "output/investment_research_scheduler/research_schedule.csv",
    "output/investment_research_scheduler/pending_jobs.csv",
    "output/investment_research_scheduler/blocked_jobs.csv",
    "output/investment_research_scheduler/completed_jobs.csv",
    "output/investment_research_scheduler/failed_jobs.csv",
    "output/investment_research_scheduler/artifact_freshness.csv",
    "output/investment_research_scheduler/dependency_graph.csv",
    "output/investment_research_scheduler/scheduler_run_history.csv",
    "output/investment_research_scheduler/scheduler_state.json",
    "output/investment_research_scheduler/scheduler_report.json",
    "output/investment_research_scheduler/scheduler_report.md",
    "output/investment_research_orchestrator/execution_plan.csv",
    "output/investment_research_orchestrator/executed_jobs.csv",
    "output/investment_research_orchestrator/skipped_jobs.csv",
    "output/investment_research_orchestrator/blocked_jobs.csv",
    "output/investment_research_orchestrator/failed_jobs.csv",
    "output/investment_research_orchestrator/execution_timeline.csv",
    "output/investment_research_orchestrator/execution_graph.csv",
    "output/investment_research_orchestrator/orchestrator_run_history.csv",
    "output/investment_research_orchestrator/execution_state.json",
    "output/investment_research_orchestrator/execution_report.json",
    "output/investment_research_orchestrator/execution_report.md",
    "output/investment_experiment_registry/experiment_registry.csv",
    "output/investment_experiment_registry/experiment_observations.csv",
    "output/investment_experiment_registry/experiment_metrics.csv",
    "output/investment_experiment_registry/experiment_artifacts.csv",
    "output/investment_experiment_registry/experiment_relationships.csv",
    "output/investment_experiment_registry/experiment_status_history.csv",
    "output/investment_experiment_registry/experiment_orchestrator_runs.csv",
    "output/investment_experiment_registry/experiment_registry_state.json",
    "output/investment_experiment_registry/experiment_registry_report.json",
    "output/investment_experiment_registry/experiment_registry_report.md",
    "output/investment_portfolio_optimizer/optimized_portfolio.csv",
    "output/investment_portfolio_optimizer/portfolio_covariance.csv",
    "output/investment_portfolio_optimizer/portfolio_optimizer_report.json",
    "output/investment_portfolio_optimizer/portfolio_optimizer_report.md",
    "output/investment_portfolio_promotion_lab/portfolio_evaluation_metrics.csv",
    "output/investment_portfolio_promotion_lab/portfolio_window_comparison.csv",
    "output/investment_portfolio_promotion_lab/portfolio_promotion_decision.csv",
    "output/investment_portfolio_promotion_lab/portfolio_promotion_report.json",
    "output/investment_portfolio_promotion_lab/portfolio_promotion_report.md",
]


EXPECTED_CONTRACTS = {
    "output/investment_alpha_ensemble/alpha_ensemble_report.json": {
        "version": "alpha_ensemble_v6_1",
    },
    "output/investment_learning/learning_report.json": {
        "version": "learning_engine_v3_1",
    },
}


def run_command(
    command: list[str],
) -> dict[str, Any]:
    """Run one checkpoint command and capture its result."""
    completed = subprocess.run(
        command,
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    return {
        "command": " ".join(command),
        "success": completed.returncode == 0,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def inspect_artifact(
    relative_path: str,
) -> dict[str, Any]:
    """Verify that an expected artifact exists and is nonempty."""
    path = ROOT / relative_path

    exists = path.exists()
    is_file = path.is_file()
    size_bytes = (
        path.stat().st_size
        if exists and is_file
        else 0
    )

    return {
        "path": relative_path,
        "exists": exists,
        "is_file": is_file,
        "size_bytes": size_bytes,
        "valid": bool(
            exists
            and is_file
            and size_bytes > 0
        ),
    }


def inspect_contract(
    relative_path: str,
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Check required values in a JSON output contract."""
    path = ROOT / relative_path

    result = {
        "path": relative_path,
        "valid": False,
        "expected": expected,
        "observed": {},
        "errors": [],
    }

    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        result["errors"].append(
            "Missing or empty JSON artifact."
        )
        return result

    try:
        payload = json.loads(
            path.read_text(
                encoding="utf-8"
            )
        )
    except (
        json.JSONDecodeError,
        UnicodeDecodeError,
    ) as exc:
        result["errors"].append(
            f"Invalid JSON: {exc}"
        )
        return result

    valid = True

    for key, expected_value in expected.items():
        observed_value = payload.get(key)

        result["observed"][key] = (
            observed_value
        )

        if observed_value != expected_value:
            valid = False
            result["errors"].append(
                f"{key}: expected "
                f"{expected_value!r}, observed "
                f"{observed_value!r}"
            )

    result["valid"] = valid

    return result


def markdown_report(
    report: dict[str, Any],
) -> str:
    lines = [
        "# Atlas v4 Stabilization Report",
        "",
        report["summary"],
        "",
        "## State",
        "",
        f"- Success: `{report['success']}`",
        f"- Generated at: `{report['generated_at']}`",
        f"- Pipeline commands: `{len(report['pipeline'])}`",
        f"- Tests passed: `{report['tests']['success']}`",
        (
            "- Valid artifacts: "
            f"`{report['counts']['valid_artifacts']}/"
            f"{report['counts']['artifact_count']}`"
        ),
        (
            "- Valid contracts: "
            f"`{report['counts']['valid_contracts']}/"
            f"{report['counts']['contract_count']}`"
        ),
        "",
        "## Pipeline",
        "",
    ]

    for row in report["pipeline"]:
        status = (
            "PASS"
            if row["success"]
            else "FAIL"
        )

        lines.extend([
            f"### {status}: `{row['command']}`",
            "",
            f"- Return code: `{row['returncode']}`",
            "",
        ])

        if row["stdout"].strip():
            lines.extend([
                "```text",
                row["stdout"].strip(),
                "```",
                "",
            ])

        if row["stderr"].strip():
            lines.extend([
                "```text",
                row["stderr"].strip(),
                "```",
                "",
            ])

    lines.extend([
        "## Tests",
        "",
        f"- Success: `{report['tests']['success']}`",
        f"- Return code: `{report['tests']['returncode']}`",
        "",
        "```text",
        report["tests"]["stdout"].strip(),
        "```",
        "",
        "## Artifacts",
        "",
    ])

    for artifact in report["artifacts"]:
        lines.append(
            "- "
            f"`{artifact['path']}` — "
            f"valid=`{artifact['valid']}`, "
            f"bytes=`{artifact['size_bytes']}`"
        )

    lines.extend([
        "",
        "## Contracts",
        "",
    ])

    for contract in report["contracts"]:
        lines.append(
            "- "
            f"`{contract['path']}` — "
            f"valid=`{contract['valid']}`, "
            f"observed=`{contract['observed']}`"
        )

    lines.extend([
        "",
        "## Known External Blockers",
        "",
    ])

    for blocker in report.get(
        "known_external_blockers",
        [],
    ):
        lines.append(
            "- "
            f"`{blocker.get('id')}` — "
            f"{blocker.get('description')} "
            f"blocks_alpha_research_loop="
            f"`{blocker.get('blocks_alpha_research_loop')}`"
        )

        for test in blocker.get(
            "affected_tests",
            [],
        ):
            lines.append(
                f"  - `{test}`"
            )

    lines.append("")

    return "\n".join(lines)


def main() -> int:
    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pipeline_results = []

    for command in PIPELINE_COMMANDS:
        result = run_command(command)
        pipeline_results.append(result)

        print(
            "PASS"
            if result["success"]
            else "FAIL",
            result["command"],
        )

        if not result["success"]:
            print(result["stdout"])
            print(result["stderr"])
            break

    pipeline_success = all(
        row["success"]
        for row in pipeline_results
    ) and len(
        pipeline_results
    ) == len(
        PIPELINE_COMMANDS
    )

    if pipeline_success:
        test_result = run_command(
            TEST_COMMAND
        )
    else:
        test_result = {
            "command": " ".join(
                TEST_COMMAND
            ),
            "success": False,
            "returncode": -1,
            "stdout": "",
            "stderr": (
                "Tests skipped because the "
                "pipeline failed."
            ),
        }

    artifacts = [
        inspect_artifact(path)
        for path in REQUIRED_ARTIFACTS
    ]

    contracts = [
        inspect_contract(
            path,
            expected,
        )
        for path, expected in (
            EXPECTED_CONTRACTS.items()
        )
    ]

    valid_artifacts = sum(
        row["valid"]
        for row in artifacts
    )

    valid_contracts = sum(
        row["valid"]
        for row in contracts
    )

    success = bool(
        pipeline_success
        and test_result["success"]
        and valid_artifacts
        == len(REQUIRED_ARTIFACTS)
        and valid_contracts
        == len(EXPECTED_CONTRACTS)
    )

    report = {
        "success": success,
        "generated_at": datetime.now(
            UTC
        ).isoformat(),
        "summary": (
            "Atlas v4 stabilization "
            + (
                "passed."
                if success
                else "failed."
            )
        ),
        "pipeline": pipeline_results,
        "tests": test_result,
        "artifacts": artifacts,
        "contracts": contracts,
        "known_external_blockers": KNOWN_EXTERNAL_BLOCKERS,
        "counts": {
            "pipeline_commands": len(
                pipeline_results
            ),
            "artifact_count": len(
                artifacts
            ),
            "valid_artifacts": (
                valid_artifacts
            ),
            "contract_count": len(
                contracts
            ),
            "valid_contracts": (
                valid_contracts
            ),
        },
    }

    REPORT_JSON.write_text(
        json.dumps(
            report,
            indent=2,
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    REPORT_MD.write_text(
        markdown_report(report),
        encoding="utf-8",
    )

    print()
    print(report["summary"])
    print(
        "Report:",
        REPORT_MD.relative_to(ROOT),
    )

    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())


































