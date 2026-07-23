"""Evidence-backed Structural Codex profiles.

This service turns canonical Atlas metrics into professional narrative sections.
Every claim carries evidence references so the UI can show why it was made.
Symbolic interpretations are labeled and are never presented as clinical facts.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import json
from pathlib import Path
from statistics import mean
from typing import Any, Iterable

from atlas.compiler.canonical_profile_compiler import compile_canonical_profile
from atlas.population.structural_neighbors_v2 import (
    build_structural_vector,
    compare_vectors,
)
from atlas.profiles.summary import build_individual_profile_summary
from atlas.services.profile_path_service import PROJECT_ROOT, resolve_profile_dir
from atlas.services.symbolic_profile_service import (
    NUMBER_THEMES,
    build_gematria_profile,
    build_numerology_profile,
)


STRUCTURAL_CODEX_SCHEMA_VERSION = "atlas.structural-codex.v2"
DEFAULT_POPULATION_PATH = (
    PROJECT_ROOT / "output" / "population" / "population_intelligence_v2.json"
)

PLANET_THEMES = {
    "mercury": "analysis, language, symbolic reasoning, and information design",
    "sun": "identity, purpose, visibility, and directed creation",
    "jupiter": "synthesis, learning, mentorship, and expansion of frameworks",
    "saturn": "discipline, boundaries, durability, and institutional structure",
    "mars": "initiative, decisive action, pressure response, and execution",
    "venus": "value alignment, relationship, aesthetics, and harmonization",
    "moon": "adaptation, memory, responsiveness, and continuity of experience",
}

ROLE_ENVIRONMENTS = {
    "Persistence-Architect": [
        "systems architecture",
        "research infrastructure",
        "long-horizon strategy",
        "knowledge management",
        "institution building",
    ],
    "Connector-Architect": [
        "platform design",
        "cross-functional integration",
        "ecosystem strategy",
        "partnership architecture",
        "technical leadership",
    ],
    "Pattern-Weaver": [
        "research and development",
        "complex-systems analysis",
        "intelligence synthesis",
        "model development",
        "strategic advisory",
    ],
    "Cycle-Weaver": [
        "temporal analysis",
        "scenario planning",
        "market-cycle research",
        "adaptive strategy",
        "forecast evaluation",
    ],
    "Regulator-Builder": [
        "operations design",
        "risk governance",
        "quality systems",
        "program management",
        "organizational infrastructure",
    ],
    "Amplifier-Connector": [
        "communications strategy",
        "community systems",
        "education",
        "business development",
        "network building",
    ],
    "Temporal-Interpreter": [
        "timing research",
        "historical analysis",
        "transition planning",
        "scenario interpretation",
        "developmental strategy",
    ],
}

def build_structural_codex_for_profile(
    profile_key: str,
    *,
    force_compile: bool = False,
    population_path: str | Path = DEFAULT_POPULATION_PATH,
    write_outputs: bool = False,
) -> dict[str, Any]:
    """Compile a profile and build its evidence-backed Structural Codex."""
    canonical = compile_canonical_profile(profile_key, force=force_compile)
    if not canonical.get("success"):
        return failure_payload(profile_key, canonical.get("errors", []))

    profile_dir = Path(canonical.get("profile_dir") or resolve_profile_dir(profile_key))
    summary = read_optional_json(profile_dir / "profile_summary.json")
    codex = build_structural_codex(
        canonical,
        profile_summary=summary,
        population_path=population_path,
    )

    if write_outputs and codex.get("success"):
        codex["output_paths"] = write_structural_codex_outputs(codex, profile_dir)

    return codex


def build_structural_codex(
    profile_payload: dict[str, Any],
    *,
    profile_summary: dict[str, Any] | None = None,
    population_path: str | Path = DEFAULT_POPULATION_PATH,
) -> dict[str, Any]:
    """Build a deterministic narrative whose claims resolve to metric evidence."""
    profile_key = str(profile_payload.get("profile_key") or "").strip()
    classification = as_dict(profile_payload.get("classification"))
    identity = as_dict(profile_payload.get("identity"))
    birth = as_dict(profile_payload.get("birth"))
    astronomy = as_dict(profile_payload.get("astronomy"))
    measurement = as_dict(profile_payload.get("structural_measurement"))
    basis = as_dict(classification.get("basis"))

    name = str(
        classification.get("name")
        or identity.get("display_name")
        or identity.get("full_name")
        or identity.get("name")
        or profile_key.replace("_", " ").title()
    )
    role = str(classification.get("structural_role") or "Unclassified Structural Actor")
    subtype = str(classification.get("structural_subtype") or "Unresolved Subtype")
    confidence = as_dict(classification.get("confidence"))
    warnings: list[str] = []
    resolved_summary = profile_summary or {}
    if not resolved_summary.get("analyses"):
        try:
            resolved_summary = build_individual_profile_summary(name)
        except Exception as exc:  # pragma: no cover - defensive optional layer
            warnings.append(f"Kamea and Hebrew score summary unavailable: {exc}")

    evidence: list[dict[str, Any]] = []
    add = evidence_appender(evidence)
    add("M01", "Structural role", role, "classification.structural_role", "deterministic classifier")
    add("M02", "Structural subtype", subtype, "classification.structural_subtype", "deterministic classifier")
    add("M03", "Classification confidence", confidence.get("percent", 0), "classification.confidence.percent", "evidence-completeness score", unit="percent")
    add("M04", "Topology class", basis.get("topology_class", "missing"), "classification.basis.topology_class", "graph topology classifier")
    add("M05", "Dominant topology axis", basis.get("dominant_topology_axis", "missing"), "classification.basis.dominant_topology_axis", "graph-genome maximum axis")
    add("M06", "Dominant motif", basis.get("dominant_motif", "missing"), "classification.basis.dominant_motif", "motif frequency comparison")
    add("M07", "Resonance class", basis.get("resonance_class", "missing"), "classification.basis.resonance_class", "resonance classifier")
    add("M08", "Dominant resonance axis", basis.get("dominant_resonance_axis", "missing"), "classification.basis.dominant_resonance_axis", "resonance-axis maximum")
    add("M09", "Motif richness", number(basis.get("motif_richness")), "classification.basis.motif_richness", "normalized motif count")
    add("M10", "Raw graph nodes", integer(basis.get("raw_node_count")), "classification.basis.raw_node_count", "canonical graph count", unit="nodes")
    add("M11", "Raw graph edges", integer(basis.get("raw_edge_count")), "classification.basis.raw_edge_count", "canonical graph count", unit="edges")
    add("M12", "Truth graph nodes", integer(basis.get("truth_node_count")), "classification.basis.truth_node_count", "truth-filtered graph count", unit="nodes")
    add("M13", "Truth graph edges", integer(basis.get("truth_edge_count")), "classification.basis.truth_edge_count", "truth-filtered graph count", unit="edges")
    add("M14", "Raw density proxy", density(basis.get("raw_edge_count"), basis.get("raw_node_count")), "derived.raw_density", "raw edges / raw nodes")
    add("M15", "Truth density proxy", density(basis.get("truth_edge_count"), basis.get("truth_node_count")), "derived.truth_density", "truth edges / truth nodes")
    add("M16", "Temporal ephemeris available", bool(basis.get("has_ephemeris")), "classification.basis.has_ephemeris", "temporal artifact presence")

    numerology = build_numerology_profile(name, str(birth.get("date") or ""))
    gematria = build_gematria_profile(name)
    life_path = as_dict(as_dict(numerology.get("core_numbers")).get("life_path")).get("number")
    numerology_claims: list[dict[str, Any]] = []
    if life_path is not None:
        add("S01", "Life Path number", life_path, "derived.birth.life_path", "digit reduction from recorded birth date", evidence_kind="symbolic")
        numerology_claims.append(symbolic_claim(f"Life Path {life_path} symbolically emphasizes {NUMBER_THEMES.get(life_path, 'an unresolved theme')}.", ["S01"]))

    numerology_refs: list[str] = ["S01"] if life_path is not None else []
    core_labels = {
        "birthday": "Birthday number",
        "attitude": "Attitude number",
        "expression": "Expression / Destiny number",
        "soul_urge": "Soul Urge number",
        "personality": "Personality number",
        "balance": "Balance number",
        "maturity": "Maturity number",
    }
    for index, (key, label) in enumerate(core_labels.items(), start=1):
        item = as_dict(as_dict(numerology.get("core_numbers")).get(key))
        if not item:
            continue
        identifier = f"N{index:02d}"
        add(identifier, label, item.get("number"), f"symbolic_profile.numerology.core_numbers.{key}", item.get("method", "deterministic number reduction"), evidence_kind="symbolic")
        numerology_refs.append(identifier)
        numerology_claims.append(symbolic_claim(f"{label} {item.get('number')} symbolically emphasizes {item.get('theme', 'an unresolved theme')}.", [identifier]))
    for offset, (label, values, source) in enumerate(
        [
            ("Hidden Passion numbers", [row.get("number") for row in numerology.get("hidden_passion_numbers", [])], "symbolic_profile.numerology.hidden_passion_numbers"),
            ("Karmic Lesson numbers", [row.get("number") for row in numerology.get("karmic_lesson_numbers", [])], "symbolic_profile.numerology.karmic_lesson_numbers"),
            ("Pinnacle sequence", [row.get("number") for row in numerology.get("pinnacles", [])], "symbolic_profile.numerology.pinnacles"),
            ("Challenge sequence", [row.get("number") for row in numerology.get("challenges", [])], "symbolic_profile.numerology.challenges"),
        ],
        start=8,
    ):
        identifier = f"N{offset:02d}"
        add(identifier, label, values, source, "deterministic Pythagorean frequency or birth-date formula", evidence_kind="symbolic")
        numerology_refs.append(identifier)
        if values:
            themes = "; ".join(f"{value}: {NUMBER_THEMES.get(value, 'unresolved')}" for value in values)
            numerology_claims.append(symbolic_claim(f"{label}: {themes}.", [identifier]))
    cycles = as_dict(numerology.get("cycles"))
    for offset, key in enumerate(("personal_year", "personal_month", "personal_day"), start=12):
        item = as_dict(cycles.get(key))
        if item:
            identifier = f"N{offset:02d}"
            add(identifier, key.replace("_", " ").title(), item.get("number"), f"symbolic_profile.numerology.cycles.{key}", item.get("method", "calendar-cycle reduction"), evidence_kind="symbolic")
            numerology_refs.append(identifier)
            numerology_claims.append(symbolic_claim(f"The {key.replace('_', ' ')} is {item.get('number')}, symbolically emphasizing {item.get('theme', 'an unresolved theme')} for the stated as-of date.", [identifier]))

    numerology_claims.append(symbolic_claim("These calculations use declared Pythagorean rules and are included as a symbolic layer, not empirical psychological evidence.", numerology_refs))

    gematria_refs: list[str] = []
    gematria_claims: list[dict[str, Any]] = []
    for index, (system, item) in enumerate(as_dict(gematria.get("systems")).items(), start=1):
        identifier = f"G{index:02d}"
        add(
            identifier,
            f"Gematria total/root: {system.replace('_', ' ').title()}",
            f"{item.get('total')} / {item.get('digital_root')}",
            f"symbolic_profile.gematria.systems.{system}",
            as_dict(gematria.get("methodology")).get(system, "Atlas cipher sequence sum"),
            evidence_kind="symbolic",
        )
        gematria_refs.append(identifier)
        gematria_claims.append(symbolic_claim(f"{system.replace('_', ' ').title()} totals {item.get('total')} and reduces to {item.get('digital_root')}, symbolically emphasizing {item.get('root_theme', 'an unresolved theme')}.", [identifier]))
    convergence = as_dict(gematria.get("cross_system"))
    if convergence:
        add("G05", "Gematria digital roots", convergence.get("digital_roots", []), "symbolic_profile.gematria.cross_system.digital_roots", "digital reduction of each cipher total", evidence_kind="symbolic")
        add("G06", "Gematria distinct-root count", convergence.get("distinct_root_count"), "symbolic_profile.gematria.cross_system.distinct_root_count", "count of unique roots across systems", evidence_kind="symbolic")
        gematria_refs.extend(["G05", "G06"])
        gematria_claims.append(symbolic_claim(f"Across {convergence.get('system_count')} systems, the totals resolve to {convergence.get('distinct_root_count')} distinct digital roots; this measures cipher convergence only.", ["G05", "G06"]))
    gematria_claims.append(symbolic_claim("Gematria totals are deterministic encodings of the recorded name; similarity or convergence does not establish identity, ability, causality, or fate.", gematria_refs))

    kamea = build_kamea_summary(resolved_summary)
    for index, planet in enumerate(kamea.get("ranked_planets", [])[:3], start=1):
        add(
            f"S{index + 1:02d}",
            f"Kamea composite: {planet['planet'].title()}",
            planet["composite_score"],
            f"profile_summary.analyses.{planet['planet']}.composite",
            "mean of driver, amplifier, and regulator scores across cipher projections",
            evidence_kind="symbolic",
        )

    hebrew = build_hebrew_summary(resolved_summary)
    if hebrew.get("analysis_count"):
        add("S05", "Hebrew-analysis count", hebrew["analysis_count"], "profile_summary.analyses[hebrew_*]", "count of Hebrew cipher projections", unit="analyses", evidence_kind="symbolic")
        add("S06", "Hebrew dominant motif", hebrew.get("dominant_motif"), "derived.hebrew.dominant_motif", "mode across Hebrew cipher projections", evidence_kind="symbolic")

    population = build_population_context(
        profile_payload,
        population_path=population_path,
        limit=5,
    )
    for metric, item in population.get("percentiles", {}).items():
        add(
            f"P{len([row for row in evidence if str(row['id']).startswith('P')]) + 1:02d}",
            f"Population percentile: {metric}",
            item.get("percentile"),
            f"population.{metric}",
            f"percentile rank among {population.get('corpus_size', 0)} compiled profiles",
            unit="percentile",
            evidence_kind="population",
        )
    if population.get("role_prevalence_percent") is not None:
        add("P08", "Role prevalence", population["role_prevalence_percent"], "population.role_prevalence_percent", "role count / corpus size", unit="percent", evidence_kind="population")

    base_refs = ["M01", "M02", "M03", "M04", "M05", "M06", "M07", "M08", "M09"]
    sections = [
        make_section(
            "executive_summary",
            "Executive Summary",
            f"{name} is classified as {subtype} in the {role} family. {classification.get('civilization_function', '')}".strip(),
            [structural_claim(str(classification.get("cognitive_style") or "Structural style unresolved."), base_refs)],
            base_refs,
            evidence,
        ),
        make_section(
            "identity_architecture",
            "Identity Architecture",
            f"The measured structure is {basis.get('topology_class', 'unresolved')}, organized around {basis.get('dominant_topology_axis', 'an unresolved axis')} with {basis.get('dominant_motif', 'no resolved')} motif dominance.",
            [structural_claim(str(classification.get("motivation") or "Motivation remains provisional."), ["M01", "M04", "M05", "M06"])],
            ["M01", "M04", "M05", "M06", "M09", "M10", "M11"],
            evidence,
        ),
        make_section(
            "psychological_architecture",
            "Psychological Architecture",
            str(classification.get("cognitive_style") or "No cognitive-style inference is available."),
            [structural_claim("This is a structural-model hypothesis, not a clinical or diagnostic assessment.", ["M03", "M04", "M05", "M09"], confidence_label="bounded")],
            ["M03", "M04", "M05", "M09", "M14", "M15"],
            evidence,
        ),
        make_section(
            "emotional_architecture",
            "Emotional Architecture",
            str(classification.get("emotional_pattern") or "Emotional pattern is unresolved."),
            [structural_claim(str(classification.get("stress_response") or "Stress response is unresolved."), ["M01", "M07", "M08"], confidence_label="provisional")],
            ["M01", "M07", "M08", "M03"],
            evidence,
        ),
        make_section(
            "cognitive_operating_system",
            "Cognitive Operating System",
            cognitive_operating_summary(role, basis),
            [structural_claim("The operating description is generated from topology, motif, density, and persistence measurements.", ["M04", "M05", "M06", "M09", "M14", "M15"])],
            ["M04", "M05", "M06", "M09", "M14", "M15"],
            evidence,
        ),
        make_section(
            "communication_style",
            "Communication Style",
            communication_summary(kamea),
            [symbolic_claim("Kamea associations are interpretive research constructs and should be tested against observed communication behavior.", [row["id"] for row in evidence if row["id"] in {"S02", "S03", "S04"}])],
            [row["id"] for row in evidence if row["id"] in {"S02", "S03", "S04"}],
            evidence,
        ),
        make_section(
            "leadership_profile",
            "Leadership Profile",
            leadership_summary(role),
            [structural_claim("Leadership fit is an environment hypothesis derived from structural role—not a measured employment outcome.", ["M01", "M02", "M04", "M05"], confidence_label="provisional")],
            ["M01", "M02", "M04", "M05", "M03"],
            evidence,
        ),
        make_section(
            "relationship_dynamics",
            "Relationship Dynamics",
            relationship_summary(classification),
            [structural_claim("Validate this hypothesis using longitudinal relationship evidence before treating it as person-specific fact.", ["M01", "M07", "M08"], confidence_label="provisional")],
            ["M01", "M07", "M08", "M03"],
            evidence,
        ),
        make_section(
            "career_resonance",
            "Career Resonance",
            career_summary(role),
            [structural_claim("These are compatible work environments, not predictions of success or employment recommendations.", ["M01", "M02", "M04", "M05"], confidence_label="bounded")],
            ["M01", "M02", "M04", "M05"],
            evidence,
        ),
        make_section(
            "numerological_integration",
            "Numerological Integration",
            numerology_summary(numerology),
            numerology_claims,
            numerology_refs,
            evidence,
        ),
        make_section(
            "gematria_synthesis",
            "Gematria Synthesis",
            gematria_summary_text(gematria),
            gematria_claims,
            gematria_refs,
            evidence,
        ),
        make_section(
            "hebrew_symbolic_layer",
            "Hebrew Symbolic Layer",
            hebrew_summary_text(hebrew),
            [symbolic_claim("The result describes deterministic cipher topology, not linguistic, religious, or clinical truth.", ["S05", "S06"] if hebrew.get("analysis_count") else [])],
            ["S05", "S06"] if hebrew.get("analysis_count") else [],
            evidence,
        ),
        make_section(
            "kamea_synthesis",
            "Kamea Synthesis",
            kamea_summary_text(kamea),
            [symbolic_claim("Planet labels identify Kamea matrices; their themes are interpretive labels attached to measured graph scores.", [row["id"] for row in evidence if row["id"] in {"S02", "S03", "S04"}])],
            [row["id"] for row in evidence if row["id"] in {"S02", "S03", "S04"}],
            evidence,
        ),
        make_section(
            "population_intelligence",
            "Population Intelligence",
            population_summary(population, role),
            [population_claim("Population comparisons describe structural similarity and rarity; they do not establish equivalent biography, ability, or outcomes.", [row["id"] for row in evidence if str(row["id"]).startswith("P")])],
            [row["id"] for row in evidence if str(row["id"]).startswith("P")],
            evidence,
        ),
        make_section(
            "shadow_atlas",
            "Shadow Atlas",
            str(classification.get("stress_response") or "No stress-response hypothesis is available."),
            [structural_claim(shadow_summary(role, population), ["M01", "M05", "M08", "P08"], confidence_label="provisional")],
            ["M01", "M05", "M08", "P08"],
            evidence,
        ),
        make_section(
            "growth_trajectory",
            "Growth Trajectory",
            str(classification.get("growth_path") or "Growth path remains unresolved."),
            [structural_claim("Growth language is a deterministic role-based hypothesis intended for reflection and longitudinal testing.", ["M01", "M02", "M05"], confidence_label="provisional")],
            ["M01", "M02", "M05"],
            evidence,
        ),
        make_section(
            "integrated_codex_summary",
            "Integrated Codex Summary",
            integrated_summary(name, role, subtype, classification, population),
            [structural_claim("The synthesis is reproducible from the cited metric registry and contains no hidden model call.", base_refs)],
            base_refs + [row["id"] for row in evidence if str(row["id"]).startswith("P")],
            evidence,
        ),
    ]

    payload = {
        "success": True,
        "schema_version": STRUCTURAL_CODEX_SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile_key": profile_key,
        "name": name,
        "title": "THE STRUCTURAL CODEX",
        "birth": birth,
        "measurement_profile": {
            "physical_astronomy": astronomy,
            "normalized_kamea_graphs": as_dict(
                profile_payload.get("kamea")
            ).get("normalized_graphs", {}),
            "structural_measurement": measurement,
            "canonical_order": [
                "physical_astronomy",
                "planet_graph",
                "normalized_kamea_graphs",
                "structural_measurement",
                "interpretation",
            ],
            "interpretation_in_measurement_layers": False,
        },
        "archetype": {
            "label": archetype_label(role),
            "structural_role": role,
            "structural_subtype": subtype,
            "confidence": confidence,
            "evidence_refs": ["M01", "M02", "M03"],
        },
        "sections": sections,
        "symbolic_profile": {
            "numerology": numerology,
            "gematria": gematria,
            "kamea": kamea,
            "hebrew_topology": hebrew,
        },
        "population_context": population,
        "evidence_registry": evidence,
        "methodology": {
            "deterministic": True,
            "measurement_precedes_interpretation": True,
            "hidden_model_calls": False,
            "claim_evidence_required": True,
            "empirical_scope": "graph, topology, temporal completeness, and population comparison",
            "symbolic_scope": "Pythagorean numerology, Atlas Gematria/cipher transforms, Hebrew topology, and Kamea interpretation",
            "limitations": [
                "This is not a clinical psychological assessment.",
                "Role-based behavioral language is hypothesis-generating and requires observed validation.",
                "Symbolic layers are labeled and must not be treated as empirical causal evidence.",
                "Population similarity does not imply equivalent identity, performance, or life outcomes.",
            ],
        },
        "errors": [],
        "warnings": warnings + population.get("warnings", []),
    }
    payload["exports"] = {"markdown": render_structural_codex_markdown(payload)}
    return payload


def build_population_context(
    profile_payload: dict[str, Any],
    *,
    population_path: str | Path,
    limit: int,
) -> dict[str, Any]:
    path = Path(population_path)
    if not path.exists():
        return {"available": False, "corpus_size": 0, "percentiles": {}, "neighbors": [], "warnings": [f"Population corpus not found: {path}"]}

    try:
        corpus = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {"available": False, "corpus_size": 0, "percentiles": {}, "neighbors": [], "warnings": [f"Population corpus could not be read: {exc}"]}

    records = [row for row in corpus.get("profiles", []) if isinstance(row, dict)]
    target = build_structural_vector(profile_payload)
    vectors = [population_record_to_vector(row) for row in records]
    metrics = ["motif_richness", "raw_density", "truth_density", "raw_nodes", "raw_edges", "truth_nodes", "truth_edges"]
    percentiles = {}
    for metric in metrics:
        values = [number(row.get(metric)) for row in vectors]
        percentiles[metric] = {
            "value": number(target.get(metric)),
            "percentile": percentile_rank(number(target.get(metric)), values),
        }

    comparable = [row for row in vectors if row.get("profile_key") != target.get("profile_key")]
    neighbors = sorted(
        (compare_vectors(target, row) for row in comparable),
        key=lambda row: row["similarity"],
        reverse=True,
    )[:limit]
    role = target.get("role")
    role_count = sum(1 for row in vectors if row.get("role") == role)
    corpus_size = len(vectors)
    return {
        "available": True,
        "source_path": str(path),
        "corpus_size": corpus_size,
        "role_count": role_count,
        "role_prevalence_percent": round(role_count / max(corpus_size, 1) * 100, 2),
        "percentiles": percentiles,
        "neighbors": neighbors,
        "metric_weights": {
            "role": 0.20,
            "subtype": 0.10,
            "topology": 0.15,
            "axis": 0.10,
            "motif": 0.05,
            "resonance": 0.05,
            "numeric": 0.35,
        },
        "warnings": [],
    }


def build_kamea_summary(summary: dict[str, Any]) -> dict[str, Any]:
    grouped: dict[str, list[float]] = defaultdict(list)
    for analysis in summary.get("analyses", []) if isinstance(summary, dict) else []:
        if not isinstance(analysis, dict):
            continue
        scores = as_dict(as_dict(analysis.get("signature")).get("scores"))
        values = [number(scores.get(key)) for key in ("driver", "amplifier", "regulator")]
        if values:
            grouped[str(analysis.get("planet") or analysis.get("kamea") or "unknown").lower()].append(mean(values))
    ranked = [
        {"planet": planet, "composite_score": round(mean(values), 6), "analysis_count": len(values)}
        for planet, values in grouped.items() if values
    ]
    ranked.sort(key=lambda row: (-row["composite_score"], row["planet"]))
    return {"ranked_planets": ranked, "method": "mean(driver, amplifier, regulator) across cipher projections"}


def build_hebrew_summary(summary: dict[str, Any]) -> dict[str, Any]:
    analyses = [
        row for row in summary.get("analyses", []) if isinstance(row, dict) and str(row.get("cipher", "")).startswith("hebrew")
    ] if isinstance(summary, dict) else []
    motifs = Counter(
        str(as_dict(as_dict(row.get("signature")).get("motifs")).get("dominant_motif") or "missing")
        for row in analyses
    )
    patterns = Counter(
        str(as_dict(as_dict(row.get("signature")).get("patterns")).get("dominant_pattern") or "missing")
        for row in analyses
    )
    return {
        "analysis_count": len(analyses),
        "dominant_motif": motifs.most_common(1)[0][0] if motifs else None,
        "dominant_pattern": patterns.most_common(1)[0][0] if patterns else None,
    }


def make_section(key: str, title: str, summary: str, claims: list[dict[str, Any]], refs: list[str], evidence: list[dict[str, Any]]) -> dict[str, Any]:
    resolved = {row["id"]: row for row in evidence}
    clean_refs = [ref for ref in dict.fromkeys(refs) if ref in resolved]
    clean_claims = []
    for claim in claims:
        clean_claim = dict(claim)
        clean_claim["evidence_refs"] = [
            ref for ref in dict.fromkeys(claim.get("evidence_refs", [])) if ref in resolved
        ]
        clean_claims.append(clean_claim)
    return {
        "key": key,
        "title": title,
        "summary": summary,
        "claims": clean_claims,
        "evidence_refs": clean_refs,
        "metrics": [resolved[ref] for ref in clean_refs],
    }


def structural_claim(text: str, refs: list[str], confidence_label: str = "model-derived") -> dict[str, Any]:
    return {"text": text, "claim_type": "structural_inference", "confidence_label": confidence_label, "evidence_refs": refs}


def symbolic_claim(text: str, refs: list[str]) -> dict[str, Any]:
    return {"text": text, "claim_type": "symbolic_interpretation", "confidence_label": "symbolic", "evidence_refs": refs}


def population_claim(text: str, refs: list[str]) -> dict[str, Any]:
    return {"text": text, "claim_type": "population_comparison", "confidence_label": "descriptive", "evidence_refs": refs}


def evidence_appender(registry: list[dict[str, Any]]):
    def add(identifier: str, label: str, value: Any, source: str, method: str, *, unit: str = "", evidence_kind: str = "structural") -> None:
        registry.append({"id": identifier, "label": label, "value": value, "unit": unit, "source": source, "method": method, "evidence_kind": evidence_kind})
    return add


def archetype_label(role: str) -> str:
    clean = role.replace("-", " ").strip()
    return f"The {clean}" if clean else "The Unresolved Structural Actor"


def cognitive_operating_summary(role: str, basis: dict[str, Any]) -> str:
    return (
        f"This model processes structure through a {basis.get('topology_class', 'unresolved')} topology, "
        f"prioritizing {basis.get('dominant_topology_axis', 'unresolved')} while organizing around "
        f"{basis.get('dominant_motif', 'unresolved')} motifs. In the classifier this resolves to {role}."
    )


def communication_summary(kamea: dict[str, Any]) -> str:
    ranked = kamea.get("ranked_planets", [])[:3]
    if not ranked:
        return "No Kamea score summary is available; communication style remains unscored."
    phrases = [f"{row['planet'].title()} ({PLANET_THEMES.get(row['planet'], 'symbolic structure')})" for row in ranked]
    return "The highest Kamea composite scores are " + ", ".join(phrases) + "."


def leadership_summary(role: str) -> str:
    if "Architect" in role or "Builder" in role:
        return "The structural model favors leadership through system design, durable standards, delegation boundaries, and long-horizon coordination rather than constant direct control."
    if "Connector" in role:
        return "The structural model favors leadership through connection, translation, coalition building, and movement of information across boundaries."
    if "Weaver" in role:
        return "The structural model favors leadership through pattern synthesis, reframing, and coordination of complex or recurring systems."
    return "Leadership style remains a provisional role-based hypothesis."


def relationship_summary(classification: dict[str, Any]) -> str:
    motivation = str(classification.get("motivation") or "Motivation unresolved.")
    stress = str(classification.get("stress_response") or "Stress response unresolved.")
    return f"{motivation} {stress}"


def career_summary(role: str) -> str:
    environments = ROLE_ENVIRONMENTS.get(role, ["research", "structured experimentation", "evidence-based decision support"])
    return f"The {role} pattern is structurally compatible with environments emphasizing " + ", ".join(environments) + "."


def numerology_summary(numerology: dict[str, Any]) -> str:
    core = as_dict(numerology.get("core_numbers"))
    if not core:
        return "Name and birth-date data are insufficient to calculate a deterministic numerology profile."
    labels = [
        ("life_path", "Life Path"),
        ("expression", "Expression"),
        ("soul_urge", "Soul Urge"),
        ("personality", "Personality"),
        ("birthday", "Birthday"),
        ("maturity", "Maturity"),
    ]
    values = [
        f"{label} {as_dict(core.get(key)).get('number')}"
        for key, label in labels
        if as_dict(core.get(key))
    ]
    pinnacles = [str(row.get("number")) for row in numerology.get("pinnacles", [])]
    challenges = [str(row.get("number")) for row in numerology.get("challenges", [])]
    cycles = as_dict(numerology.get("cycles"))
    cycle_text = ""
    if cycles:
        cycle_text = (
            f" As of {cycles.get('as_of')}, the Personal Year/Month/Day sequence is "
            f"{as_dict(cycles.get('personal_year')).get('number')}/"
            f"{as_dict(cycles.get('personal_month')).get('number')}/"
            f"{as_dict(cycles.get('personal_day')).get('number')}."
        )
    sequence_text = ""
    if pinnacles or challenges:
        sequence_text = f" Pinnacles: {'/'.join(pinnacles) or 'unavailable'}; Challenges: {'/'.join(challenges) or 'unavailable'}."
    return "The deterministic Pythagorean core is " + ", ".join(values) + "." + sequence_text + cycle_text


def gematria_summary_text(gematria: dict[str, Any]) -> str:
    systems = as_dict(gematria.get("systems"))
    if not systems:
        return "The recorded name is insufficient for Gematria calculation."
    totals = ", ".join(
        f"{system.replace('_', ' ').title()} {item.get('total')} (root {item.get('digital_root')})"
        for system, item in systems.items()
    )
    cross = as_dict(gematria.get("cross_system"))
    convergence = "exact root convergence" if cross.get("exact_root_convergence") else f"{cross.get('distinct_root_count')} distinct roots"
    return f"Atlas resolves the recorded name as {totals}; the cross-system result has {convergence}."


def hebrew_summary_text(hebrew: dict[str, Any]) -> str:
    if not hebrew.get("analysis_count"):
        return "No Hebrew cipher analyses are available."
    return f"Across {hebrew['analysis_count']} Hebrew cipher projections, the dominant measured pattern is {hebrew.get('dominant_pattern')} and the dominant motif is {hebrew.get('dominant_motif')}."


def kamea_summary_text(kamea: dict[str, Any]) -> str:
    ranked = kamea.get("ranked_planets", [])[:3]
    if not ranked:
        return "No Kamea analyses are available."
    return "The strongest composite matrix scores are " + ", ".join(f"{row['planet'].title()} ({row['composite_score']:.4f})" for row in ranked) + "."


def population_summary(population: dict[str, Any], role: str) -> str:
    if not population.get("available"):
        return "Population comparison is unavailable until the Population Intelligence corpus is built."
    neighbors = population.get("neighbors", [])
    neighbor_text = ", ".join(f"{row.get('name')} ({row.get('similarity_percent')}%)" for row in neighbors[:3]) or "none resolved"
    return (
        f"Within {population.get('corpus_size')} compiled profiles, {role} represents "
        f"{population.get('role_prevalence_percent')}% of the corpus. The closest structural neighbors are {neighbor_text}."
    )


def shadow_summary(role: str, population: dict[str, Any]) -> str:
    return f"For the {role} pattern, the primary operational risk is overextending the same mechanism that creates strength. Population percentiles should be monitored for unusually extreme density, persistence, or motif concentration."


def integrated_summary(name: str, role: str, subtype: str, classification: dict[str, Any], population: dict[str, Any]) -> str:
    return (
        f"{name} is deterministically classified as {subtype} within the {role} family. "
        f"{classification.get('civilization_function', '')} "
        f"The interpretation is grounded in graph topology, motif structure, resonance, temporal completeness, "
        f"and comparison with {population.get('corpus_size', 0)} compiled population profiles."
    ).strip()


def render_structural_codex_markdown(payload: dict[str, Any]) -> str:
    birth = as_dict(payload.get("birth"))
    measurement = as_dict(payload.get("measurement_profile"))
    astronomy = as_dict(measurement.get("physical_astronomy"))
    master = as_dict(
        as_dict(measurement.get("structural_measurement")).get("master_graph")
    )
    lines = [
        f"# {payload.get('title', 'THE STRUCTURAL CODEX')}",
        "",
        f"## {payload.get('name', '')}",
        "",
        f"**Birth:** {birth.get('date', 'unknown')} • {birth.get('time', 'unknown')} • {birth.get('place', 'unknown')}",
        "",
        "### Canonical Measurement Foundation",
        "",
        f"- Physical bodies measured: **{len(as_dict(astronomy.get('bodies')))}**",
        f"- Planet-graph edges: **{as_dict(astronomy.get('planet_graph')).get('edge_count', 0)}**",
        f"- Master graph nodes/edges: **{master.get('node_count', 0)} / {master.get('edge_count', 0)}**",
        "- IAU constellation is the canonical astronomical classification; tropical and Lahiri sidereal signs are metadata.",
        "- Interpretation is excluded from all measurement layers.",
        "",
        "### Codex Archetype",
        "",
        f"# **{as_dict(payload.get('archetype')).get('label', '')}**",
        "",
    ]
    for section in payload.get("sections", []):
        lines.extend([f"## {section.get('title')}", "", str(section.get("summary") or "")])
        refs = section.get("evidence_refs", [])
        if refs:
            lines.extend(["", f"**Metric basis:** {', '.join(f'[{ref}]' for ref in refs)}"])
        for claim in section.get("claims", []):
            lines.extend(["", f"> {claim.get('text')} ({claim.get('claim_type')}; {claim.get('confidence_label')})"])
        lines.append("")
    lines.extend(["## Evidence Registry", ""])
    for row in payload.get("evidence_registry", []):
        unit = f" {row.get('unit')}" if row.get("unit") else ""
        lines.append(f"- **[{row.get('id')}] {row.get('label')}:** `{row.get('value')}{unit}` — {row.get('method')} (`{row.get('source')}`)")
    lines.extend(["", "## Methodological Limits", ""])
    for item in as_dict(payload.get("methodology")).get("limitations", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def write_structural_codex_outputs(payload: dict[str, Any], profile_dir: str | Path) -> dict[str, str]:
    directory = Path(profile_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / "structural_codex.json"
    markdown_path = directory / "structural_codex.md"
    json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(str(as_dict(payload.get("exports")).get("markdown") or ""), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(markdown_path)}


def calculate_life_path(birth_date: str) -> int | None:
    digits = [int(char) for char in birth_date if char.isdigit()]
    if len(digits) != 8:
        return None
    value = sum(digits)
    while value not in {11, 22, 33} and value >= 10:
        value = sum(int(char) for char in str(value))
    return value


def population_record_to_vector(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "profile_key": row.get("profile_key"),
        "name": row.get("name"),
        "role": row.get("role"),
        "subtype": row.get("subtype"),
        "topology": row.get("topology_class"),
        "axis": row.get("dominant_axis"),
        "motif": row.get("dominant_motif"),
        "resonance": row.get("resonance_class", "missing"),
        "resonance_axis": row.get("dominant_resonance_axis", "missing"),
        "motif_richness": number(row.get("motif_richness")),
        "raw_nodes": integer(row.get("raw_nodes")),
        "raw_edges": integer(row.get("raw_edges")),
        "truth_nodes": integer(row.get("truth_nodes")),
        "truth_edges": integer(row.get("truth_edges")),
        "raw_density": number(row.get("raw_density")),
        "truth_density": number(row.get("truth_density")),
    }


def percentile_rank(value: float, values: Iterable[float]) -> float:
    ordered = sorted(number(item) for item in values)
    if not ordered:
        return 0.0
    below = sum(1 for item in ordered if item < value)
    equal = sum(1 for item in ordered if item == value)
    return round((below + 0.5 * equal) / len(ordered) * 100, 2)


def density(edges: Any, nodes: Any) -> float:
    return round(number(edges) / max(number(nodes), 1.0), 6)


def number(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def integer(value: Any) -> int:
    return int(number(value))


def as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def read_optional_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def failure_payload(profile_key: str, errors: Iterable[Any]) -> dict[str, Any]:
    return {
        "success": False,
        "schema_version": STRUCTURAL_CODEX_SCHEMA_VERSION,
        "profile_key": profile_key,
        "errors": [str(item) for item in errors] or ["Canonical profile compilation failed."],
        "warnings": [],
        "sections": [],
        "evidence_registry": [],
        "exports": {},
    }
