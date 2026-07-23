from atlas.services.profile_report_service import normalize_temporal_for_interpreter


def test_profile_report_uses_sidereal_planets_for_sidereal_narrative():
    tropical = {"zodiac": "tropical", "planets": {"Sun": {"sign": "Cancer"}}}
    sidereal = {"zodiac": "sidereal", "planets": {"Sun": {"sign": "Gemini"}}}
    normalized = normalize_temporal_for_interpreter({
        "exports": {"birth": {}, "natal": tropical, "sidereal": sidereal}
    })
    assert normalized["natal"] is sidereal
    assert normalized["tropical_natal"] is tropical
    assert normalized["natal"]["planets"]["Sun"]["sign"] == "Gemini"
    assert normalized["zodiac"] == "sidereal"
