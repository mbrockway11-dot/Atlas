from atlas.kamea.squares import KAMEAS


def test_all_kameas_have_valid_reports():
    for kamea in KAMEAS.values():
        report = kamea.validation_report()

        assert report.valid is True
        assert report.unique_values == kamea.max_value
        assert report.missing == ()
        assert report.extra == ()
        assert report.duplicates == ()