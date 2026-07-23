# Astronomical Constellation Layer

Atlas keeps three coordinate interpretations separate:

1. **Tropical zodiac** — twelve equal 30-degree signs measured from the equinox.
2. **Lahiri sidereal/Vedic zodiac** — twelve equal 30-degree signs after applying
   the Lahiri ayanamsha.
3. **IAU astronomical constellations** — unequal bounded regions of the observed
   sky. The Sun's ecliptic path crosses thirteen of them, including Ophiuchus.

The third layer is not called a thirteen-sign Vedic zodiac. Ophiuchus is an
astronomical constellation and is not silently inserted into Jyotish sign,
nakshatra, dignity, house, yoga, or dasha calculations.

## Calculation contract

- Planetary positions: Swiss Ephemeris, geocentric.
- Historical time scale: UT converted to TT with Swiss Ephemeris delta-T.
- Constellation boundaries: IAU 88-constellation Delporte boundaries,
  precessed to B1875 through the Roman (1987) algorithm implemented by Astropy.
- `actual_constellation`: uses the body's latitude and actual sky position.
- `ecliptic_path_constellation`: projects the longitude to ecliptic latitude
  zero. This is the comparable thirteen-constellation Sun-path reading.
- Ophiuchus is normalized to the modern English spelling in Atlas output.

Actual and projected constellations can differ. This is expected, particularly
for bodies with meaningful ecliptic latitude. Atlas must retain both values.

## Accuracy limits

- The current output is geocentric, not observer-topocentric.
- Houses and angles require a defensible time, location, timezone, latitude,
  and longitude.
- Estimated historical birth times must remain labeled estimates.
- A constellation classification is an astronomical coordinate fact. Any
  behavioral interpretation remains a separate symbolic hypothesis.

## Primary references

- IAU FAQ: <https://www.iau.org/IAU/Science/What-we-do/FAQs.aspx>
- Astropy `get_constellation`: <https://docs.astropy.org/en/stable/api/astropy.coordinates.get_constellation.html>
- Swiss Ephemeris documentation: <https://www.astro.com/swisseph-download/doc/swisseph.htm>
