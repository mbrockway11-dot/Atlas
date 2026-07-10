
"""Walk-forward Alpha report."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd

from atlas.investment.alpha.walkforward.evaluator import evaluate_split
from atlas.investment.alpha.walkforward.metrics import non_overlapping_trades, stability_score, summarize_returns
from atlas.investment.alpha.walkforward.splitter import build_walkforward_splits
from atlas.investment.alpha.walkforward.trainer import select_train_strategies


OUT_DIR = Path("output/investment_alpha")
TRADES_CSV = OUT_DIR / "alpha_backtest_trades.csv"
RANKINGS_CSV = OUT_DIR / "alpha_rankings.csv"
JSON_PATH = OUT_DIR / "walkforward_results.json"
SUMMARY_CSV = OUT_DIR / "walkforward_summary.csv"
MD_PATH = OUT_DIR / "walkforward_report.md"


def build_walkforward_alpha_report(
    *,
    exposure: float = 0.10,
    drawdown_control: bool = False,
    train_days: int = 730,
    test_days: int = 180,
    step_days: int = 180,
    top_n: int = 5,
    min_train_trades: int = 30,
) -> dict[str, Any]:
    """Build walk-forward validation report."""
    trades = pd.read_csv(TRADES_CSV) if TRADES_CSV.exists() else pd.DataFrame()
    rankings = pd.read_csv(RANKINGS_CSV) if RANKINGS_CSV.exists() else pd.DataFrame()

    if trades.empty:
        report = {
            "success": False,
            "error": f"Missing or empty trades file: {TRADES_CSV}",
        }
        write_outputs(report)
        return report

    trades["date"] = pd.to_datetime(trades["date"], errors="coerce")
    trades["return"] = pd.to_numeric(trades["return"], errors="coerce")
    trades = trades.dropna(subset=["date", "return"])

    splits = build_walkforward_splits(
        trades["date"],
        train_days=train_days,
        test_days=test_days,
        step_days=step_days,
    )

    results = []

    for split in splits:
        selected = select_train_strategies(
            rankings,
            trades,
            split,
            top_n=top_n,
            min_train_trades=min_train_trades,
        )

        results.append(
            evaluate_split(
                selected,
                trades,
                split,
                exposure=exposure,
                drawdown_control=drawdown_control,
            )
        )

    test_returns = []

    for result in results:
        selected_ids = [s["hypothesis_id"] for s in result.get("selected", [])]
        test_start = pd.to_datetime(result["test_start"])
        test_end = pd.to_datetime(result["test_end"])

        chunk = trades[
            (trades["hypothesis_id"].isin(selected_ids))
            & (trades["date"] >= test_start)
            & (trades["date"] < test_end)
        ].copy()

        chunk = non_overlapping_trades(chunk)

        if not chunk.empty:
            test_returns.extend(pd.to_numeric(chunk["return"], errors="coerce").dropna().tolist())

    aggregate_test = summarize_returns(
        pd.Series(test_returns),
        exposure=exposure,
        drawdown_control=drawdown_control,
    )

    stability = stability_score(results)

    report = {
        "success": True,
        "version": "walkforward_alpha_v1_2_risk_control",
        "params": {
            "train_days": train_days,
            "test_days": test_days,
            "step_days": step_days,
            "top_n": top_n,
            "min_train_trades": min_train_trades,
            "exposure": exposure,
            "drawdown_control": drawdown_control,
        },
        "split_count": len(results),
        "stability_score": stability,
        "aggregate_test": aggregate_test,
        "results": results,
        "summary": (
            f"Walk-forward Alpha v1.2 evaluated {len(results)} split(s). "
            f"Exposure: {exposure}. Drawdown control: {drawdown_control}. "
            f"Stability score: {stability}. "
            f"Aggregate test avg return: {aggregate_test.get('avg_return')}."
        ),
    }

    write_outputs(report)
    return report


def write_outputs(report: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    JSON_PATH.write_text(json.dumps(report, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    MD_PATH.write_text(build_markdown(report), encoding="utf-8")

    rows = []
    for r in report.get("results", []) or []:
        rows.append({
            "split_id": r.get("split_id"),
            "train_start": r.get("train_start"),
            "train_end": r.get("train_end"),
            "test_start": r.get("test_start"),
            "test_end": r.get("test_end"),
            "selected_count": len(r.get("selected", [])),
            "raw_test_count": r.get("raw_test_count"),
            "non_overlap_test_count": r.get("non_overlap_test_count"),
            "test_count": (r.get("test", {}) or {}).get("count"),
            "test_win_rate": (r.get("test", {}) or {}).get("win_rate"),
            "test_avg_return": (r.get("test", {}) or {}).get("avg_return"),
            "test_profit_factor": (r.get("test", {}) or {}).get("profit_factor"),
            "test_max_drawdown": (r.get("test", {}) or {}).get("max_drawdown"),
            "test_final_equity": (r.get("test", {}) or {}).get("final_equity"),
        })

    pd.DataFrame(rows).to_csv(SUMMARY_CSV, index=False)


def build_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Walk-Forward Alpha Report",
        "",
        report.get("summary", report.get("error", "")),
        "",
        "## Parameters",
        "",
        "```json",
        json.dumps(report.get("params", {}), indent=2),
        "```",
        "",
        "## Aggregate Test",
        "",
        "```json",
        json.dumps(report.get("aggregate_test", {}), indent=2),
        "```",
        "",
        "## Splits",
        "",
    ]

    for r in report.get("results", []) or []:
        lines.extend([
            f"### {r.get('split_id')}",
            "",
            f"- Train: `{r.get('train_start')}` -> `{r.get('train_end')}`",
            f"- Test: `{r.get('test_start')}` -> `{r.get('test_end')}`",
            f"- Selected: `{[s.get('hypothesis_id') for s in r.get('selected', [])]}`",
            f"- Raw test count: `{r.get('raw_test_count')}`",
            f"- Non-overlap test count: `{r.get('non_overlap_test_count')}`",
            f"- Test metrics: `{r.get('test')}`",
            "",
        ])

    return "\n".join(lines)
