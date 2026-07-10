
"""Walk-forward exposure sweep."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from atlas.investment.alpha.walkforward.report import build_walkforward_alpha_report


OUT_DIR = Path("output/investment_alpha")
JSON_PATH = OUT_DIR / "walkforward_exposure_sweep.json"
CSV_PATH = OUT_DIR / "walkforward_exposure_sweep.csv"
MD_PATH = OUT_DIR / "walkforward_exposure_sweep.md"


EXPOSURES = [0.05, 0.10, 0.15, 0.20]



def run_sweep() -> dict:
    results = []

    for exposure in EXPOSURES:
        report = build_walkforward_alpha_report(exposure=exposure)

        agg = report.get("aggregate_test", {}) or {}

        final_equity = agg.get("final_equity") or 0
        max_dd = abs(agg.get("max_drawdown") or 0)
        score = final_equity / max_dd if max_dd else None

        results.append({
            "exposure": exposure,
            "splits": report.get("split_count"),
            "stability_score": report.get("stability_score"),
            "trade_count": agg.get("count"),
            "win_rate": agg.get("win_rate"),
            "avg_position_return": agg.get("avg_return"),
            "avg_raw_return_capped": agg.get("avg_raw_return_capped"),
            "profit_factor": agg.get("profit_factor"),
            "max_drawdown": agg.get("max_drawdown"),
            "final_equity": final_equity,
            "return_drawdown_score": round(score, 6) if score is not None else None,
            "sharpe_like": agg.get("sharpe_like"),
        })

    payload = {
        "success": True,
        "exposures": EXPOSURES,
        "results": results,
        "summary": f"Walk-forward exposure sweep evaluated {len(results)} exposure setting(s).",
    }

    write_outputs(payload)
    return payload


def write_outputs(payload: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    JSON_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    df = pd.DataFrame(payload["results"])
    df.to_csv(CSV_PATH, index=False)

    lines = [
        "# Walk-Forward Exposure Sweep",
        "",
        payload["summary"],
        "",
        "## Results",
        "",
    ]

    for row in payload["results"]:
        lines.extend([
            f"### Exposure {row['exposure']:.0%}",
            "",
            f"- Final equity: `{row['final_equity']}`",
            f"- Max drawdown: `{row['max_drawdown']}`",
            f"- Return/DD score: `{row['return_drawdown_score']}`",
            f"- Win rate: `{row['win_rate']}`",
            f"- Avg position return: `{row['avg_position_return']}`",
            f"- Profit factor: `{row['profit_factor']}`",
            f"- Stability: `{row['stability_score']}`",
            "",
        ])

    MD_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    payload = run_sweep()

    print(payload["success"])
    print(payload["summary"])

    for row in payload["results"]:
        print(
            f"exposure={row['exposure']:.0%}",
            "equity=", row["final_equity"],
            "dd=", row["max_drawdown"],
            "score=", row["return_drawdown_score"],
        )

    print(f"JSON: {JSON_PATH}")
    print(f"CSV: {CSV_PATH}")
    print(f"Markdown: {MD_PATH}")


if __name__ == "__main__":
    main()
