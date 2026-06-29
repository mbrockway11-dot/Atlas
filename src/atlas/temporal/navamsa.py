"""Navamsa (D9) wrapper for Atlas Temporal Intelligence."""

from __future__ import annotations

from atlas.temporal.models import NatalChart
from atlas.temporal.vargas import (
    VargaChart,
    build_varga_chart,
    register_varga_strategy,
)


NAVAMSA_ENGINE_VERSION = "1.0"

NAVAMSA_SIZE = 30.0 / 9.0


def navamsa_strategy(
    longitude: float,
) -> tuple[int, int, float]:
    """Convert sidereal longitude into D9 sign, division number, and degree."""

    longitude %= 360.0

    sign_index = int(longitude // 30.0)
    degree_in_sign = longitude % 30.0

    division_number = int(degree_in_sign // NAVAMSA_SIZE)
    degree_in_division = degree_in_sign % NAVAMSA_SIZE

    target_sign = (
        sign_index * 9
        + division_number
    ) % 12

    return (
        target_sign,
        division_number + 1,
        degree_in_division,
    )


register_varga_strategy(
    9,
    navamsa_strategy,
)


def build_navamsa_chart(
    natal: NatalChart,
) -> VargaChart:
    """Build D9 Navamsa chart."""

    return build_varga_chart(
        natal,
        division=9,
    )


def longitude_to_navamsa(
    planet: str,
    longitude: float,
):
    """Compatibility wrapper for older tests/imports."""

    chart_sign, division_number, degree = navamsa_strategy(
        longitude,
    )

    from atlas.temporal.vargas import SIGNS, VargaPosition

    return VargaPosition(
        planet=planet,
        longitude=longitude % 360.0,
        sign=SIGNS[chart_sign],
        sign_index=chart_sign,
        division=9,
        division_number=division_number,
        degree_in_division=degree,
    )


def navamsa_chart_to_dict(
    chart: VargaChart,
) -> dict:
    """Convert Navamsa chart to dictionary."""

    from atlas.temporal.vargas import varga_chart_to_dict

    return varga_chart_to_dict(chart)