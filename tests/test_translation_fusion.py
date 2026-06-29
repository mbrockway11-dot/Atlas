from atlas.acf.builder import build_acf_profile
from atlas.fusion import (
    build_translation_fusion_report,
    translation_fusion_report_to_dict,
)


def test_build_translation_fusion_report():
    acf = build_acf_profile("Michael Elvis Brockway")

    report = build_translation_fusion_report(acf)

    assert report.name == "Michael Elvis Brockway"
    assert report.planets
    assert 0.0 <= report.global_agreement_score <= 1.0
    assert 0.0 <= report.global_confidence_score <= 1.0
    assert 0.0 <= report.global_completeness <= 1.0


def test_translation_fusion_report_to_dict():
    acf = build_acf_profile("Michael Elvis Brockway")

    report = build_translation_fusion_report(acf)
    data = translation_fusion_report_to_dict(report)

    assert data["name"] == "Michael Elvis Brockway"
    assert "global_agreement_score" in data
    assert "planets" in data