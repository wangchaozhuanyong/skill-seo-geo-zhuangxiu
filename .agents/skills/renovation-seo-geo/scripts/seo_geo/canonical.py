"""Canonical URL extraction and comparison helpers."""

from __future__ import annotations

from html.parser import HTMLParser
from typing import Optional
from urllib.parse import urljoin, urlsplit, urlunsplit


class _CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical_url = ""

    def handle_starttag(self, tag: str, attrs: list[tuple[str, Optional[str]]]) -> None:
        if tag.lower() != "link" or self.canonical_url:
            return
        data = {key.lower(): value or "" for key, value in attrs}
        rel_values = {part.strip().lower() for part in data.get("rel", "").split()}
        if "canonical" in rel_values and data.get("href"):
            self.canonical_url = data["href"].strip()


def extract_canonical_url(html: str, page_url: str = "") -> str:
    parser = _CanonicalParser()
    parser.feed(html or "")
    if parser.canonical_url and page_url:
        return urljoin(page_url, parser.canonical_url)
    return parser.canonical_url


def normalize_url_for_compare(url: str) -> str:
    if not url:
        return ""
    parts = urlsplit(url.strip())
    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    path = parts.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return urlunsplit((scheme, netloc, path, "", ""))


def is_self_canonical(page_url: str, canonical_url: str) -> bool:
    if not canonical_url:
        return False
    return normalize_url_for_compare(page_url) == normalize_url_for_compare(canonical_url)
