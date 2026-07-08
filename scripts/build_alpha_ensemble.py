
"""Build Alpha Ensemble."""

from __future__ import annotations

from atlas.investment.alpha.ensemble import build_alpha_ensemble_report


def main() -> None:
    report = build_alpha_ensemble_report()

    print(report["success"])
    print(report["summary"])
    print("Promoted strategies:", report.get("promoted_strategy_count"))
    print("Signals:", report.get("signal_count"))
    print("Votes:", report.get("vote_count"))
    print("Latest:", report.get("latest_signal"))
    print("Outputs:", report.get("outputs"))


if __name__ == "__main__":
    main()
