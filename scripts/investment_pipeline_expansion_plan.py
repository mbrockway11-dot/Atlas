
"""Investment Pipeline Expansion Plan.

Reads:
- output/investment_universe/investment_asset_universe_report.json

Writes:
- output/investment_universe/investment_pipeline_expansion_plan.json
- output/investment_universe/investment_pipeline_expansion_plan.md
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


UNIVERSE_REPORT = Path("output/investment_universe/investment_asset_universe_report.json")
OUT_DIR = Path("output/investment_universe")
JSON_PATH = OUT_DIR / "investment_pipeline_expansion_plan.json"
MD_PATH = OUT_DIR / "investment_pipeline_expansion_plan.md"


LIKELY_SIGIL_FILES = [
    "fetch_prices.py",
    "src/data/fetch_prices.py",
    "src/strategy/fetch_prices.py",
    "daily_runner_v5.py",
    "weekly_diagnostics_v5.py",
    "build_forward_outcomes.py",
    "pre_signal.py",
    "build_pre_signal_candidates.py",
    "build_pre_signal_candidates_v5.py",
    "backfill_live_signals_v5.py",
    "equity_curve_sim_v5.py",
    "equity_compare_runner_v5.py",
]


def load_universe_report() -> dict[str, Any]:
    if not UNIVERSE_REPORT.exists():
        return {
            "success": False,
            "error": f"Missing universe report: {UNIVERSE_REPORT}",
        }

    return json.loads(UNIVERSE_REPORT.read_text(encoding="utf-8"))


def build_expansion_plan() -> dict[str, Any]:
    universe = load_universe_report()

    if not universe.get("success"):
        plan = {
            "success": False,
            "error": universe.get("error", "Universe report failed."),
        }
        write_outputs(plan)
        return plan

    current_assets = universe.get("current_assets", []) or []
    target_assets = universe.get("target_assets", []) or []
    missing_assets = universe.get("missing_assets", []) or []

    plan = {
        "success": True,
        "current_assets": current_assets,
        "target_assets": target_assets,
        "missing_assets": missing_assets,
        "sigil_root": universe.get("root"),
        "likely_files_to_inspect": LIKELY_SIGIL_FILES,
        "asset_list_literal": build_asset_list_literal(target_assets),
        "steps": build_steps(target_assets, missing_assets),
        "validation_commands": build_validation_commands(universe.get("root")),
        "summary": (
            f"Expansion plan prepared for {len(target_assets)} target asset(s). "
            f"Current: {len(current_assets)}. Missing: {len(missing_assets)}."
        ),
    }

    write_outputs(plan)
    return plan


def build_asset_list_literal(assets: list[str]) -> str:
    return "ASSETS = [\n" + "\n".join(f'    "{asset}",' for asset in assets) + "\n]"


def build_steps(target_assets: list[str], missing_assets: list[str]) -> list[dict[str, Any]]:
    return [
        {
            "step": 1,
            "title": "Update asset universe",
            "description": "Find the asset list in sigil-engine and replace BTC/ETH/SOL with the expanded target universe.",
            "target_assets": target_assets,
            "missing_assets": missing_assets,
        },
        {
            "step": 2,
            "title": "Re-fetch price data",
            "description": "Run the sigil-engine price fetcher so output/price_data.csv contains all target assets.",
            "expected_output": "output/price_data.csv",
        },
        {
            "step": 3,
            "title": "Rebuild leader-laggard summary",
            "description": "Run the leader-laggard pipeline against the expanded universe.",
            "expected_output": "output/leader_laggard_summary.csv",
        },
        {
            "step": 4,
            "title": "Rebuild forward outcomes",
            "description": "Recalculate forward outcomes across the expanded asset set.",
            "expected_output": "output/forward_outcomes.csv",
        },
        {
            "step": 5,
            "title": "Rebuild pre-signal candidates",
            "description": "Rebuild raw and filtered pre-signal candidates for the expanded universe.",
            "expected_outputs": [
                "output/pre_signal_raw.csv",
                "output/pre_signal_candidates.csv",
                "output/pre_signal_candidates_v5.csv",
                "output/pre_signal_candidates_excess.csv",
            ],
        },
        {
            "step": 6,
            "title": "Backfill live signals",
            "description": "Run the backfill process and compare trade count, win rate, and returns versus the old 3-asset sample.",
            "expected_output": "output/backfilled_live_signals_v5.csv",
        },
        {
            "step": 7,
            "title": "Rerun equity simulations",
            "description": "Run equity curve and comparison scripts with asset caps adjusted for the expanded universe.",
            "expected_outputs": [
                "output/equity_curve_v5.csv",
                "output/equity_compare_summary_v5.csv",
                "output/equity_compare_trades_v5.csv",
            ],
        },
        {
            "step": 8,
            "title": "Audit in Atlas",
            "description": "Rerun Investment Validation, Investment Regime Validation, and Asset Universe reports from Atlas.",
        },
    ]


def build_validation_commands(root: str | None) -> list[str]:
    root = root or r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine"

    return [
        f'python scripts\\investment_asset_universe_report.py --root "{root}"',
        f'python scripts\\investment_system_audit.py --root "{root}"',
        f'python scripts\\investment_regime_validation.py --root "{root}"',
        "pytest",
        "python scripts\\audit_dashboard_modernization.py",
    ]


def write_outputs(plan: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(plan, indent=2, ensure_ascii=False), encoding="utf-8")
    MD_PATH.write_text(build_markdown(plan), encoding="utf-8")


def build_markdown(plan: dict[str, Any]) -> str:
    lines = [
        "# Investment Pipeline Expansion Plan",
        "",
        plan.get("summary", ""),
        "",
        "## Target Asset Universe",
        "",
        "```python",
        plan.get("asset_list_literal", ""),
        "```",
        "",
        "## Missing Assets",
        "",
    ]

    missing = plan.get("missing_assets", []) or []
    if missing:
        for asset in missing:
            lines.append(f"- `{asset}`")
    else:
        lines.append("- None.")

    lines.extend(["", "## Likely Sigil-Engine Files to Inspect", ""])

    for file in plan.get("likely_files_to_inspect", []) or []:
        lines.append(f"- `{file}`")

    lines.extend(["", "## Expansion Steps", ""])

    for step in plan.get("steps", []) or []:
        lines.extend([
            f"### {step.get('step')}. {step.get('title')}",
            "",
            step.get("description", ""),
            "",
        ])

        if step.get("expected_output"):
            lines.append(f"- Expected output: `{step.get('expected_output')}`")
            lines.append("")

        if step.get("expected_outputs"):
            lines.append("- Expected outputs:")
            for output in step.get("expected_outputs"):
                lines.append(f"  - `{output}`")
            lines.append("")

    lines.extend(["## Atlas Validation Commands", ""])

    for cmd in plan.get("validation_commands", []) or []:
        lines.append(f"```powershell\n{cmd}\n```")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    plan = build_expansion_plan()
    print(plan["success"])
    print(plan.get("summary", plan.get("error", "")))
    print(f"JSON: {JSON_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
