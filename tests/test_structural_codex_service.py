import json

from atlas.services.structural_codex_service import (
    build_structural_codex,
    calculate_life_path,
    percentile_rank,
    write_structural_codex_outputs,
)
from atlas.services import profile_compile_service


def profile_payload():
    return {
        "success": True,
        "profile_key": "example_person",
        "identity": {
            "display_name": "Example Person",
        },
        "birth": {
            "date": "1993-08-16",
            "time": "17:30",
            "place": "Janesville, Wisconsin",
        },
        "classification": {
            "name": "Example Person",
            "structural_role": "Persistence-Architect",
            "structural_subtype": "Persistent Distributed Architect",
            "civilization_function": "Builds continuity across distributed systems.",
            "cognitive_style": "Durable, integrative, and persistence-oriented.",
            "motivation": "Motivated by coherence and endurance.",
            "emotional_pattern": "Emotion may intensify when continuity breaks.",
            "stress_response": "May attempt to hold too much structure together alone.",
            "growth_path": "Allow structure to evolve without losing continuity.",
            "confidence": {"score": 0.9, "percent": 90.0, "label": "high"},
            "basis": {
                "dominant_motif": "hub",
                "topology_class": "distributed_sparse",
                "dominant_topology_axis": "persistence",
                "resonance_class": "low_resonance",
                "dominant_resonance_axis": "stability",
                "motif_richness": 0.4,
                "raw_node_count": 70,
                "raw_edge_count": 315,
                "truth_node_count": 39,
                "truth_edge_count": 16,
                "has_ephemeris": True,
            },
        },
        "graph": {"summary": {}},
    }


def profile_summary():
    return {
        "analyses": [
            analysis("hebrew_literal", "mercury", 0.9, "hub"),
            analysis("hebrew_phonetic", "jupiter", 0.8, "hub"),
            analysis("ordinal", "sun", 0.7, "chain"),
        ]
    }


def analysis(cipher, planet, score, motif):
    return {
        "cipher": cipher,
        "planet": planet,
        "signature": {
            "scores": {
                "driver": score,
                "amplifier": score,
                "regulator": score,
            },
            "patterns": {"dominant_pattern": "distributed"},
            "motifs": {"dominant_motif": motif},
        },
    }


def write_population(path):
    payload = {
        "profile_count": 3,
        "profiles": [
            population_row("example_person", 0.4, 70, 315, 39, 16),
            population_row("neighbor_a", 0.3, 60, 240, 30, 12),
            population_row("neighbor_b", 0.8, 100, 500, 50, 40, role="Pattern-Weaver"),
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def population_row(key, motif, raw_nodes, raw_edges, truth_nodes, truth_edges, role="Persistence-Architect"):
    return {
        "profile_key": key,
        "name": key.replace("_", " ").title(),
        "role": role,
        "subtype": "Persistent Distributed Architect",
        "topology_class": "distributed_sparse",
        "dominant_axis": "persistence",
        "dominant_motif": "hub",
        "motif_richness": motif,
        "raw_nodes": raw_nodes,
        "raw_edges": raw_edges,
        "truth_nodes": truth_nodes,
        "truth_edges": truth_edges,
        "raw_density": raw_edges / raw_nodes,
        "truth_density": truth_edges / truth_nodes,
    }


def test_structural_codex_resolves_every_claim_to_evidence(tmp_path):
    population = tmp_path / "population.json"
    write_population(population)

    codex = build_structural_codex(
        profile_payload(),
        profile_summary=profile_summary(),
        population_path=population,
    )

    assert codex["success"] is True
    assert codex["archetype"]["label"] == "The Persistence Architect"
    assert codex["population_context"]["corpus_size"] == 3
    assert codex["population_context"]["neighbors"][0]["profile_key"] == "neighbor_a"
    assert codex["schema_version"] == "atlas.structural-codex.v2"
    assert codex["symbolic_profile"]["numerology"]["core_numbers"]["expression"]
    assert codex["symbolic_profile"]["gematria"]["systems"]["ordinal"]
    assert "gematria_synthesis" in {section["key"] for section in codex["sections"]}

    evidence_ids = {row["id"] for row in codex["evidence_registry"]}
    assert {"M01", "M15", "S01", "S02", "S05", "N01", "N04", "G01", "G05", "P08"} <= evidence_ids
    for section in codex["sections"]:
        assert set(section["evidence_refs"]) <= evidence_ids
        assert {row["id"] for row in section["metrics"]} == set(section["evidence_refs"])
        for claim in section["claims"]:
            assert set(claim["evidence_refs"]) <= evidence_ids

    symbolic = [
        claim
        for section in codex["sections"]
        for claim in section["claims"]
        if claim["claim_type"] == "symbolic_interpretation"
    ]
    assert symbolic
    assert all(claim["confidence_label"] == "symbolic" for claim in symbolic)
    assert "[M01]" in codex["exports"]["markdown"]


def test_structural_codex_writes_json_and_markdown(tmp_path):
    population = tmp_path / "population.json"
    write_population(population)
    codex = build_structural_codex(
        profile_payload(),
        profile_summary=profile_summary(),
        population_path=population,
    )

    paths = write_structural_codex_outputs(codex, tmp_path / "profile")

    assert (tmp_path / "profile" / "structural_codex.json").exists()
    assert (tmp_path / "profile" / "structural_codex.md").exists()
    assert set(paths) == {"json", "markdown"}


def test_life_path_and_percentile_helpers_are_deterministic():
    assert calculate_life_path("1993-08-16") == 1
    assert calculate_life_path("") is None
    assert percentile_rank(2.0, [1.0, 2.0, 3.0]) == 50.0


def test_profile_compile_service_persists_structural_codex(monkeypatch, tmp_path):
    profile_dir = tmp_path / "example_person"
    profile_dir.mkdir()
    (profile_dir / "profile.intake.json").write_text("{}", encoding="utf-8")
    canonical = profile_payload()
    canonical["payload_path"] = str(profile_dir / "profile.payload.json")

    monkeypatch.setattr(
        profile_compile_service,
        "resolve_profile_dir",
        lambda profile_key: profile_dir,
    )
    monkeypatch.setattr(
        profile_compile_service,
        "compile_canonical_profile",
        lambda profile_key, force=False: canonical,
    )
    monkeypatch.setattr(
        profile_compile_service,
        "build_structural_codex",
        lambda payload, profile_summary=None: {
            "success": True,
            "profile_key": "example_person",
            "exports": {"markdown": "# Codex\n"},
        },
    )

    result = profile_compile_service.compile_person_profile("example_person")

    assert result["success"] is True
    assert result["artifact_status"]["structural_codex.json"] is True
    assert result["artifact_status"]["structural_codex.md"] is True
    assert (profile_dir / "structural_codex.json").exists()
