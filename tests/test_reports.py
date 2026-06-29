from atlas.interpretation.profile import interpret_profile_summary
from atlas.profiles.summary import build_individual_profile_summary
from atlas.reports.markdown import build_profile_markdown_report


def test_build_profile_markdown_report():
    summary = build_individual_profile_summary("Michael Elvis Brockway")
    interpretation = interpret_profile_summary(summary)

    report = build_profile_markdown_report(summary, interpretation)

    assert "# Atlas Codex Report: Michael Elvis Brockway" in report
    assert "## Overview" in report

    # IVE report sections
    assert "## Identity Vector Summary" in report
    assert "## Planetary Structural Signature" in report
    assert "## Planet Relationship Diagnostics" in report
    assert "## Vector Quality" in report

    # Legacy sections are archived, not primary
    assert "## Legacy Pattern Archive" in report
    assert "### Dominant Patterns" in report
    assert "### Dominant Motifs" in report
    assert "## Legacy 21-Layer Archive" in report