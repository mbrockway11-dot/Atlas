from atlas.astronomy import (
    ASTRONOMY_ONLY_BODIES,
    CANONICAL_BODIES,
    CLASSICAL_KAMEA_BODIES,
    angular_separation,
    build_physical_astronomy,
)
from atlas.css_schema import validate_multiscale_css
from atlas.kamea_normalization import build_normalized_kamea_graphs
from atlas.research.outer_planet_symbolic_transforms import (
    disabled_outer_planet_transform_registry,
)
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
    for body in ASTRONOMY_ONLY_BODIES:
        assert report["bodies"][body]["symbolic_projection"] == {
            "available": False,
            "reason": "no_historical_classical_kamea",
        }
        edges = [
            row
            for row in report["planet_graph"]["edges"]
            if body in {row["source"], row["target"]}
        ]
        assert len(edges) == 9
        assert all("normalized_orb_strength" in row for row in edges)
        assert all("applying_separating" in row for row in edges)
        assert "longitude_degrees" in report["bodies"][body][
            "tropical_coordinates"
        ]
        assert "longitude_degrees" in report["bodies"][body][
            "sidereal_lahiri_coordinates"
        ]


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


def test_only_seven_classical_kamea_graphs_are_generated():
    classical = build_normalized_kamea_graphs(
        seven_planet_payload(include_outer=False)
    )
    with_outer = build_normalized_kamea_graphs(
        seven_planet_payload(include_outer=True)
    )

    assert set(classical["graphs"]) == {
        body.casefold() for body in CLASSICAL_KAMEA_BODIES
    }
    assert len(classical["graphs"]) == 7
    assert with_outer["graphs"] == classical["graphs"]
    assert with_outer["excluded_nonclassical_streams"] == [
        "neptune",
        "pluto",
        "uranus",
    ]
    for body in ("uranus", "neptune", "pluto"):
        assert with_outer["projection_registry"][body] == {
            "available": False,
            "reason": "no_historical_classical_kamea",
            "generated": False,
        }


def test_heterogeneous_graph_schema_and_similarity_channels():
    astronomy = full_synthetic_astronomy()
    normalized = build_normalized_kamea_graphs(seven_planet_payload())
    result = build_structural_measurement(astronomy, normalized["graphs"])
    nodes = {
        row["node_id"]: row
        for row in result["master_graph"]["nodes"]
    }

    assert result["schema_validation"]["success"] is True
    assert result["master_graph"]["node_count"] == 10
    assert {
        row["node_type"] for row in result["master_graph"]["nodes"]
    } == {"astronomical_kamea_node", "astronomical_only_node"}
    for body in CLASSICAL_KAMEA_BODIES:
        assert nodes[body]["node_type"] == "astronomical_kamea_node"
        assert nodes[body]["kamea_graph_available"] is True
    for body in ASTRONOMY_ONLY_BODIES:
        assert nodes[body]["node_type"] == "astronomical_only_node"
        assert nodes[body]["kamea_graph_available"] is False
        assert nodes[body]["symbolic_projection"]["reason"] == (
            "no_historical_classical_kamea"
        )
    assert result["combined_multilayer_similarity"][
        "missing_outer_planet_kamea_penalty"
    ] == 0.0
    assert result["canonical_transform_policy"][
        "interpretive_operators_executed"
    ] == []
    assert result["canonical_transform_policy"][
        "kamea_graph_mutation_by_astronomy"
    ] is False


def test_schema_rejects_fabricated_outer_kamea_without_validity_penalty_for_absence():
    astronomy = full_synthetic_astronomy()
    graphs = build_normalized_kamea_graphs(seven_planet_payload())["graphs"]
    result = build_structural_measurement(astronomy, graphs)
    validation = validate_multiscale_css(
        astronomy=astronomy,
        normalized_kamea_graphs=graphs,
        structural_measurement=result,
    )
    assert validation["success"] is True
    assert validation["profile_validity"] == {
        "outer_planet_kamea_required": False,
        "missing_outer_planet_kamea_penalty": 0.0,
    }

    invalid = validate_multiscale_css(
        astronomy=astronomy,
        normalized_kamea_graphs={**graphs, "uranus": {}},
        structural_measurement=result,
    )
    assert invalid["success"] is False
    assert "nonclassical_kamea_projection_forbidden" in invalid["errors"]


def test_outer_planet_symbolic_hypotheses_are_disabled_and_noncanonical():
    registry = disabled_outer_planet_transform_registry()
    assert registry["status"] == "disabled"
    assert registry["execution_allowed_in_canonical_css"] is False
    assert {
        row["hypothesis"]
        for row in registry["transforms"].values()
    } == {"rewiring", "diffusion", "pruning_or_persistence"}
    assert all(
        row["enabled"] is False and row["canonical"] is False
        for row in registry["transforms"].values()
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


def seven_planet_payload(*, include_outer: bool = False) -> dict:
    bodies = list(CLASSICAL_KAMEA_BODIES)
    if include_outer:
        bodies.extend(ASTRONOMY_ONLY_BODIES)
    return {
        "profile_key": "seven-planets",
        "kamea": {
            "construction_passes": [
                {
                    "cipher": "ordinal",
                    "planet": body,
                    "steps": [
                        {"value": 1, "x": 0, "y": 0},
                        {"value": 2, "x": 1, "y": 1},
                    ],
                }
                for body in bodies
            ]
        },
    }


def full_synthetic_astronomy() -> dict:
    bodies = {}
    for index, body in enumerate(CANONICAL_BODIES):
        bodies[body] = {
            "ecliptic_longitude_degrees": index * 30.0,
            "ecliptic_latitude_degrees": 0.0,
            "distance_au": 1.0,
            "apparent_longitude_velocity_deg_per_day": 1.0,
            "retrograde": False,
            "iau_constellation": "Example",
            "iau_constellation_abbreviation": "Ex",
            "tropical_sign": "Example",
            "sidereal_lahiri_sign": "Example",
            "tropical_coordinates": {
                "longitude_degrees": index * 30.0,
                "latitude_degrees": 0.0,
                "sign": "Example",
                "degree_in_sign": 0.0,
            },
            "sidereal_lahiri_coordinates": {
                "longitude_degrees": index * 30.0,
                "latitude_degrees": 0.0,
                "sign": "Example",
                "degree_in_sign": 0.0,
                "ayanamsha_degrees": 0.0,
            },
            "symbolic_projection": (
                {
                    "available": True,
                    "basis": "historical_classical_kamea",
                }
                if body in CLASSICAL_KAMEA_BODIES
                else {
                    "available": False,
                    "reason": "no_historical_classical_kamea",
                }
            ),
        }
    return {
        "bodies": bodies,
        "planet_graph": {"nodes": [], "edges": []},
        "interpretation_applied": False,
    }
