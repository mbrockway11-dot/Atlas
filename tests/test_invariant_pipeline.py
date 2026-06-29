from atlas.invariant.pipeline import (
    build_sequence_summary,
    normalize_input,
    run_invariant_pipeline,
)


def test_normalize_input():
    assert normalize_input("Michael Elvis Brockway") == "MICHAELELVISBROCKWAY"
    assert normalize_input("A-B C!") == "ABC"


def test_build_sequence_summary():
    summary = build_sequence_summary(
        {
            "ordinal": [1, 2, 1],
        }
    )

    assert summary["ordinal"]["length"] == 3
    assert summary["ordinal"]["sum"] == 4
    assert summary["ordinal"]["repetition"] == 1


def test_run_invariant_pipeline():
    result = run_invariant_pipeline("Michael Elvis Brockway")

    assert result["name"] == "Michael Elvis Brockway"
    assert result["normalized"] == "MICHAELELVISBROCKWAY"
    assert result["analysis_count"] == 21
    assert len(result["analyses"]) == 21

    assert "sequences" in result
    assert "top_kameas" in result
    assert len(result["top_kameas"]) == 3

    assert "ranked_kameas" in result
    assert "subtype" in result
    assert "planetary_weights" in result
    assert "planetary_contrast" in result
    assert "structural_summary" in result

    contrast = result["planetary_contrast"]

    assert "raw_scores" in contrast
    assert "mean_score" in contrast
    assert "z_scores" in contrast
    assert "ranked" in contrast
    assert "dominance_gap" in contrast
    assert "is_distinct_motion_profile" in contrast