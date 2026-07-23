"""Build a deterministic autonomous relationship research program."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from atlas.autonomous.experiment_generator import build_relationship_research_program
from atlas.autonomous.memory import (
    ensure_research_memory,
    persist_research_memory,
    remember_experiment,
    remember_hypothesis,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_COHORTS = (
    PROJECT_ROOT
    / "research"
    / "historical_validation"
    / "relationship_research_candidates.v1.json"
)
DEFAULT_OUTPUT = PROJECT_ROOT / "output" / "autonomous_relationship_research"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cohorts", type=Path, default=DEFAULT_COHORTS)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--top-n", type=int, default=10)
    parser.add_argument(
        "--ignore-memory",
        action="store_true",
        help="Do not use persistent research memory for novelty scoring.",
    )
    parser.add_argument(
        "--persist-plan",
        action="store_true",
        help="Record selected questions and hypotheses in autonomous research memory.",
    )
    args = parser.parse_args()

    source = read_json(args.cohorts)
    cohorts = source.get("cohorts", []) if isinstance(source, dict) else source
    memory = None if args.ignore_memory else ensure_research_memory()
    report = build_relationship_research_program(
        cohorts,
        memory=memory,
        top_n=args.top_n,
    )
    report["source_cohort_registry"] = str(args.cohorts)

    args.output_dir.mkdir(parents=True, exist_ok=True)
    json_path = args.output_dir / "relationship_research_program.json"
    markdown_path = args.output_dir / "relationship_research_program.md"
    json_path.write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    memory_result = None
    if args.persist_plan:
        working_memory = memory or ensure_research_memory()
        working_memory["experiments"] = {
            key: value
            for key, value in (working_memory.get("experiments", {}) or {}).items()
            if not (
                value.get("source") == "autonomous_relationship_research"
                and value.get("status") == "planned"
            )
        }
        working_memory["hypotheses"] = {
            key: value
            for key, value in (working_memory.get("hypotheses", {}) or {}).items()
            if not (
                value.get("source") == "autonomous_relationship_research"
                or (
                    str(value.get("hypothesis_id") or key).startswith("relationship::")
                    and value.get("status") == "preregistered_candidate"
                )
            )
        }
        for row in report["selected_questions"]:
            working_memory = remember_experiment(working_memory, {
                "experiment_id": f"plan::{row['question_id']}",
                "question_id": row["question_id"],
                "question": row["question"],
                "pair_id": row["pair_id"],
                "status": "planned",
                "source": "autonomous_relationship_research",
            })
        for row in report["hypotheses"]:
            working_memory = remember_hypothesis(working_memory, row)
        memory_result = persist_research_memory(working_memory)
    print(json.dumps({
        "success": True,
        "cohorts": report["cohort_count"],
        "questions": report["question_count"],
        "selected": report["selected_count"],
        "hypotheses": report["hypothesis_count"],
        "json": str(json_path),
        "markdown": str(markdown_path),
        "memory": memory_result,
    }, indent=2))


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Autonomous Relationship Research Program",
        "",
        "> Research-only. Symbolic associations are not causal explanations.",
        "",
        report["summary"],
        "",
        "## Ranked cohorts",
        "",
    ]
    for row in report["cohorts"]:
        lines.extend([
            f"### {row['profile_a']} × {row['profile_b']}",
            "",
            f"- Readiness: `{row['readiness_score']:.3f}`",
            f"- Relationship: `{row['relationship_type']}`",
            f"- Outcome-test eligible: `{row['eligible_for_outcome_testing']}`",
            f"- Blockers: `{', '.join(row['blockers']) or 'none'}`",
            "",
        ])
    lines.extend(["## Selected line of inquiry", ""])
    for index, row in enumerate(report["selected_questions"], start=1):
        lines.extend([
            f"{index}. **{row['question']}**",
            f"   - Pair: `{row['pair_id']}`",
            f"   - Stage: `{row['stage']}`",
            f"   - Priority: `{row['priority_score']:.3f}`",
            f"   - Controls: {', '.join(row['controls'])}",
        ])
    lines.extend([
        "",
        "## Hypothesis policy",
        "",
        "Every selected question receives an association hypothesis, a null hypothesis, and a rival-confounder hypothesis. Promotion requires matched controls, correction for multiple testing, independent-pair replication, and held-out evaluation for predictive claims.",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    main()
