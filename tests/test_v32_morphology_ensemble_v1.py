from __future__ import annotations

import pandas as pd

from atlas.investment.morphology_intelligence.v32_ensemble import (
    ENTER_LONG,
    EXIT_POSITION,
    NO_ACTION,
    V32MorphologyEnsembleConfig,
    build_v32_morphology_ensemble,
)


def _v32(
    action: str = ENTER_LONG,
    exposure: float = 0.10,
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                ),
            "asset":
                "SOL",
            "combined_action":
                action,
            "combined_direction":
                (
                    "LONG"
                    if action == ENTER_LONG
                    else "FLAT"
                ),
            "combined_target_exposure":
                exposure,
        }
    ])


def _morphology(
    *,
    action: str = "ENTER",
    direction: str = "LONG",
    confidence: float = 0.90,
    entry_ready: bool = True,
) -> pd.DataFrame:
    return pd.DataFrame([
        {
            "decision_id":
                "MORPH-1",
            "timestamp":
                pd.Timestamp(
                    "2026-01-01T00:00:00Z"
                ),
            "asset":
                "SOL",
            "action":
                action,
            "direction":
                direction,
            "confidence":
                confidence,
            "entry_ready":
                entry_ready,
        }
    ])


def test_supportive_morphology_preserves_entry() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=_morphology(),
    )

    row = decisions.iloc[0]

    assert row["combined_action"] == ENTER_LONG
    assert row["morphology_state"] == "SUPPORTIVE"
    assert row["combined_target_exposure"] == 0.10
    assert bool(row["entry_ready"])


def test_adverse_morphology_vetoes_entry() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=_morphology(
            action="AVOID",
            direction="FLAT",
            confidence=0.10,
            entry_ready=False,
        ),
    )

    row = decisions.iloc[0]

    assert row["combined_action"] == NO_ACTION
    assert row["combined_target_exposure"] == 0.0
    assert bool(row["morphology_veto"])


def test_morphology_cannot_originate_trade() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(
            action=NO_ACTION,
            exposure=0.0,
        ),
        morphology_decisions=_morphology(),
    )

    row = decisions.iloc[0]

    assert row["combined_action"] == NO_ACTION
    assert not bool(row["entry_ready"])


def test_v32_exit_always_passes_through() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(
            action=EXIT_POSITION,
            exposure=0.0,
        ),
        morphology_decisions=_morphology(
            action="AVOID",
            confidence=0.0,
            entry_ready=False,
        ),
    )

    row = decisions.iloc[0]

    assert row["combined_action"] == EXIT_POSITION
    assert row["combined_target_exposure"] == 0.0


def test_unavailable_morphology_reduces_exposure() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=pd.DataFrame(),
        config=V32MorphologyEnsembleConfig(
            unavailable_exposure_multiplier=0.25,
        ),
    )

    row = decisions.iloc[0]

    assert row["combined_action"] == ENTER_LONG
    assert row["combined_target_exposure"] == 0.025


def test_bridge_never_authorizes_live_orders() -> None:
    decisions = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=_morphology(),
    )

    assert not decisions[
        "live_authorized"
    ].astype(bool).any()

    assert not decisions[
        "order_submission_allowed"
    ].astype(bool).any()

    assert decisions[
        "requires_manual_approval"
    ].astype(bool).all()


def test_decision_ids_are_deterministic() -> None:
    first = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=_morphology(),
    )

    second = build_v32_morphology_ensemble(
        v32_decisions=_v32(),
        morphology_decisions=_morphology(),
    )

    assert first[
        "ensemble_decision_id"
    ].tolist() == second[
        "ensemble_decision_id"
    ].tolist()
