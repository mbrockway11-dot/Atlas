"""Import a frozen earthquake cohort from the USGS FDSN event service.

Fetches once, snapshots the exact bytes, and transforms them into the
provenance-gated schema. The raw response and its hash are kept so a result
can be traced to the precise catalogue state that produced it -- USGS revises
events after publication, and a study whose inputs silently change is not
reproducible.

The snapshot is immutable by convention: a later refresh writes v2, it never
mutates v1. Records failing validation are written to a rejection artifact
with a machine-readable reason rather than disappearing.

    python scripts/import_usgs_earthquake_catalogue.py
"""

from __future__ import annotations

import argparse
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import sys
from time import perf_counter
import urllib.parse
import urllib.request


FDSN_BASE = "https://earthquake.usgs.gov/fdsnws/event/1/"
CATALOGUE_VERSION = "usgs_fdsn_event_v1"
TRANSFORM_SCHEMA = "atlas.validation.usgs-earthquake-transform.v1"

# The frozen cohort. Declared here rather than passed in, so the shipped
# default is the pre-registered one and a different cohort is a visible edit.
FROZEN_QUERY: dict[str, str] = {
    "format": "geojson",
    "eventtype": "earthquake",
    "minmagnitude": "7.0",
    "starttime": "1970-01-01T00:00:00Z",
    "endtime": "2025-12-31T23:59:59Z",
    "orderby": "time-asc",
}

# Source fields preserved verbatim. Kept even where unused: re-fetching to
# recover a discarded field would return a different catalogue state.
PRESERVED_PROPERTIES = (
    "updated",
    "status",
    "magType",
    "type",
    "place",
    "url",
    "detail",
    "net",
    "code",
    "ids",
    "sources",
    "tsunami",
    "sig",
    "rms",
    "gap",
    "nst",
    "dmin",
)


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Import the frozen USGS earthquake cohort."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path("data") / "external" / "usgs",
    )
    parser.add_argument(
        "--catalogue-dir",
        type=Path,
        default=Path("data") / "validation" / "earthquakes",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="HTTP timeout in seconds (default: 300).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help=(
            "Overwrite an existing snapshot. Off by default: the snapshot is "
            "immutable, and a refresh should write a new version."
        ),
    )
    return parser


def _get(url: str, timeout: int) -> bytes:
    """Fetch a URL and return the raw bytes."""
    request = urllib.request.Request(
        url, headers={"Accept": "application/json"}
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _canonical_query(query: dict[str, str]) -> str:
    """Return the query in a stable, comparable form."""
    return urllib.parse.urlencode(sorted(query.items()))


def _record_hash(feature: dict) -> str:
    """Return a stable hash of one normalized source feature."""
    encoded = json.dumps(feature, sort_keys=True, separators=(",", ":"))

    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def validate_feature(feature: dict) -> tuple[bool, str]:
    """Return whether a GeoJSON feature qualifies, and why not if it does not.

    Every gate is stated in advance. A record failing any of them is recorded
    as rejected with this reason, never silently dropped.
    """
    properties = feature.get("properties") or {}
    geometry = feature.get("geometry") or {}
    coordinates = geometry.get("coordinates") or []

    if not feature.get("id"):
        return False, "missing_event_id"

    if properties.get("type") != "earthquake":
        return False, "not_earthquake"

    if str(properties.get("status", "")).lower() == "deleted":
        return False, "deleted_status"

    epoch_ms = properties.get("time")

    if epoch_ms is None:
        return False, "missing_origin_time"

    magnitude = properties.get("mag")

    if magnitude is None:
        return False, "missing_magnitude"

    try:
        if float(magnitude) < 7.0:
            return False, "below_magnitude_threshold"
    except (TypeError, ValueError):
        return False, "unparseable_magnitude"

    if len(coordinates) < 3:
        return False, "incomplete_coordinates"

    longitude, latitude, depth = coordinates[0], coordinates[1], coordinates[2]

    for value, label in (
        (longitude, "longitude"),
        (latitude, "latitude"),
        (depth, "depth"),
    ):
        if value is None:
            return False, f"missing_{label}"

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            return False, f"unparseable_{label}"

        if numeric != numeric or abs(numeric) == float("inf"):
            return False, f"non_finite_{label}"

    return True, ""


def main() -> int:
    """Fetch, snapshot, and transform the cohort."""
    args = build_parser().parse_args()
    started = perf_counter()

    args.raw_dir.mkdir(parents=True, exist_ok=True)
    args.catalogue_dir.mkdir(parents=True, exist_ok=True)

    response_path = args.raw_dir / "response.geojson"

    if response_path.exists() and not args.force:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        f"{response_path} already exists. The snapshot is "
                        "immutable -- a refresh should write a new catalogue "
                        "version rather than mutate this one. Pass --force "
                        "only to repair a failed download."
                    ),
                },
                indent=2,
            )
        )
        return 1

    canonical = _canonical_query(FROZEN_QUERY)
    service_version = _get(FDSN_BASE + "version", args.timeout).decode().strip()

    count_payload = json.loads(
        _get(f"{FDSN_BASE}count?{canonical}", args.timeout)
    )
    expected = int(count_payload.get("count", 0))
    max_allowed = int(count_payload.get("maxAllowed", 20_000))

    if expected > max_allowed:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        f"{expected} events exceeds the service limit of "
                        f"{max_allowed}; the query must be partitioned."
                    ),
                },
                indent=2,
            )
        )
        return 1

    retrieved_at = datetime.now(UTC)
    raw = _get(f"{FDSN_BASE}query?{canonical}", args.timeout)
    raw_hash = hashlib.sha256(raw).hexdigest()

    response_path.write_bytes(raw)
    (args.raw_dir / "response.sha256").write_text(
        f"{raw_hash}  response.geojson\n", encoding="utf-8"
    )
    (args.raw_dir / "query.json").write_text(
        json.dumps(
            {
                "service": FDSN_BASE,
                "parameters": FROZEN_QUERY,
                "canonical_query": canonical,
                "count_endpoint_reported": expected,
                "max_allowed": max_allowed,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    (args.raw_dir / "retrieval.json").write_text(
        json.dumps(
            {
                "retrieved_utc": retrieved_at.isoformat(),
                "service_version": service_version,
                "response_sha256": raw_hash,
                "response_bytes": len(raw),
                "catalogue_version": CATALOGUE_VERSION,
                "immutable": True,
                "note": (
                    "USGS revises events after publication. This snapshot is "
                    "frozen; a refresh must produce v2 and a revision report, "
                    "never mutate v1."
                ),
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    payload = json.loads(raw)
    features = payload.get("features", [])

    accepted: list[dict] = []
    rejected: list[dict] = []
    seen_ids: set[str] = set()

    for feature in features:
        ok, reason = validate_feature(feature)
        feature_id = str(feature.get("id", ""))

        if ok and feature_id in seen_ids:
            ok, reason = False, "duplicate_event_id"

        properties = feature.get("properties") or {}
        coordinates = (feature.get("geometry") or {}).get("coordinates") or []

        if not ok:
            rejected.append(
                {
                    "source_event_id": feature_id,
                    "reason": reason,
                    "magnitude": properties.get("mag"),
                    "type": properties.get("type"),
                    "status": properties.get("status"),
                    "time": properties.get("time"),
                }
            )
            continue

        seen_ids.add(feature_id)

        instant = datetime.fromtimestamp(
            float(properties["time"]) / 1000.0, tz=UTC
        )

        row = {
            "event_id": feature_id,
            "label": str(properties.get("place") or feature_id),
            "instant": instant.isoformat(),
            "event_class": "earthquake",
            "magnitude": float(properties["mag"]),
            "latitude": float(coordinates[1]),
            "longitude": float(coordinates[0]),
            "provenance": "catalogue_verified",
            "source": CATALOGUE_VERSION,
            "timestamp_precision": "second",
            "source_catalogue": CATALOGUE_VERSION,
            "source_event_id": feature_id,
            "source_retrieved_utc": retrieved_at.isoformat(),
            "source_query": canonical,
            "source_record_hash": _record_hash(feature),
            "source_depth_km": float(coordinates[2]),
            "source_service_version": service_version,
        }

        for key in PRESERVED_PROPERTIES:
            if key in properties:
                row[f"source_{key}"] = properties[key]

        accepted.append(row)

    instants = [row["instant"] for row in accepted]
    magnitudes = [row["magnitude"] for row in accepted]

    catalogue_path = args.catalogue_dir / "catalogue.json"
    catalogue_path.write_text(
        json.dumps({"events": accepted}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    (args.catalogue_dir / "rejected_records.json").write_text(
        json.dumps({"rejected": rejected}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    def magnitude_band(value: float) -> str:
        return f"{int(value * 2) / 2:.1f}"

    distribution: dict[str, int] = {}

    for magnitude in magnitudes:
        band = magnitude_band(magnitude)
        distribution[band] = distribution.get(band, 0) + 1

    manifest = {
        "catalogue_version": CATALOGUE_VERSION,
        "transform_schema": TRANSFORM_SCHEMA,
        "service": FDSN_BASE,
        "service_version": service_version,
        "retrieved_utc": retrieved_at.isoformat(),
        "query_parameters": FROZEN_QUERY,
        "canonical_query": canonical,
        "raw_response_sha256": raw_hash,
        "raw_response_bytes": len(raw),
        "features_returned": len(features),
        "count_endpoint_reported": expected,
        "accepted_count": len(accepted),
        "rejected_count": len(rejected),
        "rejection_reasons": {
            reason: sum(1 for row in rejected if row["reason"] == reason)
            for reason in sorted({row["reason"] for row in rejected})
        },
        "duplicate_handling": (
            "First occurrence of an event id wins; later ones are rejected "
            "as duplicate_event_id."
        ),
        "earliest_event_utc": min(instants) if instants else None,
        "latest_event_utc": max(instants) if instants else None,
        "magnitude_min": min(magnitudes) if magnitudes else None,
        "magnitude_max": max(magnitudes) if magnitudes else None,
        "magnitude_distribution": dict(sorted(distribution.items())),
        "location_caveat": (
            "Earthquake latitude, longitude and depth are catalogue metadata "
            "and control information. They are NOT inputs to the present "
            "geocentric R0 vector, which depends only on the instant. They "
            "are preserved because a later topocentric or house-based "
            "representation would need them."
        ),
    }

    (args.catalogue_dir / "catalogue_manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print(
        json.dumps(
            {
                "success": True,
                "service_version": service_version,
                "retrieved_utc": retrieved_at.isoformat(),
                "raw_response_sha256": raw_hash[:16],
                "features_returned": len(features),
                "accepted": len(accepted),
                "rejected": len(rejected),
                "rejection_reasons": manifest["rejection_reasons"],
                "date_range": [
                    manifest["earliest_event_utc"],
                    manifest["latest_event_utc"],
                ],
                "magnitude_range": [
                    manifest["magnitude_min"],
                    manifest["magnitude_max"],
                ],
                "catalogue": str(catalogue_path),
                "elapsed_seconds": round(perf_counter() - started, 2),
            },
            indent=2,
        )
    )

    return 0


if __name__ == "__main__":
    sys.exit(main())
