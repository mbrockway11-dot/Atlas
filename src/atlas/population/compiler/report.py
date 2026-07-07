
"""Population compiler report service."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from atlas.population.compiler.batch import compile_population_batch, load_profile_keys


DEFAULT_NAMES_PATH = Path("research/profile_intake/prominent_figures_1500_names.txt")
DEFAULT_REPORT_PATH = Path("output/population_compiler/report.json")


def build_population_compile_report(
    names_path: str | Path = DEFAULT_NAMES_PATH,
    *,
    limit: int | None = None,
    force: bool = False,
    report_path: str | Path = DEFAULT_REPORT_PATH,
) -> dict[str, Any]:
    profile_keys = load_profile_keys(names_path)

    report = compile_population_batch(
        profile_keys,
        limit=limit,
        force=force,
    )

    target = Path(report_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    report["report_path"] = str(target)
    return report
