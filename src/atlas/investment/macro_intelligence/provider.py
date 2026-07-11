"""Public macroeconomic data provider with deterministic caching."""

from __future__ import annotations

from datetime import UTC, datetime
from io import StringIO
from pathlib import Path
from urllib.error import (
    HTTPError,
    URLError,
)
from urllib.request import (
    Request,
    urlopen,
)

import pandas as pd


CACHE_DIR = Path(
    "output/investment_macro_intelligence/cache"
)

BASE_URL = (
    "https://fred.stlouisfed.org/"
    "graph/fredgraph.csv?id={series_id}"
)


def fetch_series(
    series_id: str,
    *,
    timeout: int = 30,
) -> tuple[pd.DataFrame, dict]:
    """Fetch one public economic time series and update its cache."""
    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    cache_path = (
        CACHE_DIR
        / f"{series_id}.csv"
    )

    url = BASE_URL.format(
        series_id=series_id
    )

    metadata = {
        "series_id": series_id,
        "url": url,
        "fetched_at": datetime.now(
            UTC
        ).isoformat(),
        "network_success": False,
        "used_cache": False,
        "error": "",
    }

    try:
        request = Request(
            url,
            headers={
                "User-Agent": (
                    "Atlas-Macro-Intelligence/1.0"
                )
            },
        )

        with urlopen(
            request,
            timeout=timeout,
        ) as response:
            text = response.read().decode(
                "utf-8"
            )

        frame = parse_series_csv(
            text,
            series_id,
        )

        if frame.empty:
            raise ValueError(
                f"{series_id} returned no valid observations."
            )

        frame.to_csv(
            cache_path,
            index=False,
        )

        metadata["network_success"] = True

        return frame, metadata

    except (
        HTTPError,
        URLError,
        TimeoutError,
        UnicodeDecodeError,
        ValueError,
    ) as exc:
        metadata["error"] = str(exc)

    cached = load_cached_series(
        cache_path,
        series_id,
    )

    if not cached.empty:
        metadata["used_cache"] = True
        return cached, metadata

    return empty_series_frame(), metadata


def parse_series_csv(
    text: str,
    series_id: str,
) -> pd.DataFrame:
    """Normalize a downloaded series."""
    frame = pd.read_csv(
        StringIO(text)
    )

    if frame.empty or len(
        frame.columns
    ) < 2:
        return empty_series_frame()

    date_column = frame.columns[0]
    value_column = (
        series_id
        if series_id in frame.columns
        else frame.columns[1]
    )

    result = pd.DataFrame({
        "date": pd.to_datetime(
            frame[date_column],
            errors="coerce",
            utc=True,
        ),
        "value": pd.to_numeric(
            frame[value_column],
            errors="coerce",
        ),
    })

    return (
        result.dropna(
            subset=[
                "date",
                "value",
            ]
        )
        .sort_values(
            "date",
            kind="stable",
        )
        .drop_duplicates(
            subset=["date"],
            keep="last",
        )
        .reset_index(drop=True)
    )


def load_cached_series(
    path: Path,
    series_id: str,
) -> pd.DataFrame:
    if (
        not path.exists()
        or not path.is_file()
        or path.stat().st_size == 0
    ):
        return empty_series_frame()

    try:
        frame = pd.read_csv(path)
    except (
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ):
        return empty_series_frame()

    if not {
        "date",
        "value",
    }.issubset(frame.columns):
        return empty_series_frame()

    frame["date"] = pd.to_datetime(
        frame["date"],
        errors="coerce",
        utc=True,
    )

    frame["value"] = pd.to_numeric(
        frame["value"],
        errors="coerce",
    )

    return frame.dropna(
        subset=[
            "date",
            "value",
        ]
    ).reset_index(drop=True)


def empty_series_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "date",
            "value",
        ]
    )
