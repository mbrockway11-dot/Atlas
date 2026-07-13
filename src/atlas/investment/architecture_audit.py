"""Atlas Architecture Consolidation audit logic.

The reusable audit lives inside the importable Atlas package. Command-line
entry points should remain thin wrappers so tests and automation do not depend
on the repository's non-package ``scripts`` directory.
"""

from __future__ import annotations

import ast
from pathlib import Path

from atlas.investment.artifact_contracts import (
    validate_contract_registry,
)
from atlas.investment.artifacts import ARTIFACTS, validate_registry
from atlas.investment.research_scheduler import JOBS, topological_order


ROOT = Path(__file__).resolve().parents[3]
ACTIVE_LOADERS = (
    "src/atlas/investment/adaptive_research_prioritizer/loader.py",
    "src/atlas/investment/research_candidate_consolidator/loader.py",
    "src/atlas/investment/research_program_manager/loader.py",
    "src/atlas/investment/research_experiment_designer/loader.py",
    "src/atlas/investment/research_experiment_execution/loader.py",
    "src/atlas/investment/research_evidence_accumulator/loader.py",
    "src/atlas/investment/experiment_registry/loader.py",
    "src/atlas/investment/research_knowledge_graph/loader.py",
)
FORBIDDEN_LOCAL_FUNCTIONS = {"safe_read_csv", "safe_read_json"}
FORBIDDEN_IMPORT = "atlas.investment.experiment_registry.loader"


def audit_loader(path: Path) -> list[str]:
    """Return architecture violations found in one active loader."""
    errors: list[str] = []

    errors.extend(
        "ARTIFACT_CONTRACT:"
        + error
        for error in validate_contract_registry()
    )
    source = path.read_text(encoding="utf-8-sig")
    tree = ast.parse(source, filename=str(path))

    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if node.name in FORBIDDEN_LOCAL_FUNCTIONS:
                errors.append(f"LOCAL_IO_HELPER:{path}:{node.name}")
        if isinstance(node, ast.ImportFrom) and node.module == FORBIDDEN_IMPORT:
            imported = {alias.name for alias in node.names}
            stale = imported & FORBIDDEN_LOCAL_FUNCTIONS
            for name in sorted(stale):
                errors.append(f"STALE_IO_IMPORT:{path}:{name}")

    return errors


def run_audit() -> list[str]:
    """Return all Phase A architecture violations."""
    errors = list(validate_registry())

    job_ids = [job.job_id for job in JOBS]
    if len(job_ids) != len(set(job_ids)):
        errors.append("DUPLICATE_JOB_ID")

    ordered = topological_order()
    if len(ordered) != len(job_ids) or set(ordered) != set(job_ids):
        errors.append("INVALID_JOB_DAG")

    for relative_path in ACTIVE_LOADERS:
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"MISSING_ACTIVE_LOADER:{relative_path}")
            continue
        errors.extend(audit_loader(path))

    return errors


def format_summary() -> tuple[int, int, int]:
    """Return artifact, job, and audited-loader counts."""
    return len(ARTIFACTS), len(JOBS), len(ACTIVE_LOADERS)


__all__ = [
    "ACTIVE_LOADERS",
    "audit_loader",
    "format_summary",
    "run_audit",
]
