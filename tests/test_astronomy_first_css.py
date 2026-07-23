from atlas.astronomy import (
    CANONICAL_BODIES,
    angular_separation,
    build_physical_astronomy,
)
from atlas.kamea_normalization import build_normalized_kamea_graphs
from atlas.structural_measurement import build_structural_measurement
from atlas.temporal.models import BirthData
from atlas.core.canonical_structural_signature import CanonicalStructuralSignature
from atlas.core.compiler_framework import CompilerContext
from atlas.core.compiler_passes.compiler import build_default_engine


def test_physical_astronomy_is_complete_and_interpretation_free():
    report = build_physical_astronomy(BirthData(
        name="Test",
        birth_date="2000-01-01",
        birth_time="12:00",
        birth_place="",
        time_known=False,
    ))

    assert report["success"] is True
    assert report["interpretation_applied"] is False
    assert tuple(report["bodies"]) == CANONICAL_BODIES
    assert report["planet_graph"]["node_count"] == 10
    assert report["planet_graph"]["edge_count"] == 45
    assert report["bodies"]["Sun"]["distance_au"] > 0
    assert "right_ascension_degrees" in report["bodies"]["Pluto"]
    assert "iau_constellation" in report["bodies"]["Uranus"]


def test_angular_separation_wraps_at_zero():
    assert angular_separation(359.0, 1.0) == 2.0


def test_normalized_kamea_graph_collapses_repeated_geometry_into_weights():
    payload = {
        "profile_key": "example",
        "kamea": {
            "construction_passes": [
                {
                    "cipher": "ordinal",
                    "planet": "saturn",
                    "steps": [
                        {"value": 1, "x": 0, "y": 0},
                        {"value": 2, "x": 1, "y": 0},
                        {"value": 1, "x": 0, "y": 0},
                    ],
                }
            ]
        },
    }
    result = build_normalized_kamea_graphs(payload)
    graph = result["graphs"]["saturn"]

    assert graph["source_grid_sizes"] == [3]
    assert graph["node_count"] == 2
    assert max(node["weight"] for node in graph["nodes"]) == 2
    assert all(0.0 <= node["x"] <= 1.0 for node in graph["nodes"])
    assert graph["metrics"]["revisit_intensity"] > 0


def test_graph_of_graphs_uses_aspects_and_defers_classification():
    astronomy = {
        "bodies": {"Sun": {}, "Moon": {}},
        "planet_graph": {
            "edges": [
                {
                    "source": "Sun",
                    "target": "Moon",
                    "aspect_type": "trine",
                    "angular_separation_degrees": 120.0,
                    "orb_degrees": 0.0,
                    "orb_strength": 1.0,
                }
            ]
        },
    }
    result = build_structural_measurement(
        astronomy,
        {"sun": {"node_count": 2, "edge_count": 1, "metrics": {"entropy": 0.5}}},
    )

    assert result["master_graph"]["node_count"] == 2
    assert result["master_graph"]["edge_count"] == 1
    assert result["master_graph"]["interpretation_applied"] is False
    assert result["topology_classification"]["status"] == (
        "unclassified_pending_population_fit"
    )


def test_css_compiler_orders_measurement_before_temporal_interpretation():
    payload = {
        "profile_key": "example",
        "profile.intake": {
            "name": "Example",
            "birth_date": "2000-01-01",
            "birth_time": "12:00",
            "birth_place": "",
        },
        "kamea": {
            "construction_passes": [
                {
                    "cipher": "ordinal",
                    "planet": "sun",
                    "steps": [
                        {"value": 1, "x": 0, "y": 0},
                        {"value": 2, "x": 1, "y": 1},
                    ],
                }
            ]
        },
    }
    css, results = build_default_engine().run(
        CanonicalStructuralSignature(),
        CompilerContext(profile_key="example", profile_payload=payload),
    )
    names = [row.name for row in results]

    assert names.index("astronomy") < names.index("kamea")
    assert names.index("structural_measurement") < names.index("temporal")
    assert css.astronomy.measurements["interpretation_applied"] is False
    assert css.kamea.normalized_graphs
    assert css.structural_measurement.master_graph["interpretation_applied"] is False
