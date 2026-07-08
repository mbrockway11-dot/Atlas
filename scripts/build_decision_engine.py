
"""Build Decision Engine."""

from __future__ import annotations

from atlas.investment.decision import build_decision_engine_report


def main() -> None:
    report = build_decision_engine_report()

    print(report["success"])
    print(report["summary"])
    print("Evidence:", report["evidence"])
    print("Conflict:", report["conflict"])
    print("Decision:", report["risk_adjusted_decision"])
    print("Outputs:", report["outputs"])


if __name__ == "__main__":
    main()
