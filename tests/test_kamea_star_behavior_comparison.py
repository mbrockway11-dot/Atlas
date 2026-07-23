import json

from scripts.build_kamea_star_behavior_comparison import (
    build_dynamic_hypotheses,
    circular_span_degrees,
    merge_json_extension,
    update_codex_report,
)


def test_circular_span_handles_zero_degree_wraparound():
    assert circular_span_degrees([353.0, 0.5, 6.0]) == 13.0


def _profile(curve: float, displacement: float, tortuosity: float, ophiuchus=None):
    return {
        "shape": {
            "mean_within_planet_curve_similarity": curve,
            "mean_displacement": displacement,
            "mean_tortuosity": tortuosity,
            "strongest_shape_consensus_planet": "saturn",
        },
        "event_dynamics": {"role_sequence": ["role"]},
        "astronomical_constellations": {
            "planets": {
                "Mercury": {
                    "actual_constellation": "Orion",
                    "ecliptic_path_constellation": "Gemini",
                }
            },
            "ophiuchus_planets": ophiuchus or [],
        },
        "birth_time_constellation_sensitivity": {
            "actual_constellation_stable": False,
        },
    }


def test_dynamic_hypotheses_are_explicitly_unretained():
    profiles = {
        "a": _profile(0.8, 0.7, 10.0),
        "b": _profile(0.6, 0.5, 13.0, ["Moon"]),
    }
    comparison = {
        "mean_consensus_shape_jaccard": 0.1,
        "mean_directional_shape_jaccard": 0.02,
        "strongest_shape_confluence_planet": "jupiter",
    }

    result = build_dynamic_hypotheses(profiles, comparison)

    assert result["hypothesis_count"] == 5
    assert result["retained_findings"] == 0
    assert result["causal_claim"] is False
    assert all(row["falsification_test"] for row in result["hypotheses"])


def test_merge_json_extension_preserves_existing_summary(tmp_path):
    path = tmp_path / "profile_summary.json"
    path.write_text(json.dumps({"name": "Example", "analyses": [1]}), encoding="utf-8")

    merge_json_extension(path, {"version": "v1", "retained_findings": 0})
    result = json.loads(path.read_text(encoding="utf-8"))

    assert result["name"] == "Example"
    assert result["analyses"] == [1]
    assert result["symbolic_dynamics"]["version"] == "v1"


def test_codex_dynamic_section_is_idempotent(tmp_path):
    path = tmp_path / "codex_report.md"
    path.write_text("# Original\n", encoding="utf-8")
    extension = {
        "shape": {
            "mean_within_planet_curve_similarity": 0.8,
            "mean_shape_consensus_ratio": 0.6,
            "mean_displacement": 0.7,
            "mean_tortuosity": 10.0,
            "strongest_shape_consensus_planet": "saturn",
        },
        "vedic": {"moon_nakshatra": "Hasta"},
        "astronomical_constellations": {"ophiuchus_planets": []},
        "birth_time_constellation_sensitivity": {
            "actual_constellation_stable": True,
        },
        "hypotheses": [{"hypothesis_id": "h1"}],
        "retained_findings": 0,
    }

    update_codex_report(path, extension)
    update_codex_report(path, extension)
    content = path.read_text(encoding="utf-8")

    assert content.count("ATLAS_SYMBOLIC_DYNAMICS_START") == 1
    assert content.count("ATLAS_SYMBOLIC_DYNAMICS_END") == 1
    assert "# Original" in content
