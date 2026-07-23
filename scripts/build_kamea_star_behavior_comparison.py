"""Build an evidence-bounded Kamea, Vedic, constellation, and event comparison."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from statistics import mean
from typing import Any

from atlas.core.compiler import compile_profile
from atlas.services.vedic_behavior_service import build_vedic_behavior_payload
from atlas.temporal.constellations import build_astronomical_constellation_chart
from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KAMEA_DIR = PROJECT_ROOT / "output" / "kamea_consciousness_flow"
DEFAULT_HISTORY_DIR = PROJECT_ROOT / "output" / "historical_validation" / "edison_tesla_v1"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output" / "kamea_star_behavior"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile_a")
    parser.add_argument("profile_b")
    parser.add_argument("--kamea-dir", type=Path, default=DEFAULT_KAMEA_DIR)
    parser.add_argument("--history-dir", type=Path, default=DEFAULT_HISTORY_DIR)
    parser.add_argument(
        "--symbolic-only",
        action="store_true",
        help="Run without historical events or outcome claims for this pair.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument(
        "--update-profile-summaries",
        action="store_true",
        help="Merge the bounded dynamics extension into both profile summaries.",
    )
    args = parser.parse_args()

    report = build_comparison(
        args.profile_a,
        args.profile_b,
        kamea_dir=args.kamea_dir,
        history_dir=None if args.symbolic_only else args.history_dir,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stem = f"{args.profile_a}__{args.profile_b}"
    json_path = args.output_dir / f"{stem}.json"
    markdown_path = args.output_dir / f"{stem}.md"
    json_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    markdown_path.write_text(render_markdown(report), encoding="utf-8")
    if args.update_profile_summaries:
        update_profile_summaries(report)
    print(json.dumps({
        "success": report["success"],
        "json": str(json_path),
        "markdown": str(markdown_path),
        "strongest_shape_confluence": report["comparison"]["strongest_shape_confluence_planet"],
        "retained_historical_findings": report["methodology"]["retained_historical_findings"],
        "profile_summaries_updated": args.update_profile_summaries,
    }, indent=2))


def build_comparison(
    profile_a: str,
    profile_b: str,
    *,
    kamea_dir: Path = DEFAULT_KAMEA_DIR,
    history_dir: Path | None = DEFAULT_HISTORY_DIR,
) -> dict[str, Any]:
    kamea_a = read_json(kamea_dir / profile_a / "kamea_consciousness_flow.json")
    kamea_b = read_json(kamea_dir / profile_b / "kamea_consciousness_flow.json")
    confluence_path = kamea_dir / f"{profile_a}__{profile_b}_confluence.json"
    if not confluence_path.exists():
        confluence_path = kamea_dir / f"{profile_b}__{profile_a}_confluence.json"
    confluence = read_json(confluence_path)

    if history_dir is None:
        events: dict[str, dict[str, str]] = {}
        participation: list[dict[str, str]] = []
        missing: dict[str, dict[str, str]] = {}
        validation: dict[str, Any] = {}
    else:
        events = rows_by_key(read_csv(history_dir / "historical_event_registry.csv"), "event_id")
        participation = read_csv(history_dir / "profile_event_participation.csv")
        missing = rows_by_key(read_csv(history_dir / "missing_data_report.csv"), "record_id")
        validation = read_json(history_dir / "historical_validation_summary.json")

    profiles = {
        profile_a: build_profile_record(profile_a, kamea_a, participation, events, missing),
        profile_b: build_profile_record(profile_b, kamea_b, participation, events, missing),
    }
    shape = confluence.get("shape_confluence", {})

    comparison = {
        "shape_confluence": shape.get("planetary_shape_comparisons", []),
        "mean_consensus_shape_jaccard": shape.get("mean_consensus_shape_jaccard", 0),
        "mean_directional_shape_jaccard": shape.get("mean_directional_shape_jaccard", 0),
        "strongest_shape_confluence_planet": shape.get(
            "strongest_shape_confluence_planet", ""
        ),
        "highest_internal_curve_consistency": max(
            profiles,
            key=lambda key: profiles[key]["shape"]["mean_within_planet_curve_similarity"],
        ),
        "highest_mean_displacement": max(
            profiles,
            key=lambda key: profiles[key]["shape"]["mean_displacement"],
        ),
        "lowest_mean_tortuosity": min(
            profiles,
            key=lambda key: profiles[key]["shape"]["mean_tortuosity"],
        ),
    }
    dynamics = build_dynamic_hypotheses(
        profiles,
        comparison,
        historical_context_available=bool(validation),
    )

    return {
        "success": True,
        "version": "atlas.kamea-star-behavior-comparison.v1",
        "profiles": profiles,
        "comparison": comparison,
        "dynamics_experiment": dynamics,
        "methodology": {
            "vedic_coordinate_system": "12 equal signs; Lahiri sidereal ayanamsha",
            "constellation_coordinate_system": (
                "unequal IAU Delporte sky boundaries; Roman 1987/B1875 lookup"
            ),
            "ophiuchus_policy": (
                "included in the separate 13-constellation ecliptic-path layer; "
                "not inserted into Jyotish signs, nakshatras, houses, yogas, or dashas"
            ),
            "historical_transit_coordinate_note": (
                "The pilot tests pairwise angular aspects. A shared sidereal offset "
                "does not change angular separation, so the tropical calculation is "
                "aspect-invariant. IAU constellations are not transit aspects."
            ),
            "retained_historical_findings": validation.get("quality", {}).get(
                "retained_findings", 0
            ),
            "historical_context_available": bool(validation),
            "causal_claim": False,
            "interpretation_status": "hypothesis_generating_only",
        },
    }


def build_profile_record(
    profile_key: str,
    kamea: dict[str, Any],
    participation: list[dict[str, str]],
    events: dict[str, dict[str, str]],
    missing: dict[str, dict[str, str]],
) -> dict[str, Any]:
    css = compile_profile(profile_key).to_dict()
    ephemeris = css.get("temporal", {}).get("natal", {}).get("ephemeris", {})
    sidereal = ephemeris.get("sidereal", {})
    constellations = ephemeris.get("astronomical_constellations", {})
    vedic = build_vedic_behavior_payload(profile_key)
    shape = kamea.get("shape", {})
    features = [row.get("shape_features", {}) for row in shape.get("streams", [])]

    profile_events = []
    for row in participation:
        if row.get("profile_key") != profile_key:
            continue
        event = events.get(row.get("event_id", ""), {})
        profile_events.append({
            "date": event.get("start_date", ""),
            "event_id": row.get("event_id", ""),
            "event": event.get("name", ""),
            "role": row.get("participation_role", ""),
            "outcome_category": row.get("outcome_category", ""),
            "outcome_direction": row.get("outcome_direction", ""),
            "documented_outcome": row.get("documented_outcome", ""),
            "involvement_confidence": row.get("involvement_confidence", ""),
            "source_citations": parse_json_cell(row.get("source_citations", "[]")),
        })

    constellation_rows = constellations.get("planets", {})
    return {
        "profile_key": profile_key,
        "shape": {
            **shape.get("summary", {}),
            "mean_path_length": feature_mean(features, "path_length"),
            "mean_displacement": feature_mean(features, "displacement"),
            "mean_tortuosity": feature_mean(features, "tortuosity"),
            "mean_self_intersections": feature_mean(features, "self_intersections"),
            "planetary_fields": shape.get("planetary_fields", []),
        },
        "vedic": {
            "zodiac": sidereal.get("zodiac", ""),
            "ayanamsa": sidereal.get("ayanamsa", ""),
            "ayanamsa_degrees": sidereal.get("ayanamsa_degrees"),
            "planets": sidereal.get("planets", {}),
            "moon_nakshatra": vedic.get("metrics", {}).get("moon_nakshatra", ""),
            "coordinate_system": vedic.get("data", {}).get("behavior", {}).get(
                "coordinate_system", {}
            ),
        },
        "astronomical_constellations": {
            "definition": constellations.get("definition", ""),
            "boundary_system": constellations.get("boundary_system", ""),
            "planets": constellation_rows,
            "ophiuchus_planets": [
                planet for planet, row in constellation_rows.items()
                if row.get("is_ophiuchus")
            ],
        },
        "birth_time_quality": missing.get(profile_key, {}),
        "birth_time_constellation_sensitivity": build_birth_time_sensitivity(
            profile_key, ephemeris
        ),
        "documented_events": profile_events,
        "event_dynamics": summarize_event_dynamics(profile_events),
    }


def build_birth_time_sensitivity(
    profile_key: str,
    ephemeris: dict[str, Any],
) -> dict[str, Any]:
    """Recompute Moon constellations at bounded UT proxy times."""
    birth = ephemeris.get("birth", {})
    birth_date = str(birth.get("birth_date") or birth.get("date") or "")
    if not birth_date:
        return {"success": False, "errors": ["birth date unavailable"]}

    observations = []
    for time_value in ("00:00", "12:00", "23:59"):
        result = build_ephemeris(BirthData(
            name=profile_key,
            birth_date=birth_date,
            birth_time=time_value,
            birth_place=str(birth.get("birth_place") or birth.get("place") or ""),
            time_known=False,
        ))
        moon = build_astronomical_constellation_chart(result)["planets"]["Moon"]
        observations.append({
            "time": time_value,
            "actual_constellation": moon["actual_constellation"],
            "ecliptic_path_constellation": moon["ecliptic_path_constellation"],
            "tropical_longitude": moon["tropical_longitude"],
        })

    actual = {row["actual_constellation"] for row in observations}
    projected = {row["ecliptic_path_constellation"] for row in observations}
    return {
        "success": True,
        "time_policy": "00:00/12:00/23:59 UT proxy bounds; local timezone unresolved",
        "observations": observations,
        "actual_constellation_stable": len(actual) == 1,
        "ecliptic_path_constellation_stable": len(projected) == 1,
        "stable_actual_constellation": next(iter(actual)) if len(actual) == 1 else None,
        "stable_ecliptic_path_constellation": (
            next(iter(projected)) if len(projected) == 1 else None
        ),
        "moon_longitude_span_degrees": round(
            circular_span_degrees(
                [row["tropical_longitude"] for row in observations]
            ),
            6,
        ),
        "claim_type": "birth_time_sensitivity_analysis",
        "causal_claim": False,
    }


def summarize_event_dynamics(events: list[dict[str, Any]]) -> dict[str, Any]:
    """Summarize observed event sequences without assigning personality labels."""
    category_counts: dict[str, int] = {}
    direction_counts: dict[str, int] = {}
    for event in events:
        category = str(event.get("outcome_category") or "unknown")
        direction = str(event.get("outcome_direction") or "unknown")
        category_counts[category] = category_counts.get(category, 0) + 1
        direction_counts[direction] = direction_counts.get(direction, 0) + 1
    return {
        "event_count": len(events),
        "outcome_category_counts": category_counts,
        "outcome_direction_counts": direction_counts,
        "role_sequence": [event.get("role", "") for event in events],
        "claim_type": "documented_event_summary",
        "causal_claim": False,
    }


def build_dynamic_hypotheses(
    profiles: dict[str, dict[str, Any]],
    comparison: dict[str, Any],
    *,
    historical_context_available: bool = True,
) -> dict[str, Any]:
    """Build explicit case-study hypotheses with disconfirmation requirements."""
    keys = list(profiles)
    first, second = keys[0], keys[1]
    p1, p2 = profiles[first], profiles[second]
    spatial = float(comparison.get("mean_consensus_shape_jaccard", 0))
    directional = float(comparison.get("mean_directional_shape_jaccard", 0))

    divergences = {
        key: [
            planet
            for planet, row in profile["astronomical_constellations"]["planets"].items()
            if row.get("actual_constellation")
            != row.get("ecliptic_path_constellation")
        ]
        for key, profile in profiles.items()
    }
    ophiuchus = {
        key: {
            "central_chart": profile["astronomical_constellations"]["ophiuchus_planets"],
            "moon_time_sensitivity": profile["birth_time_constellation_sensitivity"],
        }
        for key, profile in profiles.items()
    }

    hypotheses = [
        {
            "hypothesis_id": "DYN_SHARED_FIELD_DIVERGENT_ROUTE",
            "statement": (
                "Relationship pairs may occupy overlapping normalized Kamea regions "
                "while traversing those regions in different directions."
            ),
            "observed_support": {
                "mean_consensus_shape_jaccard": spatial,
                "mean_directional_shape_jaccard": directional,
                "directional_to_spatial_ratio": round(directional / spatial, 6)
                if spatial else None,
            },
            "status": "descriptive_single_pair",
            "falsification_test": (
                "Preregister the same metrics across independent relationship pairs; "
                "reject if directional overlap is not systematically lower than spatial overlap."
            ),
        },
    ]
    if historical_context_available:
        hypotheses.extend([
        {
            "hypothesis_id": "DYN_ROUTE_STABILITY_AND_RESPONSE_SEQUENCE",
            "statement": (
                "Higher cross-cipher curve consistency and net displacement may align "
                "with maintaining a technical direction across institutional separation."
            ),
            "observed_support": {
                first: {
                    "curve_similarity": p1["shape"]["mean_within_planet_curve_similarity"],
                    "mean_displacement": p1["shape"]["mean_displacement"],
                    "mean_tortuosity": p1["shape"]["mean_tortuosity"],
                    "event_roles": p1["event_dynamics"]["role_sequence"],
                },
                second: {
                    "curve_similarity": p2["shape"]["mean_within_planet_curve_similarity"],
                    "mean_displacement": p2["shape"]["mean_displacement"],
                    "mean_tortuosity": p2["shape"]["mean_tortuosity"],
                    "event_roles": p2["event_dynamics"]["role_sequence"],
                },
            },
            "status": "post_hoc_case_alignment_not_validated",
            "falsification_test": (
                "Blind-code organizational exit, strategy continuation, and institutional "
                "adaptation for a larger cohort before exposing Kamea metrics."
            ),
        },
        {
            "hypothesis_id": "DYN_INFRASTRUCTURE_SATURN_JUPITER",
            "statement": (
                "Infrastructure competitors may show internal Saturn coherence with "
                "cross-person Jupiter spatial confluence."
            ),
            "observed_support": {
                "strongest_cross_profile_shape_planet": comparison.get(
                    "strongest_shape_confluence_planet"
                ),
                "internal_consensus_planets": {
                    key: profile["shape"].get("strongest_shape_consensus_planet")
                    for key, profile in profiles.items()
                },
            },
            "status": "single_pair_symbolic_hypothesis",
            "falsification_test": (
                "Compare preregistered infrastructure, artistic, political, and random "
                "relationship cohorts with matched name-length controls."
            ),
        },
        ])
    hypotheses.extend([
        {
            "hypothesis_id": "DYN_ACTUAL_VS_ECLIPTIC_DIVERGENCE",
            "statement": (
                "Actual-sky constellation divergence from the zero-latitude ecliptic "
                "projection may provide a distinct feature from equal-sign placement."
            ),
            "observed_support": divergences,
            "status": "feature_discovery_unlinked_to_behavior",
            "falsification_test": (
                "Test divergence as its own astronomical feature; do not infer behavior "
                "until a blinded registry contains enough divergent and non-divergent cases."
            ),
        },
        {
            "hypothesis_id": "DYN_OPHIUCHUS_MOON_SENSITIVITY",
            "statement": (
                "Ophiuchus Moon classifications in historical profiles must be tested "
                "across the full birth-time uncertainty interval before interpretation."
            ),
            "observed_support": ophiuchus,
            "status": "astronomical_time_sensitivity_check",
            "falsification_test": (
                "Recompute the Moon at 00:00, 12:00, and 23:59 local-time bounds; "
                "discard the categorical feature if the constellation changes."
            ),
        },
    ])
    return {
        "version": "atlas.symbolic-dynamics.case-study.v1",
        "profile_count": len(profiles),
        "hypothesis_count": len(hypotheses),
        "hypotheses": hypotheses,
        "retained_findings": 0,
        "research_only": True,
        "causal_claim": False,
    }


def update_profile_summaries(report: dict[str, Any]) -> None:
    """Merge a reproducible extension into summary, interpretation, and report files."""
    dynamics = report["dynamics_experiment"]
    profile_keys = list(report["profiles"])
    for profile_key, profile in report["profiles"].items():
        profile_dir = PROJECT_ROOT / "output" / "library" / "profiles" / profile_key
        extension = {
            "version": dynamics["version"],
            "profile_key": profile_key,
            "comparison_profiles": [key for key in profile_keys if key != profile_key],
            "shape": {
                key: profile["shape"].get(key)
                for key in [
                    "mean_within_planet_curve_similarity",
                    "mean_shape_consensus_ratio",
                    "mean_path_length",
                    "mean_displacement",
                    "mean_tortuosity",
                    "strongest_shape_consensus_planet",
                ]
            },
            "vedic": profile["vedic"],
            "astronomical_constellations": profile["astronomical_constellations"],
            "birth_time_constellation_sensitivity": profile[
                "birth_time_constellation_sensitivity"
            ],
            "event_dynamics": profile["event_dynamics"],
            "hypotheses": dynamics["hypotheses"],
            "retained_findings": 0,
            "research_only": True,
            "causal_claim": False,
        }
        merge_json_extension(profile_dir / "profile_summary.json", extension)
        merge_json_extension(profile_dir / "profile_interpretation.json", extension)
        update_codex_report(profile_dir / "codex_report.md", extension)


def merge_json_extension(path: Path, extension: dict[str, Any]) -> None:
    payload = read_json(path) if path.exists() else {}
    payload["symbolic_dynamics"] = extension
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_codex_report(path: Path, extension: dict[str, Any]) -> None:
    start = "<!-- ATLAS_SYMBOLIC_DYNAMICS_START -->"
    end = "<!-- ATLAS_SYMBOLIC_DYNAMICS_END -->"
    existing = path.read_text(encoding="utf-8") if path.exists() else ""
    if start in existing and end in existing:
        prefix = existing.split(start, 1)[0].rstrip()
        suffix = existing.split(end, 1)[1].lstrip()
        existing = prefix + ("\n\n" + suffix if suffix else "")

    lines = [
        start,
        "## Symbolic Dynamics Experiment",
        "",
        "> Research-only case study. No causal or validated behavioral claim.",
        "",
        f"- Mean curve similarity: **{extension['shape']['mean_within_planet_curve_similarity']:.6f}**",
        f"- Mean shape consensus: **{extension['shape']['mean_shape_consensus_ratio']:.6f}**",
        f"- Mean displacement: **{extension['shape']['mean_displacement']:.6f}**",
        f"- Mean tortuosity: **{extension['shape']['mean_tortuosity']:.6f}**",
        f"- Strongest shape-consensus planet: **{extension['shape']['strongest_shape_consensus_planet']}**",
        f"- Lahiri Moon nakshatra: **{extension['vedic']['moon_nakshatra']}**",
        f"- Central-time Ophiuchus placements: **{', '.join(extension['astronomical_constellations']['ophiuchus_planets']) or 'none'}**",
        f"- Moon constellation stable across time bounds: **{extension['birth_time_constellation_sensitivity'].get('actual_constellation_stable', False)}**",
        f"- Dynamic hypotheses registered: **{len(extension['hypotheses'])}**",
        f"- Retained findings: **{extension['retained_findings']}**",
        "",
        "See `output/kamea_star_behavior` for measured evidence, event sequences, and falsification requirements.",
        end,
    ]
    combined = existing.rstrip() + "\n\n" + "\n".join(lines) + "\n"
    path.write_text(combined, encoding="utf-8")


def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Kamea, Vedic, Astronomical Constellation, and Behavior Comparison",
        "",
        "> This report separates measured geometry, astronomical coordinates, documented history, and symbolic hypotheses. It makes no causal claim.",
        "",
    ]
    for key, profile in report["profiles"].items():
        shape = profile["shape"]
        lines.extend([
            f"## {key.replace('_', ' ').title()}",
            "",
            "### Normalized Kamea geometry",
            "",
            f"- Mean within-planet curve similarity: **{shape.get('mean_within_planet_curve_similarity', 0):.6f}**",
            f"- Mean shape consensus: **{shape.get('mean_shape_consensus_ratio', 0):.6f}**",
            f"- Mean path length: **{shape.get('mean_path_length', 0):.6f}**",
            f"- Mean displacement: **{shape.get('mean_displacement', 0):.6f}**",
            f"- Mean tortuosity: **{shape.get('mean_tortuosity', 0):.6f}**",
            f"- Strongest consensus planet: **{shape.get('strongest_shape_consensus_planet', '')}**",
            "",
            "### Lahiri sidereal placements",
            "",
            "| Planet | Sidereal sign | Longitude |",
            "|---|---|---:|",
        ])
        for planet, row in profile["vedic"]["planets"].items():
            lines.append(f"| {planet} | {row.get('sign', '')} | {row.get('longitude', 0):.6f} |")
        lines.extend([
            "",
            f"Moon nakshatra: **{profile['vedic']['moon_nakshatra']}**",
            "",
            "### IAU astronomical constellations",
            "",
            "| Planet | Actual sky | Ecliptic-path projection |",
            "|---|---|---|",
        ])
        for planet, row in profile["astronomical_constellations"]["planets"].items():
            lines.append(
                f"| {planet} | {row.get('actual_constellation', '')} | "
                f"{row.get('ecliptic_path_constellation', '')} |"
            )
        ophiuchus = profile["astronomical_constellations"]["ophiuchus_planets"]
        sensitivity = profile["birth_time_constellation_sensitivity"]
        lines.extend([
            "",
            f"Ophiuchus placements: **{', '.join(ophiuchus) if ophiuchus else 'none'}**",
            f"Moon constellation stable across UT proxy bounds: **{sensitivity.get('actual_constellation_stable', False)}**",
            f"Moon longitude span across bounds: **{sensitivity.get('moon_longitude_span_degrees', 0):.6f} degrees**",
            "",
            "### Documented situations",
            "",
        ])
        for event in profile["documented_events"]:
            lines.append(
                f"- **{event['date']} - {event['event']}**: "
                f"{event['documented_outcome']} ({event['involvement_confidence']} confidence)"
            )
        lines.append("")

    comparison = report["comparison"]
    methodology = report["methodology"]
    lines.extend([
        "## Comparison findings",
        "",
        f"- Strongest normalized cross-profile shape confluence: **{comparison['strongest_shape_confluence_planet']}**",
        f"- Higher internal curve consistency: **{comparison['highest_internal_curve_consistency']}**",
        f"- Higher net displacement: **{comparison['highest_mean_displacement']}**",
        f"- Lower tortuosity: **{comparison['lowest_mean_tortuosity']}**",
        f"- Mean consensus-shape Jaccard: **{comparison['mean_consensus_shape_jaccard']:.6f}**",
        f"- Mean directional-shape Jaccard: **{comparison['mean_directional_shape_jaccard']:.6f}**",
        "",
        "## Methodological limits",
        "",
        f"- Ophiuchus policy: {methodology['ophiuchus_policy']}.",
        f"- {methodology['historical_transit_coordinate_note']}",
        f"- Retained historical findings: **{methodology['retained_historical_findings']}**.",
        "- Unknown/estimated birth times disable houses and angles and make Moon timing sensitive.",
        "- Symbolic correspondences are hypotheses requiring population-level replication.",
        "",
    ])
    return "\n".join(lines)


def feature_mean(features: list[dict[str, Any]], key: str) -> float:
    values = [float(row[key]) for row in features if row.get(key) is not None]
    return round(mean(values), 6) if values else 0.0


def circular_span_degrees(values: list[float]) -> float:
    """Return the smallest arc containing all longitudes on a 360-degree circle."""
    if len(values) < 2:
        return 0.0
    ordered = sorted(float(value) % 360.0 for value in values)
    gaps = [
        ordered[index + 1] - ordered[index]
        for index in range(len(ordered) - 1)
    ]
    gaps.append((ordered[0] + 360.0) - ordered[-1])
    return 360.0 - max(gaps)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def rows_by_key(rows: list[dict[str, str]], key: str) -> dict[str, dict[str, str]]:
    return {row.get(key, ""): row for row in rows}


def parse_json_cell(value: str) -> Any:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return value


if __name__ == "__main__":
    main()
