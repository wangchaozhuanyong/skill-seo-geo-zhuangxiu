"""Robots.txt and sitemap helpers for SEO/GEO audits."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin
from urllib.robotparser import RobotFileParser


@dataclass
class SitemapEntry:
    loc: str
    lastmod: str = ""


@dataclass
class RobotsInfo:
    sitemaps: list[str] = field(default_factory=list)
    allows: list[str] = field(default_factory=list)
    disallows: list[str] = field(default_factory=list)


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if "}" in tag else tag


def parse_robots_txt(text: str) -> RobotsInfo:
    info = RobotsInfo()
    active_applies_to_all = False

    for raw_line in text.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = [part.strip() for part in line.split(":", 1)]
        key_lower = key.lower()
        if key_lower == "sitemap" and value:
            info.sitemaps.append(value)
        elif key_lower == "user-agent":
            active_applies_to_all = value == "*"
        elif key_lower == "allow" and active_applies_to_all:
            info.allows.append(value)
        elif key_lower == "disallow" and active_applies_to_all:
            info.disallows.append(value)
    return info


def robots_allowed(url: str, robots_text: str = "", user_agent: str = "*") -> bool:
    if not robots_text.strip():
        return True
    parser = RobotFileParser()
    parser.parse(robots_text.splitlines())
    return parser.can_fetch(user_agent, url)


def robots_url_for(base_url: str) -> str:
    return urljoin(base_url.rstrip("/") + "/", "robots.txt")


def parse_sitemap_xml(text: str) -> list[SitemapEntry]:
    if not text.strip():
        return []

    root = ET.fromstring(text)
    entries: list[SitemapEntry] = []
    for child in list(root):
        loc = ""
        lastmod = ""
        for element in list(child):
            name = _local_name(element.tag)
            if name == "loc":
                loc = (element.text or "").strip()
            elif name == "lastmod":
                lastmod = (element.text or "").strip()
        if loc:
            entries.append(SitemapEntry(loc=loc, lastmod=lastmod))
    return entries


def read_sitemap_file(path: Path) -> list[SitemapEntry]:
    if not path.exists():
        return []
    return parse_sitemap_xml(path.read_text(encoding="utf-8", errors="replace"))


def find_local_sitemaps(root: Path) -> list[Path]:
    candidates = [
        root / "public" / "sitemap.xml",
        root / "dist" / "sitemap.xml",
        root / "sitemap.xml",
    ]
    return [path for path in candidates if path.exists()]
