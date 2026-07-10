
"""Alpha Ensemble v4 allocation hints."""

from __future__ import annotations


MAX_RISKY = 0.70


def build_ensemble_allocations(scores: list[dict]) -> list[dict]:
    risky = [s for s in scores if s.get("asset") != "CASH" and s.get("ensemble_score", 0.0) > 0.40]

    if not risky:
        return [{"asset": "CASH", "ensemble_target_weight": 1.0, "source": "alpha_ensemble_v4"}]

    total_score = sum(float(s.get("ensemble_score") or 0.0) for s in risky)

    rows = []

    for s in risky:
        score = float(s.get("ensemble_score") or 0.0)
        target = (score / total_score) * MAX_RISKY if total_score else 0.0

        rows.append({
            "asset": s.get("asset"),
            "ensemble_score": round(score, 6),
            "ensemble_target_weight": round(target, 6),
            "ensemble_action": s.get("ensemble_action"),
            "source_count": s.get("source_count"),
            "source": "alpha_ensemble_v4",
        })

    cash = round(max(0.0, 1.0 - sum(r["ensemble_target_weight"] for r in rows)), 6)

    rows.append({
        "asset": "CASH",
        "ensemble_score": 1.0,
        "ensemble_target_weight": cash,
        "ensemble_action": "RESERVE_CASH",
        "source_count": 0,
        "source": "alpha_ensemble_v4",
    })

    return rows
