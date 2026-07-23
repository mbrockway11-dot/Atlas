"""Reproducible transit exposure calculations with explicit uncertainty."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from atlas.temporal.ephemeris import build_ephemeris
from atlas.temporal.models import BirthData
from atlas.services.profile_path_service import PROJECT_ROOT


ASPECT_ANGLES = {
    "conjunction": 0.0,
    "sextile": 60.0,
    "square": 90.0,
    "trine": 120.0,
    "opposition": 180.0,
}
CALCULATION_METHOD = "Swiss Ephemeris tropical geocentric longitudes; daily 12:00 UT scan"


def build_transit_exposures(
    profiles: list[dict[str, Any]],
    windows: list[dict[str, Any]],
    *,
    scan_days: int = 15,
    max_orb: float = 5.0,
) -> list[dict[str, Any]]:
    profile_map = {row["profile_key"]: row for row in profiles}
    rows: list[dict[str, Any]] = []
    for window in windows:
        profile = profile_map.get(window["profile_key"])
        if not profile or not profile.get("birth_date"):
            continue
        rows.extend(build_window_exposures(profile, window, scan_days=scan_days, max_orb=max_orb))
    return rows


def build_pairwise_natal_contacts(
    profiles: list[dict[str, Any]],
    relationships: list[dict[str, Any]],
    *,
    max_orb: float = 3.0,
) -> list[dict[str, Any]]:
    """Build reproducible relationship contacts with birth-time sensitivity.

    These are geometric contacts, not behavioral or causal evidence. Tropical
    longitudes are used consistently for both people; aspect separations are
    invariant when the same ayanamsha is subtracted from both charts.
    """
    profile_map = {row["profile_key"]: row for row in profiles}
    output: list[dict[str, Any]] = []
    for relationship in relationships:
        left = profile_map.get(relationship["source_profile"])
        right = profile_map.get(relationship["target_profile"])
        if not left or not right or not left.get("birth_date") or not right.get("birth_date"):
            continue
        left_known = _profile_time_known(left)
        right_known = _profile_time_known(right)
        left_sets = _natal_uncertainty_sets(left, left_known)
        right_sets = _natal_uncertainty_sets(right, right_known)
        for left_planet in sorted(left_sets["central"]):
            for right_planet in sorted(right_sets["central"]):
                for aspect, angle in ASPECT_ANGLES.items():
                    central_orb = aspect_orb(
                        left_sets["central"][left_planet]["longitude"],
                        right_sets["central"][right_planet]["longitude"],
                        angle,
                    )
                    if central_orb > max_orb:
                        continue
                    endpoint_orbs = [
                        aspect_orb(
                            left_sets[left_endpoint][left_planet]["longitude"],
                            right_sets[right_endpoint][right_planet]["longitude"],
                            angle,
                        )
                        for left_endpoint in ("early", "late")
                        for right_endpoint in ("early", "late")
                    ]
                    time_sensitive = (
                        (not left_known and left_planet == "Moon")
                        or (not right_known and right_planet == "Moon")
                    )
                    output.append({
                        "contact_id": f"{relationship['relationship_id']}:{left_planet}:{right_planet}:{aspect}",
                        "relationship_id": relationship["relationship_id"],
                        "profile_a": left["profile_key"],
                        "profile_b": right["profile_key"],
                        "profile_a_planet": left_planet,
                        "profile_b_planet": right_planet,
                        "aspect": aspect,
                        "aspect_angle": angle,
                        "orb_degrees": round(central_orb, 6),
                        "maximum_endpoint_orb": round(max(endpoint_orbs), 6),
                        "contact_stable_across_birth_time_range": all(value <= max_orb for value in endpoint_orbs),
                        "birth_time_sensitive": time_sensitive,
                        "profile_a_birth_time_status": left.get("birth_time_status", "unknown"),
                        "profile_b_birth_time_status": right.get("birth_time_status", "unknown"),
                        "houses_angles_included": False,
                        "zodiac_frame": "tropical_geocentric_for_geometry",
                        "zodiac_invariance_note": "Pairwise angular separation is unchanged by a shared sidereal offset.",
                        "claim_type": "astronomical_calculation",
                        "causal_claim": False,
                        "interpretive_status": "symbolic_hypothesis_only",
                        "source_citations": relationship.get("source_citations", []),
                    })
    return sorted(output, key=lambda row: (row["relationship_id"], row["orb_degrees"], row["contact_id"]))


def _profile_time_known(profile: dict[str, Any]) -> bool:
    return bool(str(profile.get("birth_time") or "").strip()) and profile.get("birth_time_status") == "known"


def _profile_central_time(profile: dict[str, Any]) -> tuple[str, str]:
    supplied = str(profile.get("birth_time") or "").strip()
    status = profile.get("birth_time_status", "unknown")
    if supplied and status == "known":
        return supplied, "verified recorded time used"
    if supplied and status in {"reported_unverified", "estimated_historical"}:
        return supplied, (
            f"{status} time used as central estimate; 00:00/12:00/23:59 full-day "
            "range retained for sensitivity; houses and angles disabled"
        )
    return "12:00", "no historical estimate available; noon computational center with 00:00/12:00/23:59 uncertainty range; noon is not treated as certain"


def _natal_uncertainty_sets(profile: dict[str, Any], time_known: bool) -> dict[str, dict[str, dict[str, Any]]]:
    central_time, _ = _profile_central_time(profile)
    return {
        "central": positions(profile["name"], profile["birth_date"], central_time or "12:00", time_known=time_known),
        "early": positions(profile["name"], profile["birth_date"], "00:00", time_known=False),
        "late": positions(profile["name"], profile["birth_date"], "23:59", time_known=False),
    }


def build_window_exposures(
    profile: dict[str, Any],
    window: dict[str, Any],
    *,
    scan_days: int,
    max_orb: float,
) -> list[dict[str, Any]]:
    anchor = date.fromisoformat(window["anchor_date"])
    time_known = _profile_time_known(profile)
    central_time, central_time_policy = _profile_central_time(profile)
    natal_central = positions(profile["name"], profile["birth_date"], central_time, time_known=time_known)
    natal_early = positions(profile["name"], profile["birth_date"], "00:00", time_known=False)
    natal_late = positions(profile["name"], profile["birth_date"], "23:59", time_known=False)
    transit_by_offset = {
        offset: positions("Transit", (anchor + timedelta(days=offset)).isoformat(), "12:00", time_known=False)
        for offset in range(-scan_days, scan_days + 1)
    }
    candidates: list[dict[str, Any]] = []
    for transit_planet in sorted(transit_by_offset[0]):
        for natal_target in sorted(natal_central):
            for aspect, angle in ASPECT_ANGLES.items():
                series = [
                    aspect_orb(
                        transit_by_offset[offset][transit_planet]["longitude"],
                        natal_central[natal_target]["longitude"],
                        angle,
                    )
                    for offset in range(-scan_days, scan_days + 1)
                ]
                minimum = min(series)
                if minimum > max_orb:
                    continue
                min_index = series.index(minimum)
                min_offset = min_index - scan_days
                anchor_orb = series[scan_days]
                early_orb = aspect_orb(transit_by_offset[0][transit_planet]["longitude"], natal_early[natal_target]["longitude"], angle)
                late_orb = aspect_orb(transit_by_offset[0][transit_planet]["longitude"], natal_late[natal_target]["longitude"], angle)
                stable = (early_orb <= max_orb) == (late_orb <= max_orb) if not time_known else True
                in_orb_offsets = [offset - scan_days for offset, value in enumerate(series) if value <= max_orb]
                exact_offsets = local_minima_offsets(series, threshold=min(1.0, max_orb))
                candidates.append({
                    "exposure_id": f"{window['window_id']}:{transit_planet}:{natal_target}:{aspect}",
                    "profile_key": profile["profile_key"],
                    "event_id": window.get("event_id"),
                    "event_family": window.get("event_family"),
                    "window_id": window["window_id"],
                    "window_kind": window["window_kind"],
                    "anchor_date": window["anchor_date"],
                    "outcome_present": int(bool(window.get("outcome_present"))),
                    "transit_planet": transit_planet,
                    "natal_target": natal_target,
                    "aspect": aspect,
                    "aspect_angle": angle,
                    "orb_at_anchor": round(anchor_orb, 6),
                    "minimum_orb": round(minimum, 6),
                    "exactness": round(max(0.0, 1.0 - minimum / max(max_orb, 0.000001)), 6),
                    "applying_separating": applying_state(series, scan_days),
                    "retrograde_at_anchor": bool(transit_by_offset[0][transit_planet]["retrograde"]),
                    "duration_days_in_orb": len(in_orb_offsets),
                    "first_in_orb_date": (anchor + timedelta(days=min(in_orb_offsets))).isoformat() if in_orb_offsets else None,
                    "closest_date": (anchor + timedelta(days=min_offset)).isoformat(),
                    "first_exact_hit": (anchor + timedelta(days=exact_offsets[0])).isoformat() if exact_offsets else None,
                    "repeated_hit_count": len(exact_offsets),
                    "lead_days": scan_days,
                    "lag_days": scan_days,
                    "birth_time_known": time_known,
                    "birth_time_policy": central_time_policy,
                    "central_birth_time_used": central_time,
                    "central_birth_time_status": profile.get("birth_time_status", "unknown"),
                    "natal_longitude_uncertainty_degrees": round(angular_distance(natal_early[natal_target]["longitude"], natal_late[natal_target]["longitude"]), 6),
                    "contact_stable_across_birth_time_range": stable,
                    "fast_moon_uncertainty": bool(not time_known and natal_target == "Moon"),
                    "houses_angles_included": False,
                    "houses_angles_disabled_reason": "birth time unavailable or house method not preregistered" if not time_known else "house method not preregistered for pilot",
                    "calculation_method": CALCULATION_METHOD,
                    "source_inputs": [f"profile:{profile['profile_key']}:birth", f"window:{window['window_id']}"],
                    "evidence_type": "astronomical_calculation",
                })
    concurrent = sum(row["orb_at_anchor"] <= max_orb for row in candidates)
    cluster = sorted({f"{row['transit_planet']} {row['aspect']} {row['natal_target']}" for row in candidates if row["orb_at_anchor"] <= max_orb})
    for row in candidates:
        row["concurrent_transit_count"] = concurrent
        row["transit_cluster"] = cluster
    return candidates


def positions(name: str, day: str, time: str, *, time_known: bool) -> dict[str, dict[str, Any]]:
    result = build_ephemeris(
        BirthData(name=name, birth_date=day, birth_time=time, birth_place="", time_known=time_known),
        ephemeris_path=PROJECT_ROOT / "data" / "ephemeris",
    )
    return {
        key: {"longitude": value.longitude, "speed": value.speed, "retrograde": value.retrograde}
        for key, value in result.planets.items()
    }


def aspect_orb(longitude_a: float, longitude_b: float, exact_angle: float) -> float:
    return abs(angular_distance(longitude_a, longitude_b) - exact_angle)


def angular_distance(longitude_a: float, longitude_b: float) -> float:
    difference = abs((longitude_a - longitude_b) % 360.0)
    return min(difference, 360.0 - difference)


def applying_state(series: list[float], anchor_index: int) -> str:
    if anchor_index <= 0 or anchor_index >= len(series) - 1:
        return "indeterminate"
    before, after = series[anchor_index - 1], series[anchor_index + 1]
    if abs(before - after) < 1e-9:
        return "stationary_or_indeterminate"
    return "applying" if after < before else "separating"


def local_minima_offsets(series: list[float], *, threshold: float) -> list[int]:
    center = len(series) // 2
    offsets: list[int] = []
    for index, value in enumerate(series):
        left = series[index - 1] if index else float("inf")
        right = series[index + 1] if index + 1 < len(series) else float("inf")
        if value <= threshold and value <= left and value <= right:
            offsets.append(index - center)
    return offsets
