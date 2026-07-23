"""Build corrected Kamea consciousness-flow and invariant-riverbed reports."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from atlas.kamea_flow.report import build_kamea_flow_report
from atlas.kamea_flow.confluence import build_riverbed_confluence
from atlas.services.profile_path_service import PROJECT_ROOT
from atlas.visualization.kamea_riverbed import export_planetary_riverbed_svg
from atlas.visualization.kamea_unified_shape import export_unified_kamea_shape_svg


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("profiles", nargs="*", default=["nikola_tesla", "thomas_edison"])
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "output" / "kamea_consciousness_flow")
    args = parser.parse_args()
    built = [build_profile(profile_key, args.output_dir) for profile_key in args.profiles]
    summaries = [item["summary"] for item in built]
    confluence = None
    if len(built) == 2:
        confluence = build_riverbed_confluence(args.profiles[0], built[0]["report"], args.profiles[1], built[1]["report"])
        stem = f"{args.profiles[0]}__{args.profiles[1]}_confluence"
        confluence_path = Path(args.output_dir) / f"{stem}.json"
        confluence_path.write_text(json.dumps(confluence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (Path(args.output_dir) / f"{stem}.md").write_text(render_confluence_markdown(confluence), encoding="utf-8")
    print(json.dumps({"success": True, "profiles": summaries, "confluence": confluence["summary"] if confluence else None}, indent=2))


def build_profile(profile_key: str, output_root: Path) -> dict[str, Any]:
    payload_path = PROJECT_ROOT / "output" / "library" / "profiles" / profile_key / "profile.payload.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    report = build_kamea_flow_report(payload)
    profile_dir = Path(output_root) / profile_key
    profile_dir.mkdir(parents=True, exist_ok=True)
    report_path = profile_dir / "kamea_consciousness_flow.json"
    report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    svg_paths = []
    for riverbed in report["riverbed"]["planetary_riverbeds"]:
        path = export_planetary_riverbed_svg(riverbed, profile_dir / f"{riverbed['planet']}_invariant_riverbed.svg")
        svg_paths.append(str(path))
    unified_path = export_unified_kamea_shape_svg(
        report["shape"],
        profile_dir / "unified_kamea_shape.svg",
        title=f"{profile_key.replace('_', ' ').title()} — Unified Kamea Shape",
    )
    svg_paths.append(str(unified_path))
    markdown_path = profile_dir / "kamea_consciousness_flow.md"
    markdown_path.write_text(render_markdown(profile_key, report), encoding="utf-8")
    summary = {
        "profile_key": profile_key,
        "step_count": report["flow"]["step_count"],
        "tributary_count": report["tributaries"]["tributary_count"],
        "invariant_nodes": report["riverbed"]["summary"]["invariant_node_count"],
        "invariant_edges": report["riverbed"]["summary"]["invariant_edge_count"],
        "report": str(report_path),
        "markdown": str(markdown_path),
        "svg_count": len(svg_paths),
        "unified_shape": str(unified_path),
    }
    return {"summary": summary, "report": report}


def render_markdown(profile_key: str, report: dict[str, Any]) -> str:
    flow = report["flow"]
    metrics = report["metrics"]["metrics"]
    riverbed = report["riverbed"]
    lines = [
        f"# Kamea Consciousness Flow — {profile_key.replace('_', ' ').title()}",
        "",
        "> Deterministic symbolic structure; not an empirical measurement of consciousness or causality.",
        "",
        f"- Full traversal steps: **{flow['step_count']}**",
        f"- Independent tributaries: **{report['tributaries']['tributary_count']}**",
        f"- Directed channels: **{flow['edge_count']}**",
        f"- Flow entropy: **{metrics['flow_entropy']}**",
        f"- Recurrence: **{metrics['recurrence_ratio']}**",
        f"- Directional coherence: **{metrics['directional_coherence']}**",
        f"- Invariant riverbed nodes: **{riverbed['summary']['invariant_node_count']}**",
        f"- Invariant riverbed channels: **{riverbed['summary']['invariant_edge_count']}**",
        f"- Mean geometric shape consensus: **{report['shape']['summary']['mean_shape_consensus_ratio']}**",
        "",
        "## Unified Geometric Shape",
        "",
        "![Unified normalized Kamea shape](unified_kamea_shape.svg)",
        "",
        "## Planetary Riverbeds",
        "",
    ]
    for row in riverbed["planetary_riverbeds"]:
        lines.extend([
            f"### {row['planet'].title()}",
            "",
            f"![{row['planet'].title()} invariant riverbed]({row['planet']}_invariant_riverbed.svg)",
            "",
            f"Streams: {row['stream_count']} · invariant nodes: {row['invariant_node_count']} · invariant channels: {row['invariant_edge_count']} · node consensus: {row['node_consensus_ratio']} · edge consensus: {row['edge_consensus_ratio']}",
            "",
        ])
    return "\n".join(lines) + "\n"


def render_confluence_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        f"# Kamea Riverbed Confluence — {report['profile_a']} × {report['profile_b']}",
        "",
        "> Deterministic symbolic comparison; not evidence of consciousness, causality, or relationship destiny.",
        "",
        f"- Shared invariant nodes: **{summary['shared_invariant_node_count']}**",
        f"- Shared invariant channels: **{summary['shared_invariant_edge_count']}**",
        f"- Opposing currents: **{summary['opposing_current_count']}**",
        f"- Mean node Jaccard: **{summary['mean_node_jaccard']}**",
        f"- Mean edge Jaccard: **{summary['mean_edge_jaccard']}**",
        f"- Strongest confluence planet: **{summary['strongest_confluence_planet']}**",
        f"- Mean normalized shape Jaccard: **{summary['mean_normalized_shape_jaccard']}**",
        f"- Strongest normalized shape confluence: **{summary['strongest_shape_confluence_planet']}**",
        "",
        "## Planetary Comparison",
        "",
    ]
    for row in report["planetary_confluences"]:
        lines.append(f"- **{row['planet'].title()}** — shared nodes {row['shared_node_count']}, shared channels {row['shared_edge_count']}, opposing currents {row['opposing_current_count']}, node/edge Jaccard {row['node_jaccard']} / {row['edge_jaccard']}")
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
