from atlas.provenance import build_provenance_report


def test_build_provenance_report():
    report = build_provenance_report()

    assert report["module_count"] > 0
    assert "modules" in report
    assert "active_cipher_engine" in report["modules"]

    active = report["modules"]["active_cipher_engine"]

    assert active["available"] is True
    assert active["path"]