"""Top-3 vs bottom-4 kamea activity differential."""

import pytest

from atlas.invariant.pipeline import build_planetary_differential


def _ranked(scores):
    """Build a ranked_kameas list (already sorted desc) from (planet, score)."""
    return [
        {"planet": p, "score": s, "z_score": s}
        for p, s in scores
    ]


def test_differential_splits_top3_and_bottom4():
    ranked = _ranked([
        ("Saturn", 0.9), ("Jupiter", 0.8), ("Mars", 0.7),   # top 3
        ("Sun", 0.4), ("Venus", 0.3), ("Mercury", 0.2), ("Moon", 0.1),  # bottom 4
    ])
    diff = build_planetary_differential(ranked)
    assert diff["top_planets"] == ["Saturn", "Jupiter", "Mars"]
    assert diff["bottom_planets"] == ["Sun", "Venus", "Mercury", "Moon"]
    assert diff["top_mean_score"] == pytest.approx(0.8)      # mean(.9,.8,.7)
    assert diff["bottom_mean_score"] == pytest.approx(0.25)  # mean(.4,.3,.2,.1)
    assert diff["score_differential"] == pytest.approx(0.55)  # 0.80 - 0.25


def test_peaked_profile_has_larger_differential_than_flat():
    peaked = build_planetary_differential(_ranked([
        ("Saturn", 1.0), ("Jupiter", 0.9), ("Mars", 0.8),
        ("Sun", 0.1), ("Venus", 0.1), ("Mercury", 0.1), ("Moon", 0.1),
    ]))
    flat = build_planetary_differential(_ranked([
        ("Saturn", 0.55), ("Jupiter", 0.52), ("Mars", 0.51),
        ("Sun", 0.50), ("Venus", 0.49), ("Mercury", 0.48), ("Moon", 0.47),
    ]))
    assert peaked["score_differential"] > flat["score_differential"]


def test_fewer_than_four_planets_is_safe():
    diff = build_planetary_differential(_ranked([("Saturn", 0.5), ("Mars", 0.3)]))
    assert diff["score_differential"] == 0.0
    assert diff["bottom_planets"] == []


def test_rank_kameas_is_population_relative():
    from atlas.invariant.pipeline import rank_kameas
    # Moon far above its low baseline (0.14), Saturn merely at its high baseline
    # (0.69). Relatively, Moon is the standout -- it must outrank Saturn even
    # though Saturn's RAW score is much larger (the old bug ranked by raw).
    analyses = [
        {"planet": "Moon", "kamea_score": 0.30},
        {"planet": "Saturn", "kamea_score": 0.686},
    ]
    ranked = rank_kameas(analyses)
    assert ranked[0]["planet"] == "Moon"
    assert ranked[0]["score"] < ranked[1]["score"]  # won despite a lower raw score
