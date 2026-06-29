"""Temporal Intelligence dashboard page."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import streamlit as st

from atlas.temporal.aspects import aspect_chart_to_dict, build_aspect_chart
from atlas.temporal.birth import load_birth_data_from_profile
from atlas.temporal.dignity import build_dignity_chart, dignity_chart_to_dict
from atlas.temporal.houses import build_house_chart, house_chart_to_dict
from atlas.temporal.nakshatra import build_nakshatra_chart, nakshatra_chart_to_dict
from atlas.temporal.natal_chart import build_natal_chart, natal_chart_to_dict
from atlas.temporal.navamsa import build_navamsa_chart, navamsa_chart_to_dict
from atlas.temporal.transits import build_transit_chart, transit_chart_to_dict
from atlas.temporal.vimshottari_dasha import (
    build_vimshottari_dasha,
    vimshottari_dasha_to_dict,
)
from atlas.temporal.yoga_engine import evaluate_all_yogas, yoga_evaluation_to_dict


DEFAULT_PROFILE_DIR = Path("output/library/profiles")


def render_temporal_intelligence_page() -> None:
    """Render Temporal Intelligence dashboard."""
    st.header("Temporal Intelligence")
    st.caption("Natal, houses, nakshatras, dignities, yogas, dashas, and transits.")

    root = Path(
        st.text_input(
            "Profile library directory",
            value=str(DEFAULT_PROFILE_DIR),
        )
    )

    if not root.exists():
        st.error(f"Profile directory not found: {root}")
        return

    profiles = load_profiles(root)

    if not profiles:
        st.warning("No profiles found.")
        return

    selected_name = st.selectbox(
        "Select profile",
        [profile["name"] for profile in profiles],
    )

    selected = next(
        profile
        for profile in profiles
        if profile["name"] == selected_name
    )

    transit_date = st.text_input(
        "Transit date",
        value="2026-06-29",
        help="Use YYYY-MM-DD.",
    )

    profile_path = root / selected["slug"]
    birth = load_birth_data_from_profile(profile_path)

    if not birth.birth_date:
        st.error("Selected profile has no birth date.")
        return

    with st.spinner("Building temporal intelligence layers..."):
        natal = build_natal_chart(birth)
        houses = build_house_chart(natal)
        nakshatras = build_nakshatra_chart(natal)
        dignity = build_dignity_chart(natal)
        aspects = build_aspect_chart(houses)
        yogas = evaluate_all_yogas(
            natal=natal,
            houses=houses,
            dignity=dignity,
            aspects=aspects,
        )
        navamsa = build_navamsa_chart(natal)
        dasha = build_vimshottari_dasha(
            name=birth.name,
            birth_date=birth.birth_date,
            nakshatra_chart=nakshatras,
        )
        transits = build_transit_chart(
            natal,
            transit_date=transit_date,
        )

    render_summary(birth, natal, houses, nakshatras, dignity, yogas, dasha, transits)
    render_planets(natal)
    render_houses(houses)
    render_nakshatras(nakshatras)
    render_dignities(dignity)
    render_aspects(aspects)
    render_yogas(yogas)
    render_navamsa(navamsa)
    render_dasha(dasha)
    render_transits(transits)
    render_exports(natal, houses, nakshatras, dignity, aspects, yogas, navamsa, dasha, transits)


def load_profiles(root: Path) -> list[dict]:
    """Load profile names and slugs."""
    profiles: list[dict] = []

    for profile_path in sorted(root.iterdir()):
        if not profile_path.is_dir():
            continue

        intake_path = profile_path / "profile.intake.json"

        name = profile_path.name

        if intake_path.exists():
            try:
                intake = json.loads(intake_path.read_text(encoding="utf-8"))
                name = intake.get("name", name)
            except json.JSONDecodeError:
                pass

        profiles.append(
            {
                "name": name,
                "slug": profile_path.name,
            }
        )

    return profiles


def render_summary(
    birth,
    natal,
    houses,
    nakshatras,
    dignity,
    yogas,
    dasha,
    transits,
) -> None:
    """Render summary cards."""
    st.markdown("## Summary")

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Name", birth.name)
    c2.metric("Birth Date", birth.birth_date)
    c3.metric("Zodiac", natal.zodiac)
    c4.metric("Ayanamsa", natal.ayanamsa)

    c5, c6, c7, c8 = st.columns(4)

    c5.metric("Ascendant", houses.ascendant.sign)
    c6.metric("Moon Nakshatra", dasha.moon_nakshatra)
    c7.metric("Starting Dasha", dasha.moon_nakshatra_lord)
    c8.metric("Yoga Matches", yogas.summary.get("matched", 0))

    c9, c10, c11, c12 = st.columns(4)

    c9.metric("Planets", len(natal.planets))
    c10.metric("Nakshatras", nakshatras.summary.get("nakshatra_count", 0))
    c11.metric("Aspects", aspects_count_safe(transits))
    c12.metric("Transit Contacts", transits.summary.get("contact_count", 0))


def render_planets(natal) -> None:
    """Render natal planets."""
    st.markdown("## Natal Planets")

    rows = [
        {
            "planet": planet,
            "sign": position.sign,
            "degree": round(position.degree_in_sign, 4),
            "longitude": round(position.longitude, 4),
            "retrograde": position.retrograde,
        }
        for planet, position in natal.planets.items()
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_houses(houses) -> None:
    """Render house placements."""
    st.markdown("## Houses")

    rows = [
        {
            "planet": planet,
            "house": placement.house,
            "sign": placement.sign,
            "degree": round(placement.degree_in_sign, 4),
        }
        for planet, placement in houses.placements.items()
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_nakshatras(nakshatras) -> None:
    """Render nakshatras."""
    st.markdown("## Nakshatras")

    rows = [
        {
            "body": body,
            "nakshatra": position.nakshatra,
            "index": position.nakshatra_index,
            "pada": position.pada,
            "degree_in_nakshatra": round(position.degree_in_nakshatra, 4),
        }
        for body, position in nakshatras.positions.items()
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_dignities(dignity) -> None:
    """Render dignity chart."""
    st.markdown("## Planetary Dignity")

    rows = [
        {
            "planet": planet,
            "sign": value.sign,
            "ruler": value.ruler,
            "relationship": value.relationship,
            "own_sign": value.own_sign,
            "exalted": value.exalted,
            "debilitated": value.debilitated,
            "moolatrikona": value.moolatrikona,
            "strength_score": value.strength_score,
        }
        for planet, value in dignity.dignities.items()
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_aspects(aspects) -> None:
    """Render Graha Drishti."""
    st.markdown("## Graha Drishti")

    rows = [
        {
            "source": aspect.source,
            "target": aspect.target,
            "source_house": aspect.source_house,
            "target_house": aspect.target_house,
            "aspect_type": aspect.aspect_type,
            "strength": aspect.strength,
        }
        for aspect in aspects.aspects
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_yogas(yogas) -> None:
    """Render yogas."""
    st.markdown("## Yogas")

    rows = [
        {
            "name": match.name,
            "category": match.category,
            "source": match.source,
            "score": match.score,
            "conditions": f"{match.conditions_passed}/{match.conditions_total}",
        }
        for match in yogas.matches
    ]

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True)
    else:
        st.info("No yogas matched with the current rule set.")


def render_navamsa(navamsa) -> None:
    """Render Navamsa D9."""
    st.markdown("## Navamsa / D9")

    rows = [
        {
            "planet": planet,
            "sign": position.sign,
            "division_number": position.division_number,
            "degree_in_division": round(position.degree_in_division, 4),
        }
        for planet, position in navamsa.positions.items()
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_dasha(dasha) -> None:
    """Render Vimshottari Dasha."""
    st.markdown("## Vimshottari Dasha")

    rows = [
        {
            "lord": period.lord,
            "start_date": period.start_date,
            "end_date": period.end_date,
            "years": round(period.years, 4),
            "level": period.level,
        }
        for period in dasha.periods
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_transits(transits) -> None:
    """Render transit contacts."""
    st.markdown("## Transits")

    rows = [
        {
            "transit_planet": contact.transit_planet,
            "natal_planet": contact.natal_planet,
            "transit_sign": contact.transit_sign,
            "natal_sign": contact.natal_sign,
            "sign_distance": contact.sign_distance,
            "same_sign": contact.same_sign,
            "opposition": contact.opposition,
        }
        for contact in transits.contacts
    ]

    st.dataframe(pd.DataFrame(rows), use_container_width=True)


def render_exports(
    natal,
    houses,
    nakshatras,
    dignity,
    aspects,
    yogas,
    navamsa,
    dasha,
    transits,
) -> None:
    """Render export buttons."""
    st.markdown("## Exports")

    payload = {
        "natal": natal_chart_to_dict(natal),
        "houses": house_chart_to_dict(houses),
        "nakshatras": nakshatra_chart_to_dict(nakshatras),
        "dignity": dignity_chart_to_dict(dignity),
        "aspects": aspect_chart_to_dict(aspects),
        "yogas": yoga_evaluation_to_dict(yogas),
        "navamsa": navamsa_chart_to_dict(navamsa),
        "dasha": vimshottari_dasha_to_dict(dasha),
        "transits": transit_chart_to_dict(transits),
    }

    st.download_button(
        label="Download temporal intelligence JSON",
        data=json.dumps(payload, indent=2, sort_keys=True),
        file_name="temporal_intelligence.json",
        mime="application/json",
    )


def aspects_count_safe(transits) -> int:
    """Temporary summary helper."""
    return transits.summary.get("opposition_count", 0) + transits.summary.get(
        "same_sign_count",
        0,
    )