"""Hreflang extraction and bilingual URL-pair checks."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit


class _HreflangParser(HTMLParser):
    def __init__(self, page_url: str = "") -> None:
        super().__init__()
        self.page_url = page_url
        self.links: dict[str, str] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "link":
            return
        data = {key.lower(): value or "" for key, value in attrs}
        rel_values = {part.strip().lower() for part in data.get("rel", "").split()}
        hreflang = data.get("hreflang", "").strip().lower()
        href = data.get("href", "").strip()
        if "alternate" in rel_values and hreflang and href:
            self.links[hreflang] = urljoin(self.page_url, href) if self.page_url else href


def extract_hreflang_links(html: str, page_url: str = "") -> dict[str, str]:
    parser = _HreflangParser(page_url=page_url)
    parser.feed(html or "")
    return parser.links


def detect_language_from_url(url: str) -> str:
    path_parts = [part for part in urlsplit(url).path.split("/") if part]
    if path_parts and path_parts[0].lower() in {"en", "zh"}:
        return path_parts[0].lower()
    return ""


def expected_pair_url(url: str) -> str:
    parts = urlsplit(url)
    path_parts = [part for part in parts.path.split("/") if part]
    if not path_parts or path_parts[0].lower() not in {"en", "zh"}:
        return ""
    path_parts[0] = "zh" if path_parts[0].lower() == "en" else "en"
    new_path = "/" + "/".join(path_parts)
    if parts.path.endswith("/") and not new_path.endswith("/"):
        new_path += "/"
    return urlunsplit((parts.scheme, parts.netloc, new_path, "", ""))


def _normalize(url: str) -> str:
    parts = urlsplit(url.strip())
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), path, "", ""))


def has_hreflang_pair(url: str, links: dict[str, str]) -> bool:
    pair = expected_pair_url(url)
    if not pair:
        return False
    normalized_pair = _normalize(pair)
    return any(_normalize(value) == normalized_pair for value in links.values())
