from atlas.services.vedic_behavior_service import build_vedic_behavior_model


def test_vedic_behavior_prefers_sidereal_planets_over_tropical_planets():
    temporal_data = {
        "natal": {
            "zodiac": "tropical",
            "planets": {
                "Sun": {"sign": "Cancer", "longitude": 107.0},
            },
        },
        "sidereal": {
            "zodiac": "sidereal",
            "ayanamsa": "Lahiri",
            "planets": {
                "Sun": {"sign": "Gemini", "longitude": 86.0},
            },
        },
        "birth": {},
        "dignity": {},
        "dasha": {},
        "transits": {},
    }

    result = build_vedic_behavior_model(
        profile_key="coordinate_test",
        temporal_data=temporal_data,
        temporal_metrics={},
        source_warnings=[],
    )

    solar = next(
        assumption
        for assumption in result["assumptions"]
        if assumption["theme"] == "identity_expression"
    )
    assert solar["evidence"] == ["Sun: Gemini 86.0"]
    assert result["coordinate_system"]["zodiac"] == "sidereal"
    assert result["coordinate_system"]["fallback_used"] is False


def test_vedic_behavior_marks_tropical_fallback():
    result = build_vedic_behavior_model(
        profile_key="fallback_test",
        temporal_data={
            "natal": {
                "zodiac": "tropical",
                "planets": {"Sun": {"sign": "Cancer", "longitude": 107.0}},
            },
            "birth": {},
            "dignity": {},
            "dasha": {},
            "transits": {},
        },
        temporal_metrics={},
        source_warnings=[],
    )

    assert result["coordinate_system"]["fallback_used"] is True
    assert result["coordinate_system"]["zodiac"] == "tropical"
    assert result["coordinate_system"]["planet_source"] == "temporal.natal_fallback"
