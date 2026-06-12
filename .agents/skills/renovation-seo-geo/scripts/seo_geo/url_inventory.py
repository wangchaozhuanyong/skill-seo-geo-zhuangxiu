"""URL inventory helpers for SEO/GEO technical audits."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional
from urllib.parse import urljoin, urlsplit

try:
    from .hreflang import detect_language_from_url
except ImportError:  # pragma: no cover - used when running as a script file
    from hreflang import detect_language_from_url


INVENTORY_FIELDS = [
    "url",
    "language",
    "page_type",
    "status_code",
    "indexable",
    "robots_allowed",
    "meta_robots",
    "canonical_url",
    "canonical_self",
    "hreflang_pair",
    "title",
    "meta_description",
    "h1",
    "word_count",
    "internal_inlinks_count",
    "internal_outlinks_count",
    "schema_types",
    "image_count",
    "missing_alt_count",
    "lastmod",
    "sitemap_included",
    "priority_issue",
]


@dataclass
class UrlCandidate:
    url: str
    source: str = ""
    lastmod: str = ""
    page_type: str = ""


def normalize_url(value: str, base_url: str = "") -> str:
    value = (value or "").strip()
    if not value:
        return ""
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("/") and base_url:
        return urljoin(base_url.rstrip("/") + "/", value.lstrip("/"))
    return value


def infer_page_type(url: str) -> str:
    path = urlsplit(url).path.lower().strip("/")
    parts = [part for part in path.split("/") if part]
    if not parts:
        return "home"
    if parts[-1] in {"services", "projects", "blog"}:
        return f"{parts[-1]}-hub"
    if "services" in parts:
        return "service"
    if "locations" in parts:
        return "local"
    if "projects" in parts:
        return "case-study"
    if "blog" in parts or "articles" in parts:
        return "article"
    if parts[-1] in {"quote", "contact", "consultation"}:
        return "conversion"
    return "page"


def blank_inventory_row(url: str, *, page_type: str = "", lastmod: str = "") -> dict[str, str]:
    inferred_page_type = page_type or infer_page_type(url)
    return {
        "url": url,
        "language": detect_language_from_url(url),
        "page_type": inferred_page_type,
        "status_code": "",
        "indexable": "unknown",
        "robots_allowed": "unknown",
        "meta_robots": "",
        "canonical_url": "",
        "canonical_self": "unknown",
        "hreflang_pair": "unknown",
        "title": "",
        "meta_description": "",
        "h1": "",
        "word_count": "",
        "internal_inlinks_count": "0",
        "internal_outlinks_count": "0",
        "schema_types": "",
        "image_count": "0",
        "missing_alt_count": "0",
        "lastmod": lastmod,
        "sitemap_included": "no",
        "priority_issue": "",
    }


def priority_issue(row: dict[str, str]) -> str:
    if row.get("robots_allowed") == "no":
        return "blocked_by_robots"
    if "noindex" in row.get("meta_robots", "").lower():
        return "meta_noindex"
    if row.get("canonical_self") == "no":
        return "canonical_not_self"
    if row.get("indexable") == "no":
        return "not_indexable"
    if row.get("hreflang_pair") == "no" and row.get("language") in {"en", "zh"}:
        return "missing_hreflang_pair"
    if not row.get("title"):
        return "missing_title"
    if not row.get("meta_description"):
        return "missing_meta_description"
    try:
        if int(row.get("missing_alt_count") or "0") > 0:
            return "missing_image_alt"
    except ValueError:
        pass
    return ""


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]


def collect_from_keyword_map(path: Path, base_url: str = "") -> list[UrlCandidate]:
    candidates: list[UrlCandidate] = []
    for row in read_csv_rows(path):
        page_type = row.get("page_type", "")
        for field in ("target_url", "current_url"):
            url = normalize_url(row.get(field, ""), base_url)
            if url:
                candidates.append(UrlCandidate(url=url, source=f"keyword-map:{field}", page_type=page_type))
    return candidates


def collect_from_internal_links(path: Path, base_url: str = "") -> list[UrlCandidate]:
    candidates: list[UrlCandidate] = []
    for row in read_csv_rows(path):
        for field in ("source_url", "target_url"):
            url = normalize_url(row.get(field, ""), base_url)
            if url:
                candidates.append(UrlCandidate(url=url, source=f"internal-links:{field}"))
    return candidates


def _manifest_urls(value: object, base_url: str = "") -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if key_lower in {"url", "path", "route", "href", "loc", "canonical"} and isinstance(item, str):
                normalized = normalize_url(item, base_url)
                if normalized:
                    yield normalized
            yield from _manifest_urls(item, base_url)
    elif isinstance(value, list):
        for item in value:
            yield from _manifest_urls(item, base_url)
    elif isinstance(value, str) and value.startswith(("http://", "https://", "/en", "/zh")):
        normalized = normalize_url(value, base_url)
        if normalized:
            yield normalized


def collect_from_seo_manifest(path: Path, base_url: str = "") -> list[UrlCandidate]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    return [UrlCandidate(url=url, source="seo-manifest") for url in _manifest_urls(data, base_url)]


def dedupe_candidates(candidates: Iterable[UrlCandidate]) -> list[UrlCandidate]:
    seen: dict[str, UrlCandidate] = {}
    for candidate in candidates:
        if not candidate.url:
            continue
        if candidate.url not in seen:
            seen[candidate.url] = candidate
            continue
        existing = seen[candidate.url]
        if not existing.lastmod and candidate.lastmod:
            existing.lastmod = candidate.lastmod
        if not existing.page_type and candidate.page_type:
            existing.page_type = candidate.page_type
    return sorted(seen.values(), key=lambda item: item.url)


def write_inventory_csv(rows: list[dict[str, str]], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=INVENTORY_FIELDS)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in INVENTORY_FIELDS})


def read_inventory_csv(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)
