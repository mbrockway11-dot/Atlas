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
        "scripts/update_regime_intelligence.py",
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
]


TEST_COMMAND = [
    sys.executable,
    "-m",
    "pytest",
    "tests/test_alpha_engines.py",
    "tests/test_regime_intelligence_v1.py",
    "tests/test_regime_intelligence_v1.py",
    "tests/test_alpha_engine_expansion.py",
    "tests/test_historical_alpha_engines.py",
    "tests/test_alpha_engine_validation.py",
    "tests/test_alpha_research_lab.py",
    "tests/test_alpha_research_portfolio.py",
    "tests/test_alpha_ensemble_v6.py",
    "tests/test_learning_engine_v3_1.py",
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
    "output/investment_regime_intelligence/regime_intelligence_report.json",
    "output/investment_regime_intelligence/current_market_state.csv",
    "output/investment_regime_intelligence/engine_regime_suitability.csv",
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








