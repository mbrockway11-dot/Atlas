
"""Service layer for Investment Validation Lab."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


AUDIT_JSON = Path("output/investment_audit/investment_system_audit.json")


def build_investment_validation_payload(
    *,
    root: str = r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine",
    rerun_audit: bool = True,
) -> dict[str, Any]:
    """Build Investment Validation Lab payload."""
    if rerun_audit:
        run_audit(root)

    if not AUDIT_JSON.exists():
        return {
            "success": False,
            "error": f"Missing audit output: {AUDIT_JSON}",
        }

    audit = json.loads(AUDIT_JSON.read_text(encoding="utf-8"))

    return {
        "success": True,
        "root": root,
        "audit": audit,
        "summary": audit.get("summary", ""),
        "warnings": audit.get("warnings", []),
        "files": audit.get("files", {}),
        "signals": audit.get("signals", {}),
        "forward_returns": audit.get("forward_returns", {}),
    }


def run_audit(root: str) -> None:
    """Run investment audit script."""
    subprocess.run(
        [
            sys.executable,
            "scripts/investment_system_audit.py",
            "--root",
            root,
        ],
        check=True,
    )
