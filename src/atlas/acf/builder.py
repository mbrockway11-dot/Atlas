"""Atlas Codex Format builder."""

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from atlas.birth import BirthData, birth_data_to_dict
from atlas.classification import (
    classification_to_dict,
    classify_signature,
    get_expression_meaning,
    get_functional_role_meaning,
    get_structural_state_meaning,
)
from atlas.essence.builder import build_essence_graph
from atlas.export.json import graph_to_dict, signature_to_dict, write_json
from atlas.identity import build_identity_graph, build_identity_persistence
from atlas.interpretation.profile import (
    interpret_profile_summary,
    profile_interpretation_to_dict,
)
from atlas.invariant.pipeline import run_invariant_pipeline
from atlas.profiles.summary import build_individual_profile_summary
from atlas.signatures.fingerprint import build_topology_signature


ATLAS_CODEX_FORMAT_VERSION = "1.0"


def build_acf_profile(
    name: str,
    entity_type: str = "person",
    birth_data: BirthData | None = None,
) -> dict[str, Any]:
    """Build one Atlas Codex Format profile."""
    summary = build_individual_profile_summary(name)
    interpretation = interpret_profile_summary(summary)

    essence_graph = build_essence_graph(name)
    essence_signature = build_topology_signature(essence_graph)
    essence_classification = classify_signature(
        essence_signature,
        scale="Individual",
    )
    essence_classification_dict = classification_to_dict(essence_classification)

    invariant_analysis = run_invariant_pipeline(name)
    identity_graph = build_identity_graph(name)
    identity_persistence = build_identity_persistence(identity_graph)

    return {
        "metadata": {
            "atlas_codex_format": ATLAS_CODEX_FORMAT_VERSION,
            "created_utc": datetime.now(timezone.utc).isoformat(),
            "entity_type": entity_type,
            "entity_name": name,
            "analysis_count": summary["analysis_count"],
            "deterministic": True,
        },
        "identity": {
            "name": name,
            "entity_type": entity_type,
            "birth_data": birth_data_to_dict(birth_data),
        },
        "profile_interpretation": profile_interpretation_to_dict(interpretation),
        "essence": {
            "graph_summary": graph_to_dict(essence_graph)["summary"],
            "signature": signature_to_dict(essence_signature),
            "classification": add_classification_meanings(
                essence_classification_dict
            ),
            "graph": graph_to_dict(essence_graph),
        },
        "invariant_analysis": invariant_analysis,
        "identity_graph": identity_graph,
        "identity_persistence": identity_persistence,
        "planetary_matrix": build_planetary_matrix(summary),
        "cipher_matrix": build_cipher_matrix(summary),
        "analyses": summary["analyses"],
        "interpretation_seed": build_interpretation_seed(summary, interpretation),
    }


def export_acf_profile(
    name: str,
    output_path: str | Path,
    entity_type: str = "person",
    birth_data: BirthData | None = None,
) -> Path:
    """Build and export one Atlas Codex Format profile."""
    acf = build_acf_profile(
        name=name,
        entity_type=entity_type,
        birth_data=birth_data,
    )

    return write_json(acf, output_path)


def add_classification_meanings(
    classification: dict[str, Any],
) -> dict[str, Any]:
    """Attach official meaning dictionaries to classification output."""
    role = classification["function"]["role"]
    expression = classification["expression"]["type"]
    state = classification["state"]["type"]

    classification["meanings"] = {
        "function": get_functional_role_meaning(role),
        "expression": get_expression_meaning(expression),
        "state": get_structural_state_meaning(state),
    }

    return classification


def build_planetary_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    """Aggregate profile metrics by planet."""
    matrix = {}

    for analysis in summary["analyses"]:
        planet = analysis["planet"]
        matrix.setdefault(planet, [])
        matrix[planet].append(_analysis_metrics(analysis))

    return {
        planet: _average_metric_rows(rows)
        for planet, rows in matrix.items()
    }


def build_cipher_matrix(summary: dict[str, Any]) -> dict[str, Any]:
    """Aggregate profile metrics by cipher."""
    matrix = {}

    for analysis in summary["analyses"]:
        cipher = analysis["cipher"]
        matrix.setdefault(cipher, [])
        matrix[cipher].append(_analysis_metrics(analysis))

    return {
        cipher: _average_metric_rows(rows)
        for cipher, rows in matrix.items()
    }


def build_interpretation_seed(
    summary: dict[str, Any],
    interpretation: Any,
) -> dict[str, Any]:
    """Build deterministic fact seed for language-model interpretation."""
    facts = list(interpretation.summary_lines)

    strongest_driver = interpretation.strongest_driver
    strongest_amplifier = interpretation.strongest_amplifier
    strongest_regulator = interpretation.strongest_regulator

    facts.append(
        "Strongest driver occurs in "
        f"{strongest_driver['planet']} / {strongest_driver['cipher']}."
    )
    facts.append(
        "Strongest amplifier occurs in "
        f"{strongest_amplifier['planet']} / {strongest_amplifier['cipher']}."
    )
    facts.append(
        "Strongest regulator occurs in "
        f"{strongest_regulator['planet']} / {strongest_regulator['cipher']}."
    )

    return {
        "facts": facts,
        "instructions": [
            "Treat Atlas outputs as deterministic measurements.",
            "Do not recalculate the metrics.",
            "Distinguish direct observations from interpretation.",
            "Do not infer claims unsupported by the supplied topology data.",
        ],
    }


def _analysis_metrics(analysis: dict[str, Any]) -> dict[str, float]:
    """Extract numeric metrics from one analysis."""
    signature = analysis["signature"]

    return {
        "driver": signature["scores"]["driver"],
        "amplifier": signature["scores"]["amplifier"],
        "regulator": signature["scores"]["regulator"],
        "edge_density": signature["metrics"]["edge_density"],
        "symmetry": signature["metrics"]["symmetry"],
        "entropy": signature["metrics"]["entropy"],
        "node_count": signature["metrics"]["node_count"],
        "edge_count": signature["metrics"]["edge_count"],
        "motif_density": signature["motifs"]["motif_density"],
    }


def _average_metric_rows(rows: list[dict[str, float]]) -> dict[str, float]:
    """Average numeric metric rows."""
    if not rows:
        return {}

    keys = rows[0].keys()

    return {
        key: sum(row[key] for row in rows) / len(rows)
        for key in keys
    }