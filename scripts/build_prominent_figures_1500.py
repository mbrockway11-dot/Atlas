
"""Build a resumable 1500 prominent figure corpus from Wikidata.

Outputs:
- research/profile_intake/prominent_figures_1500.csv
- research/profile_intake/prominent_figures_1500.json
- research/profile_intake/prominent_figures_1500_names.txt
- output/library/profiles/<profile_key>/profile.intake.json

This script is intentionally slow and cached to avoid Wikidata rate limits.
"""

from __future__ import annotations

import csv
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


API = "https://www.wikidata.org/w/api.php"
WIKI_API = "https://en.wikipedia.org/w/api.php"

TARGET_TOTAL = 1500

OUT_DIR = Path("research/profile_intake")
CSV_PATH = OUT_DIR / "prominent_figures_1500.csv"
JSON_PATH = OUT_DIR / "prominent_figures_1500.json"
NAMES_PATH = OUT_DIR / "prominent_figures_1500_names.txt"

CACHE_DIR = Path("output/wikidata_cache")
QID_CACHE_PATH = CACHE_DIR / "prominent_figures_qids_from_categories.json"
ENTITY_CACHE_PATH = CACHE_DIR / "prominent_figures_entities_from_categories.json"

LIBRARY_DIR = Path("output/library/profiles")

REQUEST_SLEEP_SECONDS = 4.0
RATE_LIMIT_SLEEP_SECONDS = 90
MAX_SEARCH_OFFSET = 500
SEARCH_LIMIT = 50
ENTITY_CHUNK_SIZE = 20


SEARCH_TERMS = [
    "philosopher",
    "scientist",
    "mathematician",
    "physicist",
    "chemist",
    "biologist",
    "astronomer",
    "inventor",
    "engineer",
    "physician",
    "psychologist",
    "economist",
    "historian",
    "sociologist",
    "anthropologist",
    "politician",
    "president",
    "prime minister",
    "king",
    "queen",
    "emperor",
    "general",
    "military leader",
    "revolutionary",
    "activist",
    "writer",
    "poet",
    "novelist",
    "playwright",
    "journalist",
    "artist",
    "painter",
    "sculptor",
    "architect",
    "composer",
    "musician",
    "singer",
    "actor",
    "director",
    "filmmaker",
    "entrepreneur",
    "industrialist",
    "explorer",
    "religious leader",
    "theologian",
    "saint",
    "lawyer",
    "judge",
    "athlete",
    "Nobel Prize winner",
    "ancient Greek philosopher",
    "Roman emperor",
    "Chinese philosopher",
    "Indian philosopher",
    "Islamic scholar",
    "Renaissance artist",
    "Enlightenment philosopher",
    "civil rights activist",
    "computer scientist",
    "founder",
    "chief executive officer",
    "pope",
    "prophet",
    "archaeologist",
    "linguist",
    "composer classical music",
    "jazz musician",
    "film director",
    "Olympic athlete",
]


def api_get(params: dict[str, Any]) -> dict[str, Any]:
    """Call Wikidata API with throttling, cache, and 429 handling."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    params = {
        "format": "json",
        "formatversion": "2",
        **params,
    }

    cache_key = hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.json"

    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache_path.unlink(missing_ok=True)

    url = API + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AtlasResearchBot/1.0 local corpus builder",
            "Accept": "application/json",
        },
    )

    last_error = None

    for attempt in range(1, 8):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                time.sleep(REQUEST_SLEEP_SECONDS)
                return data

        except urllib.error.HTTPError as exc:
            last_error = exc

            if exc.code == 429:
                retry_after = exc.headers.get("Retry-After")
                wait = int(retry_after) if retry_after and retry_after.isdigit() else RATE_LIMIT_SLEEP_SECONDS
                print(f"Rate limited by Wikidata. Waiting {wait} seconds...")
                time.sleep(wait)
                continue

            print(f"HTTP attempt {attempt} failed: {exc}")
            time.sleep(10 * attempt)

        except Exception as exc:
            last_error = exc
            print(f"API attempt {attempt} failed: {exc}")
            time.sleep(10 * attempt)

    print(f"Skipping failed request after retries: {last_error}")
    return {}


def load_json(path: Path, default: Any) -> Any:
    """Load JSON safely."""
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def save_json(path: Path, payload: Any) -> None:
    """Save JSON safely."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def wiki_api_get(params: dict[str, Any]) -> dict[str, Any]:
    """Call English Wikipedia API."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    params = {
        "format": "json",
        "formatversion": "2",
        **params,
    }

    cache_key = "wiki_" + hashlib.sha256(json.dumps(params, sort_keys=True).encode("utf-8")).hexdigest()
    cache_path = CACHE_DIR / f"{cache_key}.json"

    if cache_path.exists():
        try:
            return json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            cache_path.unlink(missing_ok=True)

    url = WIKI_API + "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "AtlasResearchBot/1.0 local corpus builder",
            "Accept": "application/json",
        },
    )

    last_error = None

    for attempt in range(1, 8):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.loads(response.read().decode("utf-8"))
                cache_path.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
                time.sleep(REQUEST_SLEEP_SECONDS)
                return data

        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code == 429:
                wait = RATE_LIMIT_SLEEP_SECONDS
                print(f"Rate limited by Wikipedia. Waiting {wait} seconds...")
                time.sleep(wait)
                continue
            print(f"Wikipedia HTTP attempt {attempt} failed: {exc}")
            time.sleep(10 * attempt)

        except Exception as exc:
            last_error = exc
            print(f"Wikipedia API attempt {attempt} failed: {exc}")
            time.sleep(10 * attempt)

    print(f"Skipping failed Wikipedia request after retries: {last_error}")
    return {}


PEOPLE_CATEGORIES = [
    "Category:Philosophers",
    "Category:Scientists",
    "Category:Mathematicians",
    "Category:Physicists",
    "Category:Chemists",
    "Category:Biologists",
    "Category:Astronomers",
    "Category:Inventors",
    "Category:Engineers",
    "Category:Physicians",
    "Category:Psychologists",
    "Category:Economists",
    "Category:Historians",
    "Category:Sociologists",
    "Category:Anthropologists",
    "Category:Politicians",
    "Category:Presidents",
    "Category:Prime ministers",
    "Category:Monarchs",
    "Category:Military leaders",
    "Category:Revolutionaries",
    "Category:Activists",
    "Category:Writers",
    "Category:Poets",
    "Category:Novelists",
    "Category:Playwrights",
    "Category:Journalists",
    "Category:Artists",
    "Category:Painters",
    "Category:Sculptors",
    "Category:Architects",
    "Category:Composers",
    "Category:Musicians",
    "Category:Singers",
    "Category:Actors",
    "Category:Film directors",
    "Category:Entrepreneurs",
    "Category:Explorers",
    "Category:Religious leaders",
    "Category:Theologians",
    "Category:Saints",
    "Category:Lawyers",
    "Category:Judges",
    "Category:Athletes",
    "Category:Nobel laureates",
    "Category:Computer scientists",
]


def category_members(category: str, *, limit: int = 500) -> list[dict[str, Any]]:
    """Return category member pages and subcategories."""
    members: list[dict[str, Any]] = []
    cmcontinue = None

    while len(members) < limit:
        params = {
            "action": "query",
            "list": "categorymembers",
            "cmtitle": category,
            "cmtype": "page|subcat",
            "cmlimit": 50,
        }

        if cmcontinue:
            params["cmcontinue"] = cmcontinue

        data = wiki_api_get(params)
        batch = ((data.get("query", {}) or {}).get("categorymembers", []) or [])
        members.extend(batch)

        cmcontinue = ((data.get("continue", {}) or {}).get("cmcontinue"))
        if not cmcontinue:
            break

    return members[:limit]


def collect_page_titles() -> list[str]:
    """Collect likely biography page titles from people categories."""
    cached = load_json(QID_CACHE_PATH, {"titles": [], "qids": [], "completed_categories": []})

    titles = list(cached.get("titles", []))
    completed = set(cached.get("completed_categories", []))
    seen_titles = set(titles)
    queued_categories = list(PEOPLE_CATEGORIES)

    for category in queued_categories:
        if category in completed:
            continue

        print(f"Crawling category: {category}")
        members = category_members(category, limit=300)

        subcats = []
        for item in members:
            title = item.get("title", "")
            ns = item.get("ns")

            if ns == 0 and title and title not in seen_titles:
                seen_titles.add(title)
                titles.append(title)

            elif ns == 14 and title.startswith("Category:"):
                subcats.append(title)

        # One shallow pass through subcategories for extra people pages.
        for subcat in subcats[:8]:
            print(f"  Crawling subcategory: {subcat}")
            for item in category_members(subcat, limit=120):
                title = item.get("title", "")
                ns = item.get("ns")
                if ns == 0 and title and title not in seen_titles:
                    seen_titles.add(title)
                    titles.append(title)

                if len(titles) >= TARGET_TOTAL * 3:
                    break

            if len(titles) >= TARGET_TOTAL * 3:
                break

        completed.add(category)

        save_json(
            QID_CACHE_PATH,
            {
                "titles": titles,
                "qids": cached.get("qids", []),
                "completed_categories": sorted(completed),
            },
        )

        print(f"Candidate page titles so far: {len(titles)}")

        if len(titles) >= TARGET_TOTAL * 3:
            break

    return titles


def fetch_page_qids(titles: list[str]) -> list[str]:
    """Map Wikipedia page titles to Wikidata QIDs."""
    cached = load_json(QID_CACHE_PATH, {"titles": titles, "qids": [], "completed_categories": []})
    existing_qids = list(cached.get("qids", []))
    seen_qids = set(existing_qids)

    title_to_qid = dict(cached.get("title_to_qid", {}))
    missing_titles = [title for title in titles if title not in title_to_qid]

    for i in range(0, len(missing_titles), 50):
        chunk = missing_titles[i:i + 50]
        print(f"Mapping pages to QIDs {i + 1}-{i + len(chunk)} / {len(missing_titles)}")

        data = wiki_api_get(
            {
                "action": "query",
                "prop": "pageprops",
                "titles": "|".join(chunk),
                "ppprop": "wikibase_item",
                "redirects": 1,
            }
        )

        pages = ((data.get("query", {}) or {}).get("pages", []) or [])
        for page in pages:
            title = page.get("title", "")
            qid = ((page.get("pageprops", {}) or {}).get("wikibase_item", ""))
            if title and qid:
                title_to_qid[title] = qid
                if qid not in seen_qids:
                    seen_qids.add(qid)
                    existing_qids.append(qid)

        save_json(
            QID_CACHE_PATH,
            {
                "titles": titles,
                "qids": existing_qids,
                "title_to_qid": title_to_qid,
                "completed_categories": cached.get("completed_categories", []),
            },
        )

        if len(existing_qids) >= TARGET_TOTAL * 2:
            break

    return existing_qids


def search_qids() -> list[str]:
    """Collect Wikidata QIDs from Wikipedia biography categories."""
    cached = load_json(QID_CACHE_PATH, {})
    if len(cached.get("qids", [])) >= TARGET_TOTAL * 2:
        return cached["qids"]

    titles = collect_page_titles()
    qids = fetch_page_qids(titles)
    print(f"Candidate QIDs total: {len(qids)}")
    return qids

def fetch_entities(qids: list[str]) -> dict[str, Any]:
    """Fetch entity payloads with resume."""
    cached = load_json(ENTITY_CACHE_PATH, {})
    entities: dict[str, Any] = dict(cached)

    missing = [qid for qid in qids if qid not in entities]

    for i in range(0, len(missing), ENTITY_CHUNK_SIZE):
        chunk = missing[i : i + ENTITY_CHUNK_SIZE]
        print(f"Fetching entities {i + 1}-{i + len(chunk)} / {len(missing)}")

        data = api_get(
            {
                "action": "wbgetentities",
                "ids": "|".join(chunk),
                "props": "labels|descriptions|claims|sitelinks",
                "languages": "en",
                "sitefilter": "enwiki",
            }
        )

        entities.update(data.get("entities", {}) or {})
        save_json(ENTITY_CACHE_PATH, entities)

    return entities


def claim_values(entity: dict[str, Any], prop: str) -> list[Any]:
    """Return all raw claim values for a property."""
    values = []

    for claim in entity.get("claims", {}).get(prop, []) or []:
        try:
            value = claim["mainsnak"]["datavalue"]["value"]
            values.append(value)
        except Exception:
            pass

    return values


def claim_value(entity: dict[str, Any], prop: str) -> str:
    """Return first claim value as string."""
    values = claim_values(entity, prop)
    if not values:
        return ""

    value = values[0]

    if isinstance(value, dict):
        if "time" in value:
            return value["time"].lstrip("+")[:10]
        if "id" in value:
            return value["id"]

    return str(value)


def collect_label_qids(entities: dict[str, Any]) -> set[str]:
    """Collect QIDs that need label expansion."""
    qids = set()

    for entity in entities.values():
        for prop in ["P19", "P27", "P21", "P106"]:
            for value in claim_values(entity, prop):
                if isinstance(value, dict) and str(value.get("id", "")).startswith("Q"):
                    qids.add(value["id"])

    return qids


def fetch_labels(qids: set[str]) -> dict[str, str]:
    """Fetch labels for QIDs."""
    if not qids:
        return {}

    label_entities = fetch_entities(sorted(qids))
    labels = {}

    for qid, entity in label_entities.items():
        labels[qid] = entity.get("labels", {}).get("en", {}).get("value", "")

    return labels


def is_human(entity: dict[str, Any]) -> bool:
    """Check whether entity is a human."""
    for value in claim_values(entity, "P31"):
        if isinstance(value, dict) and value.get("id") == "Q5":
            return True
    return False


def label(entity: dict[str, Any]) -> str:
    """Return English label."""
    return entity.get("labels", {}).get("en", {}).get("value", "")


def description(entity: dict[str, Any]) -> str:
    """Return English description."""
    return entity.get("descriptions", {}).get("en", {}).get("value", "")


def wikipedia_url(entity: dict[str, Any]) -> str:
    """Return English Wikipedia URL."""
    title = entity.get("sitelinks", {}).get("enwiki", {}).get("title", "")
    if not title:
        return ""
    return "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title.replace(" ", "_"))


def slug(name: str, qid: str) -> str:
    """Build profile key."""
    base = "".join(ch.lower() if ch.isalnum() else "_" for ch in name)
    base = "_".join(part for part in base.split("_") if part)
    return f"{base}_{qid.lower()}"


def category_from_text(occupation: str, desc: str) -> str:
    """Infer category."""
    text = f"{occupation} {desc}".lower()

    if "philosopher" in text:
        return "philosophy"
    if any(word in text for word in ["scientist", "physicist", "chemist", "biologist", "mathematician", "astronomer"]):
        return "science"
    if any(word in text for word in ["politician", "president", "prime minister", "king", "queen", "emperor", "monarch"]):
        return "politics"
    if any(word in text for word in ["military", "general", "commander"]):
        return "military"
    if any(word in text for word in ["writer", "poet", "novelist", "playwright", "journalist"]):
        return "literature"
    if any(word in text for word in ["artist", "painter", "sculptor", "architect"]):
        return "visual_art"
    if any(word in text for word in ["musician", "composer", "singer"]):
        return "music"
    if any(word in text for word in ["actor", "director", "filmmaker"]):
        return "film_theater"
    if any(word in text for word in ["entrepreneur", "businessperson", "industrialist"]):
        return "business"
    if any(word in text for word in ["athlete", "footballer", "player", "olympic"]):
        return "sports"
    if any(word in text for word in ["religious", "theologian", "pope", "saint"]):
        return "religion"

    return "prominent_figure"


def build_records() -> list[dict[str, Any]]:
    """Build final records."""
    qids = search_qids()
    entities = fetch_entities(qids)
    labels = fetch_labels(collect_label_qids(entities))

    records = []
    seen_names = set()

    for qid, entity in entities.items():
        if not isinstance(entity, dict):
            continue

        if not is_human(entity):
            continue

        name = label(entity)
        if not name:
            continue

        wiki = wikipedia_url(entity)
        if not wiki:
            continue

        name_key = name.lower().strip()
        if name_key in seen_names:
            continue

        occupation_qids = [
            value.get("id")
            for value in claim_values(entity, "P106")
            if isinstance(value, dict) and value.get("id")
        ]

        occupations = [labels.get(qid_value, "") for qid_value in occupation_qids]
        occupations = [item for item in occupations if item]

        occupation = occupations[0] if occupations else ""
        all_occupations = "; ".join(occupations)

        desc = description(entity)

        record = {
            "profile_key": slug(name, qid),
            "name": name,
            "wikidata_id": qid,
            "source_url": f"https://www.wikidata.org/wiki/{qid}",
            "wikipedia_url": wiki,
            "category": category_from_text(all_occupations, desc),
            "birth_date": claim_value(entity, "P569"),
            "death_date": claim_value(entity, "P570"),
            "birth_place": labels.get(claim_value(entity, "P19"), ""),
            "country": labels.get(claim_value(entity, "P27"), ""),
            "gender": labels.get(claim_value(entity, "P21"), ""),
            "occupation": occupation,
            "occupations": all_occupations,
            "description": desc,
            "sitelinks": len(entity.get("sitelinks", {}) or {}),
            "data_quality": "wikidata_api_structured",
            "notes": "Imported from Wikidata API; missing fields intentionally left blank.",
        }

        records.append(record)
        seen_names.add(name_key)

    records.sort(key=lambda item: (-int(item.get("sitelinks") or 0), item["name"]))
    return records[:TARGET_TOTAL]


def write_outputs(records: list[dict[str, Any]]) -> None:
    """Write CSV/JSON/names and intake files."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    fields = [
        "profile_key",
        "name",
        "wikidata_id",
        "source_url",
        "wikipedia_url",
        "category",
        "birth_date",
        "death_date",
        "birth_place",
        "country",
        "gender",
        "occupation",
        "occupations",
        "description",
        "sitelinks",
        "data_quality",
        "notes",
    ]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(records)

    JSON_PATH.write_text(json.dumps(records, indent=2, ensure_ascii=False), encoding="utf-8")
    NAMES_PATH.write_text("\n".join(record["profile_key"] for record in records) + "\n", encoding="utf-8")

    for record in records:
        write_intake(record)


def write_intake(record: dict[str, Any]) -> None:
    """Write Atlas profile intake JSON."""
    profile_key = record["profile_key"]
    target = LIBRARY_DIR / profile_key
    target.mkdir(parents=True, exist_ok=True)

    intake = {
        "profile_key": profile_key,
        "name": record["name"],
        "birth_date": record.get("birth_date", ""),
        "birth_time": "",
        "birth_place": record.get("birth_place", ""),
        "country": record.get("country", ""),
        "gender": record.get("gender", ""),
        "category": record.get("category", ""),
        "occupation": record.get("occupation", ""),
        "occupations": record.get("occupations", ""),
        "source": "wikidata",
        "source_url": record.get("source_url", ""),
        "wikipedia_url": record.get("wikipedia_url", ""),
        "wikidata_id": record.get("wikidata_id", ""),
        "data_quality": record.get("data_quality", ""),
        "notes": record.get("notes", ""),
        "metadata": {
            "description": record.get("description", ""),
            "sitelinks": record.get("sitelinks", 0),
            "death_date": record.get("death_date", ""),
        },
    }

    (target / "profile.intake.json").write_text(
        json.dumps(intake, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def main() -> None:
    records = build_records()
    write_outputs(records)

    print(f"Created {len(records)} prominent figure records.")
    print(f"CSV: {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")
    print(f"Names: {NAMES_PATH}")
    print(f"Intake root: {LIBRARY_DIR}")


if __name__ == "__main__":
    main()
