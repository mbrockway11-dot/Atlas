"""Self-refine the forward config's engine weights from live paper evidence.

A strategy that retunes on its own recent results is a classic way to look great
then blow up -- it chases noise. So this refiner is deliberately timid. It nudges
the two engines' relative weight toward whichever has the stronger *recent*
research-lab promotion score, but under four guardrails:

- min-sample gate: below N forward days, do nothing (weights stay equal).
- bounds: each engine weight stays in [0.5, 1.5] (equal = 1.0) -- neither engine
  can be dropped or dominate.
- step cap: weights move at most STEP per refine, so one noisy window can't swing
  the book.
- circuit breaker: if the forward equity is in a >15% drawdown, pull weights back
  toward equal -- de-risk, don't double down on a losing tilt.

Writes engine_weights.json (read by run_forward_paper.py) and logs every change.

    .venv/Scripts/python.exe scripts/forward_refine.py
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path

ENGINE_IDS = ("drawdown_recovery_v1", "defensive_risk_off_v1")
PROMOTIONS = Path("output/investment_alpha_research_lab/alpha_research_promotion_decisions.csv")
STATE_DIR = Path("output/investment_forward_paper")
WEIGHTS_JSON = STATE_DIR / "engine_weights.json"
EQUITY_LOG = STATE_DIR / "forward_equity_log.csv"
REFINE_LOG = STATE_DIR / "refine_log.csv"

BOUND_LO, BOUND_HI = 0.5, 1.5
STEP = 0.10


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def promotion_scores() -> dict[str, float]:
    scores = {e: 0.5 for e in ENGINE_IDS}
    if PROMOTIONS.exists():
        for r in csv.DictReader(open(PROMOTIONS, encoding="utf-8")):
            if r["engine_id"] in scores:
                scores[r["engine_id"]] = max(0.01, float(r["promotion_score"]))
    return scores


def forward_stats() -> tuple[int, float]:
    if not EQUITY_LOG.exists():
        return 0, 0.0
    rows = list(csv.DictReader(open(EQUITY_LOG, encoding="utf-8")))
    days = len({r["timestamp"][:10] for r in rows})
    eq = [float(r["equity"]) for r in rows]
    peak, dd = (eq[0] if eq else 0.0), 0.0
    for e in eq:
        peak = max(peak, e)
        dd = min(dd, e / peak - 1.0) if peak else 0.0
    return days, dd


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--min-days", type=int, default=20)
    args = parser.parse_args(argv)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    current = {e: 1.0 for e in ENGINE_IDS}
    if WEIGHTS_JSON.exists():
        loaded = json.loads(WEIGHTS_JSON.read_text("utf-8"))
        current = {e: float(loaded.get(e, 1.0)) for e in ENGINE_IDS}

    days, drawdown = forward_stats()
    reason = ""

    if days < args.min_days:
        target = {e: 1.0 for e in ENGINE_IDS}  # not enough live evidence: stay equal
        reason = f"min_sample_gate ({days}<{args.min_days}d): weights held equal"
    else:
        scores = promotion_scores()
        total = sum(scores.values())
        # Weights proportional to recent promotion score, normalized to sum 2.
        raw = {e: 2.0 * scores[e] / total for e in ENGINE_IDS}
        target = {e: _clamp(raw[e], BOUND_LO, BOUND_HI) for e in ENGINE_IDS}
        # Circuit breaker: in a >15% drawdown, pull halfway back to equal.
        if drawdown <= -0.15:
            target = {e: (target[e] + 1.0) / 2.0 for e in ENGINE_IDS}
            reason = f"circuit_breaker (dd {drawdown*100:.0f}%): de-risked toward equal"
        else:
            reason = "reweighted by recent promotion score (bounded)"

    # Step cap vs current.
    new = {e: _clamp(target[e], current[e] - STEP, current[e] + STEP) for e in ENGINE_IDS}
    new = {e: round(_clamp(v, BOUND_LO, BOUND_HI), 4) for e, v in new.items()}

    WEIGHTS_JSON.write_text(json.dumps(new, indent=2, sort_keys=True) + "\n", "utf-8")
    now = datetime.now(timezone.utc).isoformat()
    row = {"timestamp": now, "forward_days": days, "drawdown": round(drawdown, 4),
           **{f"w_{e}": new[e] for e in ENGINE_IDS}, "reason": reason}
    header = not REFINE_LOG.exists()
    with REFINE_LOG.open("a", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if header:
            w.writeheader()
        w.writerow(row)

    print("Self-refinement (guarded):")
    print(f"  forward days: {days}   drawdown: {drawdown*100:.1f}%")
    print(f"  {reason}")
    print(f"  weights: " + "  ".join(f"{e.split('_v1')[0]}={new[e]:.2f}" for e in ENGINE_IDS))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
