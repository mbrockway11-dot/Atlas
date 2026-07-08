
"""Service layer for Investment Regime Validation Lab."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


REGIME_JSON = Path("output/investment_regime/investment_regime_validation.json")


def build_investment_regime_payload(
    *,
    root: str = r"C:\Users\lyfe1\OneDrive\Desktop\sigil-engine",
    rerun: bool = True,
) -> dict[str, Any]:
    """Build Investment Regime Validation payload."""
    if rerun:
        subprocess.run(
            [
                sys.executable,
                "scripts/investment_regime_validation.py",
                "--root",
                root,
            ],
            check=True,
        )

    if not REGIME_JSON.exists():
        return {
            "success": False,
            "error": f"Missing regime validation output: {REGIME_JSON}",
        }

    report = json.loads(REGIME_JSON.read_text(encoding="utf-8"))

    return {
        "success": True,
        "root": root,
        "report": report,
        "summary": report.get("summary", ""),
        "warnings": report.get("warnings", []),
        "return_summary": report.get("return_summary", {}),
    }
