
"""Alpha Ensemble v5 report and exports."""

from __future__ import annotations

from datetime import datetime, UTC
import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha_ensemble.allocation import (
    build_ensemble_allocations,
)
from atlas.investment.alpha_ensemble.loader import (
    load_alpha_ensemble_inputs,
)
from atlas.investment.alpha_ensemble.regime import (
    HISTORY_CSV,
    build_ensemble_regime,
    detect_rotations,
)
from atlas.investment.alpha_ensemble.votes import (
    build_asset_votes,
)


OUT_DIR = Path(
    "output/investment_alpha_ensemble"
)
REPORT_JSON = OUT_DIR / "alpha_ensemble_report.json"
REPORT_MD = OUT_DIR / "alpha_ensemble_report.md"
SIGNALS_CSV = OUT_DIR / "alpha_ensemble_signals.csv"
SCORES_CSV = OUT_DIR / "alpha_ensemble_scores.csv"
RANKINGS_CSV = OUT_DIR / "alpha_ensemble_rankings.csv"
ALLOCATIONS_CSV = OUT_DIR / "alpha_ensemble_allocations.csv"
ROTATIONS_CSV = OUT_DIR / "alpha_ensemble_rotations.csv"
REGIME_JSON = OUT_DIR / "alpha_ensemble_regime.json"


def build_alpha_ensemble_report() -> dict[str, Any]:
    inputs = load_alpha_ensemble_inputs()
    scores = build_asset_votes(inputs)
    regime = build_ensemble_regime(scores)
    rotations = detect_rotations(scores)
    allocations = build_ensemble_allocations(
        scores,
        regime,
    )

    generated_at = datetime.now(UTC).isoformat()

    signals = build_compatibility_signals(
        scores
    )

    success = (
        len(scores) > 0
        and any(
            row["asset"] == "CASH"
            for row in allocations
        )
    )

    summary = (
        f"Alpha Ensemble v5.1 evaluated "
        f"{len(scores)} approved asset(s), "
        f"identified regime {regime.get('regime')}, "
        f"and produced {len(allocations)} "
        f"allocation hint(s)."
    )

    report = {
        "success": success,
        "version": "alpha_ensemble_v5_1",
        "generated_at": generated_at,
        "summary": summary,
        "text_summary": summary,
        "regime": regime,
        "signals": signals,
        "scores": scores,
        "rankings": scores,
        "allocations": allocations,
        "rotations": rotations,
        "counts": {
            "approved_assets": len(scores),
            "signals": len(signals),
            "scores": len(scores),
            "allocations": len(allocations),
            "rotations": len(rotations),
            "promote_long": sum(
                row["ensemble_action"]
                == "PROMOTE_LONG"
                for row in scores
            ),
            "maintain": sum(
                row["ensemble_action"]
                == "MAINTAIN"
                for row in scores
            ),
            "watch": sum(
                row["ensemble_action"]
                == "WATCH"
                for row in scores
            ),
        },
        "contract": {
            "research_only": True,
            "execution_instruction": False,
            "approved_universe_only": True,
            "adaptive_weighting_compatible": True,
            "allocation_field": (
                "ensemble_target_weight"
            ),
            "allocation_influences_portfolio": True,
            "regime_cash_preserved": True,
            "no_qualified_asset_policy": (
                "DEFENSIVE_WATCH_FALLBACK"
            ),
            "emergency_cash_requires_no_defensive_candidates": True,
            "rank_basis": (
                "confidence_adjusted_conviction"
            ),
        },
        "outputs": {
            "json": str(REPORT_JSON),
            "markdown": str(REPORT_MD),
            "signals_csv": str(SIGNALS_CSV),
            "scores_csv": str(SCORES_CSV),
            "rankings_csv": str(RANKINGS_CSV),
            "allocations_csv": str(
                ALLOCATIONS_CSV
            ),
            "rotations_csv": str(
                ROTATIONS_CSV
            ),
            "regime_json": str(REGIME_JSON),
            "history_csv": str(HISTORY_CSV),
        },
    }

    write_outputs(report)
    return report


def build_compatibility_signals(
    scores: list[dict],
) -> list[dict]:
    return [
        {
            "asset": row["asset"],
            "signal_source": (
                "alpha_ensemble_v5"
            ),
            "direction": row["direction"],
            "raw_score": row["ensemble_score"],
            "confidence": row["confidence"],
            "status": row["ensemble_action"],
            "source_count": row["source_count"],
        }
        for row in scores
    ]


def write_outputs(
    report: dict[str, Any],
) -> None:
    OUT_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    pd.DataFrame(
        report.get("signals", [])
    ).to_csv(
        SIGNALS_CSV,
        index=False,
    )

    pd.DataFrame(
        report.get("scores", [])
    ).to_csv(
        SCORES_CSV,
        index=False,
    )

    pd.DataFrame(
        report.get("rankings", [])
    ).to_csv(
        RANKINGS_CSV,
        index=False,
    )

    pd.DataFrame(
        report.get("allocations", [])
    ).to_csv(
        ALLOCATIONS_CSV,
        index=False,
    )

    pd.DataFrame(
        report.get("rotations", [])
    ).to_csv(
        ROTATIONS_CSV,
        index=False,
    )

    REGIME_JSON.write_text(
        json.dumps(
            report.get("regime", {}),
            indent=2,
            ensure_ascii=False,
            default=str,
        ),
        encoding="utf-8",
    )

    append_history(report)

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
        build_markdown(report),
        encoding="utf-8",
    )


def append_history(
    report: dict[str, Any],
) -> None:
    generated_at = report.get(
        "generated_at"
    )

    rows = []

    for row in report.get("scores", []):
        rows.append({
            "generated_at": generated_at,
            "asset": row.get("asset"),
            "ensemble_rank": row.get(
                "ensemble_rank"
            ),
            "ensemble_score": row.get(
                "ensemble_score"
            ),
            "confidence": row.get(
                "confidence"
            ),
            "conviction": row.get(
                "conviction"
            ),
            "ensemble_action": row.get(
                "ensemble_action"
            ),
            "regime": report.get(
                "regime",
                {},
            ).get("regime"),
        })

    current = pd.DataFrame(rows)

    if HISTORY_CSV.exists():
        try:
            existing = pd.read_csv(
                HISTORY_CSV
            )
        except Exception:
            existing = pd.DataFrame()
    else:
        existing = pd.DataFrame()

    combined = pd.concat(
        [existing, current],
        ignore_index=True,
    )

    combined.to_csv(
        HISTORY_CSV,
        index=False,
    )


def build_markdown(
    report: dict[str, Any],
) -> str:
    lines = [
        "# Alpha Ensemble v5.1",
        "",
        report.get("summary", ""),
        "",
        "## Regime",
        "",
        "```json",
        json.dumps(
            report.get("regime", {}),
            indent=2,
        ),
        "```",
        "",
        "## Multi-Asset Rankings",
        "",
    ]

    for row in report.get(
        "scores",
        [],
    ):
        lines.append(
            f"- `{row.get('ensemble_rank')}` "
            f"`{row.get('asset')}` "
            f"score=`{row.get('ensemble_score')}` "
            f"confidence=`{row.get('confidence')}` "
            f"conviction=`{row.get('conviction')}` "
            f"action=`{row.get('ensemble_action')}`"
        )

    lines.extend([
        "",
        "## Allocation Hints",
        "",
    ])

    for row in report.get(
        "allocations",
        [],
    ):
        lines.append(
            f"- `{row.get('asset')}` "
            f"target=`{row.get('ensemble_target_weight')}` "
            f"sector=`{row.get('sector')}`"
        )

    lines.extend([
        "",
        "## Rotation",
        "",
    ])

    for row in report.get(
        "rotations",
        [],
    ):
        lines.append(
            f"- `{row.get('asset')}` "
            f"rotation=`{row.get('rotation')}` "
            f"rank_change=`{row.get('rank_change')}`"
        )

    return "\n".join(lines) + "\n"
