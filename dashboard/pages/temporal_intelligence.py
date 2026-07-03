"""Temporal Intelligence dashboard page."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from atlas.services.temporal_intelligence_service import (
    DEFAULT_PROFILE_DIR,
    DEFAULT_TRANSIT_DATE,
    build_temporal_intelligence_payload,
    json_export,
    list_temporal_profiles,
)


def render_temporal_intelligence_page() -> None:
    st.header("Temporal Intelligence")
    st.caption("Natal, houses, nakshatras, dignities, yogas, dashas, and transits.")

    profile_dir = st.text_input(
        "Profile library directory",
        value=str(DEFAULT_PROFILE_DIR),
    )

    profiles = list_temporal_profiles(profile_dir)

    if not profiles:
        st.warning("No profiles found.")
        return

    selected_name = st.selectbox(
        "Select profile",
        [profile["name"] for profile in profiles],
    )

    selected = next(profile for profile in profiles if profile["name"] == selected_name)

    transit_date = st.text_input(
        "Transit date",
        value=DEFAULT_TRANSIT_DATE,
    )

    with st.spinner("Building temporal intelligence layers..."):
        payload = build_temporal_intelligence_payload(
            selected["slug"],
            profile_dir,
            transit_date=transit_date,
        )

    if not payload.get("success"):
        for error in payload.get("errors", []):
            st.error(error)
        with st.expander("Raw service payload", expanded=False):
            st.json(payload)
        return

    data = payload["data"]

    render_summary(payload)
    render_planets(data["natal"])
    render_houses(data["houses"])
    render_nakshatras(data["nakshatras"])
    render_dignities(data["dignity"])
    render_aspects(data["aspects"])
    render_yogas(data["yogas"])
    render_navamsa(data["navamsa"])
    render_dasha(data["dasha"])
    render_transits(data["transits"])
    render_exports(payload["exports"])


def render_summary(payload: dict) -> None:
    st.markdown("## Summary")

    metrics = payload.get("metrics", {})

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Birth Date", metrics.get("birth_date", ""))
    c2.metric("Birth Time", metrics.get("birth_time", "Unknown"))
    c3.metric("Planets", metrics.get("planet_count", 0))
    c4.metric("Houses", metrics.get("house_count", 0))

    c5, c6, c7, c8 = st.columns(4)
    c5.metric("Nakshatras", metrics.get("nakshatra_count", 0))
    c6.metric("Dignities", metrics.get("dignity_count", 0))
    c7.metric("Yogas", metrics.get("yoga_count", 0))
    c8.metric("Dasha Periods", metrics.get("dasha_periods", 0))

    c9, c10 = st.columns(2)
    c9.metric("Transit Contacts", metrics.get("transit_contacts", 0))
    c10.metric("Transit Aspects", metrics.get("transit_aspects", 0))

    with st.expander("Temporal Metrics JSON", expanded=False):
        st.json(metrics)


def render_planets(natal) -> None:
    st.markdown("## Natal Planets")

    planets = natal.get("planets", {}) if isinstance(natal, dict) else {}

    rows = [
        {
            "planet": planet,
            "sign": data.get("sign", ""),
            "longitude": data.get("longitude", ""),
            "degree": data.get("degree", ""),
        }
        for planet, data in planets.items()
    ]

    render_table(rows, "No natal planets available.")


def render_houses(houses) -> None:
    st.markdown("## Houses")

    items = houses.get("houses", {}) if isinstance(houses, dict) else {}

    rows = [
        {
            "house": key,
            "sign": value.get("sign", ""),
            "ruler": value.get("ruler", ""),
            "theme": value.get("theme", ""),
        }
        for key, value in (
            items.items() if isinstance(items, dict) else enumerate(items, start=1)
        )
    ]

    render_table(rows, "No houses available.")


def render_nakshatras(nakshatras) -> None:
    st.markdown("## Nakshatras")

    positions = nakshatras.get("positions", {}) if isinstance(nakshatras, dict) else {}

    rows = [
        {
            "planet": planet,
            "nakshatra": data.get("nakshatra", ""),
            "pada": data.get("pada", ""),
            "ruler": data.get("ruler", ""),
            "degree_in_nakshatra": data.get("degree_in_nakshatra", ""),
        }
        for planet, data in positions.items()
    ]

    render_table(rows, "No nakshatra placements available.")


def render_dignities(dignity) -> None:
    st.markdown("## Dignities")

    dignities = dignity.get("dignities", {}) if isinstance(dignity, dict) else {}

    rows = [
        {
            "planet": planet,
            "sign": data.get("sign", ""),
            "ruler": data.get("ruler", ""),
            "relationship": data.get("relationship", ""),
            "own_sign": data.get("own_sign", False),
            "exalted": data.get("exalted", False),
            "debilitated": data.get("debilitated", False),
            "moolatrikona": data.get("moolatrikona", False),
            "strength_score": data.get("strength_score", ""),
        }
        for planet, data in dignities.items()
    ]

    render_table(rows, "No dignity placements available.")


def render_aspects(aspects) -> None:
    st.markdown("## Aspects")

    rows = [
        {
            "source": aspect.get("source", ""),
            "target": aspect.get("target", ""),
            "source_house": aspect.get("source_house", ""),
            "target_house": aspect.get("target_house", ""),
            "aspect_type": aspect.get("aspect_type", ""),
            "strength": aspect.get("strength", ""),
        }
        for aspect in (aspects.get("aspects", []) if isinstance(aspects, dict) else [])
    ]

    render_table(rows, "No aspects available.")


def render_yogas(yogas) -> None:
    st.markdown("## Yogas")

    rows = [
        {
            "name": yoga.name,
            "present": yoga.present,
            "strength": getattr(yoga, "strength", None),
            "description": getattr(yoga, "description", ""),
        }
        for yoga in yogas.yogas
    ]

    render_table(rows, "No yogas available.")


def render_navamsa(navamsa) -> None:
    st.markdown("## Navamsa")

    positions = navamsa.get("positions", {}) if isinstance(navamsa, dict) else {}

    rows = [
        {
            "planet": planet,
            "sign": data.get("sign", ""),
            "sign_index": data.get("sign_index", ""),
            "division": data.get("division", ""),
            "division_number": data.get("division_number", ""),
            "degree_in_division": data.get("degree_in_division", ""),
        }
        for planet, data in positions.items()
    ]

    render_table(rows, "No navamsa placements available.")


def render_dasha(dasha) -> None:
    st.markdown("## Vimshottari Dasha")

    rows = [
        {
            "lord": period.get("lord", ""),
            "level": period.get("level", ""),
            "start_date": period.get("start_date", ""),
            "end_date": period.get("end_date", ""),
            "years": period.get("years", ""),
        }
        for period in (dasha.get("periods", []) if isinstance(dasha, dict) else [])
    ]

    render_table(rows, "No dasha periods available.")


def render_transits(transits) -> None:
    st.markdown("## Transits")

    rows = [
        {
            "transit_planet": contact.get("transit_planet", ""),
            "natal_planet": contact.get("natal_planet", ""),
            "contact_type": contact.get("contact_type", ""),
            "transit_sign": contact.get("transit_sign", ""),
            "natal_sign": contact.get("natal_sign", ""),
            "orb": contact.get("orb", ""),
        }
        for contact in (transits.get("contacts", []) if isinstance(transits, dict) else [])
    ]

    render_table(rows, "No transit contacts available.")


def render_exports(exports: dict) -> None:
    st.markdown("## Exports")

    st.download_button(
        label="Download temporal intelligence JSON",
        data=json_export(exports),
        file_name="temporal_intelligence.json",
        mime="application/json",
    )

    with st.expander("Raw Temporal Export JSON", expanded=False):
        st.json(exports)


def render_table(rows: list[dict], empty_message: str) -> None:
    if not rows:
        st.info(empty_message)
        return

    st.dataframe(pd.DataFrame(rows), width="stretch")
