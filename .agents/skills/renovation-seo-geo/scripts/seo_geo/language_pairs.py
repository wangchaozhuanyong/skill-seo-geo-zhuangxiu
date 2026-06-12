#!/usr/bin/env python3
"""Build bilingual URL-pair inventory for /zh and /en pages."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit

try:
    from .hreflang import detect_language_from_url, expected_pair_url
except ImportError:  # pragma: no cover
    from hreflang import detect_language_from_url, expected_pair_url


PAIR_FIELDS = [
    "source_url",
    "source_language",
    "paired_url",
    "paired_language",
    "pair_exists",
    "page_type",
    "source_slug",
    "paired_slug",
    "service_slug_pair_consistent",
    "source_in_sitemap",
    "paired_in_sitemap",
    "source_canonical_self",
    "paired_canonical_self",
    "source_hreflang_pair",
    "paired_hreflang_pair",
]


@dataclass
class LanguagePair:
    source_url: str
    source_language: str
    paired_url: str
    paired_language: str
    pair_exists: str
    page_type: str = ""
    source_slug: str = ""
    paired_slug: str = ""
    service_slug_pair_consistent: str = ""
    source_in_sitemap: str = ""
    paired_in_sitemap: str = ""
    source_canonical_self: str = ""
    paired_canonical_self: str = ""
    source_hreflang_pair: str = ""
    paired_hreflang_pair: str = ""

    def as_row(self) -> dict[str, str]:
        return {field: getattr(self, field) for field in PAIR_FIELDS}


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [{key: (value or "").strip() for key, value in row.items()} for row in csv.DictReader(handle)]


def slug_after_language(url: str) -> str:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if parts and parts[0] in {"en", "zh"}:
        return "/".join(parts[1:])
    return "/".join(parts)


def service_slug(url: str) -> str:
    parts = [part for part in urlsplit(url).path.split("/") if part]
    if len(parts) >= 3 and parts[1] == "services":
        return parts[2]
    return ""


def row_by_url(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    return {row.get("url", ""): row for row in rows if row.get("url")}


def sitemap_value(row: dict[str, str]) -> str:
    return row.get("in_sitemap") or row.get("sitemap_included", "")


def build_language_pairs(root: Path) -> list[LanguagePair]:
    rows = read_csv_rows(root / "seo-workspace" / "data" / "url-inventory.csv")
    lookup = row_by_url(rows)
    pairs: list[LanguagePair] = []
    for row in rows:
        url = row.get("url", "")
        source_lang = detect_language_from_url(url) or row.get("language", "")
        if source_lang not in {"en", "zh"}:
            continue
        pair_url = expected_pair_url(url)
        pair_row = lookup.get(pair_url, {})
        pair_lang = "zh" if source_lang == "en" else "en"
        source_service_slug = service_slug(url)
        paired_service_slug = service_slug(pair_url)
        slug_consistent = ""
        if source_service_slug or paired_service_slug:
            slug_consistent = "yes" if source_service_slug == paired_service_slug else "no"
        pairs.append(
            LanguagePair(
                source_url=url,
                source_language=source_lang,
                paired_url=pair_url,
                paired_language=pair_lang,
                pair_exists="yes" if pair_url in lookup else "no",
                page_type=row.get("page_type", ""),
                source_slug=slug_after_language(url),
                paired_slug=slug_after_language(pair_url),
                service_slug_pair_consistent=slug_consistent,
                source_in_sitemap=sitemap_value(row),
                paired_in_sitemap=sitemap_value(pair_row),
                source_canonical_self=row.get("canonical_self", ""),
                paired_canonical_self=pair_row.get("canonical_self", ""),
                source_hreflang_pair=row.get("hreflang_pair", ""),
                paired_hreflang_pair=pair_row.get("hreflang_pair", ""),
            )
        )
    return pairs


def write_language_pairs(root: Path) -> Path:
    root = root.resolve()
    output = root / "seo-workspace" / "data" / "language-pairs.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=PAIR_FIELDS)
        writer.writeheader()
        writer.writerows(pair.as_row() for pair in build_language_pairs(root))
    return output


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build bilingual URL-pair inventory.")
    parser.add_argument("--root", default=".", help="Repository root. Defaults to current directory.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    print(write_language_pairs(Path(args.root)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
