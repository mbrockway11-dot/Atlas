"""Export Alpha Ensemble v6.1 governance audit."""

from __future__ import annotations

from pathlib import Path

from atlas.investment.alpha_ensemble.governance import (
    build_engine_governance,
)
from atlas.investment.alpha_ensemble.loader import (
    load_alpha_ensemble_inputs,
)


OUTPUT = Path(
    "output/investment_alpha_ensemble/"
    "alpha_ensemble_engine_governance.csv"
)


def main() -> None:
    inputs = load_alpha_ensemble_inputs()

    governance = build_engine_governance(
        inputs.get("research_decisions"),
        learning_recommendations=inputs.get(
            "engine_learning_recommendations"
        ),
        regime_suitability=inputs.get(
            "engine_regime_suitability"
        ),
    )

    OUTPUT.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    governance.to_csv(
        OUTPUT,
        index=False,
    )

    print(True)
    print(
        "Alpha Ensemble v6.1 governance "
        f"exported {len(governance)} engine row(s)."
    )

    for _, row in governance.iterrows():
        print({
            "engine_id": row.get(
                "engine_id"
            ),
            "decision": row.get(
                "decision"
            ),
            "eligible": bool(
                row.get(
                    "eligible",
                    False,
                )
            ),
            "base": row.get(
                "base_governance_weight"
            ),
            "learning": row.get(
                "learning_modifier"
            ),
            "regime": row.get(
                "regime_modifier"
            ),
            "combined": row.get(
                "combined_modifier"
            ),
            "final": row.get(
                "governance_weight"
            ),
        })

    print("Output:", OUTPUT)


if __name__ == "__main__":
    main()
