"""Astronomical IAU-constellation placements for Atlas Temporal Intelligence.

This module is deliberately separate from tropical signs and the 12-sign
Lahiri sidereal zodiac.  Constellations are unequal regions on the observed
sky.  The Sun's ecliptic path crosses thirteen of those regions, including
Ophiuchus; that fact does not create a thirteenth equal astrological sign.
"""

from __future__ import annotations

from typing import Any

import astropy.units as u
import swisseph as swe
from astropy.coordinates import FK5, GeocentricTrueEcliptic, SkyCoord, get_constellation
from astropy.time import Time

from atlas.temporal.ephemeris import EphemerisResult, PLANET_IDS


CONSTELLATION_ENGINE_VERSION = "1.0"
IAU_BOUNDARY_EPOCH = "B1875"
IAU_ZODIAC_CONSTELLATIONS = (
    "Aries",
    "Taurus",
    "Gemini",
    "Cancer",
    "Leo",
    "Virgo",
    "Libra",
    "Scorpius",
    "Ophiuchus",
    "Sagittarius",
    "Capricornus",
    "Aquarius",
    "Pisces",
)

_ASTROPY_NAME_FIXES = {
    # Astropy's Roman/Delporte lookup currently returns this historical
    # spelling. Atlas exposes the modern IAU English spelling.
    "Ophiucus": "Ophiuchus",
}


def build_astronomical_constellation_chart(
    ephemeris: EphemerisResult,
) -> dict[str, Any]:
    """Return actual-sky and ecliptic-path constellation placements.

    ``actual_constellation`` uses each body's geocentric equatorial position,
    including ecliptic latitude. ``ecliptic_path_constellation`` projects the
    body's longitude onto latitude zero, producing the explicitly requested
    thirteen-constellation Sun-path comparison.
    """
    # Swiss Ephemeris gives delta-T in days. Converting UT to TT avoids
    # pretending that pre-UTC historical dates used the modern UTC scale.
    terrestrial_julian_day = ephemeris.julian_day + float(
        swe.deltat(ephemeris.julian_day)
    )
    observation_time = Time(
        terrestrial_julian_day,
        format="jd",
        scale="tt",
    )
    placements: dict[str, dict[str, Any]] = {}

    for planet, position in ephemeris.planets.items():
        actual_coord = _body_equatorial_coordinate(
            ephemeris.julian_day,
            observation_time,
            planet,
        )
        projected_coord = _ecliptic_path_coordinate(
            position.longitude,
            observation_time,
        )

        actual_name, actual_abbreviation = _constellation_names(actual_coord)
        projected_name, projected_abbreviation = _constellation_names(projected_coord)

        placements[planet] = {
            "planet": planet,
            "actual_constellation": actual_name,
            "actual_constellation_abbreviation": actual_abbreviation,
            "actual_is_one_of_13": actual_name in IAU_ZODIAC_CONSTELLATIONS,
            "ecliptic_path_constellation": projected_name,
            "ecliptic_path_constellation_abbreviation": projected_abbreviation,
            "ecliptic_path_is_one_of_13": projected_name in IAU_ZODIAC_CONSTELLATIONS,
            "is_ophiuchus": (
                actual_name == "Ophiuchus" or projected_name == "Ophiuchus"
            ),
            "tropical_longitude": round(float(position.longitude), 9),
            "ecliptic_latitude": round(float(position.latitude), 9),
            "right_ascension": round(float(actual_coord.ra.deg), 9),
            "declination": round(float(actual_coord.dec.deg), 9),
        }

    return {
        "success": True,
        "version": CONSTELLATION_ENGINE_VERSION,
        "coordinate_system": "geocentric apparent sky; equator/ecliptic of date",
        "time_scale_policy": "Swiss Ephemeris UT converted to TT using delta-T",
        "boundary_system": "IAU 88-constellation Delporte boundaries",
        "boundary_epoch": IAU_BOUNDARY_EPOCH,
        "boundary_algorithm": "Roman 1987 via astropy.coordinates.get_constellation",
        "zodiac_constellation_count": len(IAU_ZODIAC_CONSTELLATIONS),
        "zodiac_constellations": list(IAU_ZODIAC_CONSTELLATIONS),
        "definition": (
            "Astronomical constellations are unequal IAU sky regions. The "
            "ecliptic-path field includes Ophiuchus but is not an equal-sign zodiac."
        ),
        "planets": placements,
        "summary": {
            "planet_count": len(placements),
            "actual_ophiuchus_count": sum(
                row["actual_constellation"] == "Ophiuchus"
                for row in placements.values()
            ),
            "ecliptic_path_ophiuchus_count": sum(
                row["ecliptic_path_constellation"] == "Ophiuchus"
                for row in placements.values()
            ),
        },
        "claim_type": "astronomical_coordinate_classification",
        "causal_claim": False,
    }


def _body_equatorial_coordinate(
    julian_day: float,
    observation_time: Time,
    planet: str,
) -> SkyCoord:
    """Calculate a body's geocentric equatorial position of date."""
    if planet == "Ketu":
        rahu_values, _ = swe.calc_ut(
            julian_day,
            PLANET_IDS["Rahu"],
            swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_EQUATORIAL,
        )
        ra = (float(rahu_values[0]) + 180.0) % 360.0
        dec = -float(rahu_values[1])
    else:
        body_id = PLANET_IDS[planet]
        values, _ = swe.calc_ut(
            julian_day,
            body_id,
            swe.FLG_SWIEPH | swe.FLG_SPEED | swe.FLG_EQUATORIAL,
        )
        ra = float(values[0])
        dec = float(values[1])

    return SkyCoord(
        ra=ra * u.deg,
        dec=dec * u.deg,
        frame=FK5(equinox=observation_time),
    )


def _ecliptic_path_coordinate(
    longitude: float,
    observation_time: Time,
) -> SkyCoord:
    """Project a longitude onto the Sun's zero-latitude ecliptic path."""
    ecliptic = SkyCoord(
        lon=float(longitude) * u.deg,
        lat=0.0 * u.deg,
        frame=GeocentricTrueEcliptic(equinox=observation_time),
    )
    return ecliptic.transform_to(FK5(equinox=observation_time))


def _constellation_names(coordinate: SkyCoord) -> tuple[str, str]:
    """Return normalized full and IAU abbreviated constellation names."""
    full = str(get_constellation(coordinate, short_name=False))
    short = str(get_constellation(coordinate, short_name=True))
    return _ASTROPY_NAME_FIXES.get(full, full), short


__all__ = [
    "CONSTELLATION_ENGINE_VERSION",
    "IAU_ZODIAC_CONSTELLATIONS",
    "build_astronomical_constellation_chart",
]
