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

    rows = [
        {
            "planet": planet.planet,
            "sign": planet.sign,
            "longitude": planet.longitude,
            "nakshatra": getattr(planet, "nakshatra", ""),
            "pada": getattr(planet, "pada", ""),
        }
        for planet in natal.planets
    ]

    render_table(rows, "No natal planets available.")


def render_houses(houses) -> None:
    st.markdown("## Houses")

    rows = [
        {
            "house": house.house,
            "sign": house.sign,
            "ruler": getattr(house, "ruler", ""),
            "theme": getattr(house, "theme", ""),
        }
        for house in houses.houses
    ]

    render_table(rows, "No houses available.")


def render_nakshatras(nakshatras) -> None:
    st.markdown("## Nakshatras")

    rows = [
        {
            "planet": placement.planet,
            "nakshatra": placement.nakshatra,
            "pada": placement.pada,
            "ruler": getattr(placement, "ruler", ""),
        }
        for placement in nakshatras.placements
    ]

    render_table(rows, "No nakshatra placements available.")


def render_dignities(dignity) -> None:
    st.markdown("## Dignities")

    rows = [
        {
            "planet": placement.planet,
            "sign": placement.sign,
            "dignity": placement.dignity,
            "score": getattr(placement, "score", None),
            "notes": getattr(placement, "notes", ""),
        }
        for placement in dignity.placements
    ]

    render_table(rows, "No dignity placements available.")


def render_aspects(aspects) -> None:
    st.markdown("## Aspects")

    rows = [
        {
            "planet_a": aspect.planet_a,
            "planet_b": aspect.planet_b,
            "aspect": aspect.aspect,
            "orb": getattr(aspect, "orb", None),
        }
        for aspect in aspects.aspects
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

    rows = [
        {
            "planet": placement.planet,
            "rashi_sign": getattr(placement, "rashi_sign", ""),
            "navamsa_sign": placement.navamsa_sign,
            "degree": getattr(placement, "degree", None),
        }
        for placement in navamsa.placements
    ]

    render_table(rows, "No navamsa placements available.")


def render_dasha(dasha) -> None:
    st.markdown("## Vimshottari Dasha")

    rows = [
        {
            "mahadasha_lord": period.mahadasha_lord,
            "start_date": period.start_date,
            "end_date": period.end_date,
            "duration_years": getattr(period, "duration_years", None),
        }
        for period in dasha.periods
    ]

    render_table(rows, "No dasha periods available.")


def render_transits(transits) -> None:
    st.markdown("## Transits")

    rows = [
        {
            "transit_planet": contact.transit_planet,
            "natal_planet": contact.natal_planet,
            "aspect": contact.aspect,
            "transit_sign": contact.transit_sign,
            "orb": getattr(contact, "orb", None),
        }
        for contact in transits.contacts
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